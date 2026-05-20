import struct
from dataclasses import dataclass

from pymodbus.client import ModbusTcpClient

from logger import logger


@dataclass
class InverterMeasurement:
    voltage_dc: float | None
    current_dc: float | None
    power_ac: float | None
    temp: float | None
    freq: float | None
    pf: float | None
    energy_total: float | None
    energy_day: float | None
    runtime: float | None
    status: int | None
    error: int | None


class ModbusClient:
    """Wrapper around ModbusTcpClient for inverter telemetry."""

    FLOAT_ADDRESSES = (0, 2, 4, 6, 8, 10, 12, 14, 16)
    STATUS_OFFSET = 18
    ERROR_OFFSET = 19

    def __init__(self, host: str, port: int, device_id: int = 1) -> None:
        self.client = ModbusTcpClient(host, port=port)
        self.device_id = device_id

    @property
    def is_connected(self) -> bool:
        return bool(self.client.connected)

    def connect(self, retries: int = 3) -> bool:
        for attempt in range(retries):
            if self.client.connect():
                return True
            logger.warning(f'Failed to connect to Modbus server (attempt {attempt + 1}/{retries})')

        raise ConnectionError(f'Unable to connect to Modbus server after {retries} attempts')

    def close(self) -> None:
        self.client.close()

    def ensure_connected(self, retries: int = 3) -> None:
        if not self.is_connected:
            self.connect(retries=retries)

    @staticmethod
    def _decode_float32(high_register: int, low_register: int) -> float:
        raw = (high_register << 16) | low_register
        return struct.unpack('>f', raw.to_bytes(4, byteorder='big'))[0]

    def read_registers_block(self, start_address: int, count: int) -> list[int] | None:
        try:
            result = self.client.read_input_registers(
                address=start_address,
                count=count,
                device_id=self.device_id,
            )
        except Exception as error:
            logger.warning(f'Ignoring error reading register block at {start_address}: {error}', exc_info=True)
            return None

        if result.isError():
            logger.warning(f'Ignoring Modbus error reading register block at {start_address}: {result}')
            return None

        return list(result.registers)

    def read_float32(self, address: int, registers: list[int] | None, offset: int) -> float | None:
        if registers is None:
            return None

        try:
            return self._decode_float32(registers[offset], registers[offset + 1])
        except (IndexError, struct.error) as error:
            logger.warning(f'Ignoring error decoding float32 at address {address}: {error}')
            return None

    def read_int16(self, registers: list[int] | None, offset: int, address: int) -> int | None:
        if registers is None:
            return None

        try:
            return registers[offset]
        except IndexError as error:
            logger.warning(f'Ignoring error decoding int16 at address {address}: {error}')
            return None

    def read_measurement_block(self, start_address: int, count: int) -> InverterMeasurement:
        registers = self.read_registers_block(start_address, count)

        if registers is None:
            return InverterMeasurement(None, None, None, None, None, None, None, None, None, None, None)

        base_offset = start_address - 32000

        return InverterMeasurement(
            voltage_dc=self.read_float32(32000, registers, base_offset + self.FLOAT_ADDRESSES[0]),
            current_dc=self.read_float32(32002, registers, base_offset + self.FLOAT_ADDRESSES[1]),
            power_ac=self.read_float32(32004, registers, base_offset + self.FLOAT_ADDRESSES[2]),
            temp=self.read_float32(32006, registers, base_offset + self.FLOAT_ADDRESSES[3]),
            freq=self.read_float32(32008, registers, base_offset + self.FLOAT_ADDRESSES[4]),
            pf=self.read_float32(32010, registers, base_offset + self.FLOAT_ADDRESSES[5]),
            energy_total=self.read_float32(32012, registers, base_offset + self.FLOAT_ADDRESSES[6]),
            energy_day=self.read_float32(32014, registers, base_offset + self.FLOAT_ADDRESSES[7]),
            runtime=self.read_float32(32016, registers, base_offset + self.FLOAT_ADDRESSES[8]),
            status=self.read_int16(registers, base_offset + self.STATUS_OFFSET, 32018),
            error=self.read_int16(registers, base_offset + self.ERROR_OFFSET, 32019),
        )
