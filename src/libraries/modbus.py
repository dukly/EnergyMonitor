import struct
from dataclasses import dataclass

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

from config import settings
from logger import logger

REGISTER_KIND_HOLDING = 'holding'
REGISTER_KIND_INPUT = 'input'
REGISTER_KINDS = (REGISTER_KIND_HOLDING, REGISTER_KIND_INPUT)


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

    FLOAT_OFFSETS = (0, 2, 4, 6, 8, 10, 12, 14, 16)
    STATUS_OFFSET = 18
    ERROR_OFFSET = 19

    def __init__(self, host: str, port: int, device_id: int = 1) -> None:
        self.host = host
        self.port = port
        self.device_id = device_id
        self._preferred_register_kind: str | None = None
        self.client = ModbusTcpClient(
            host,
            port=port,
            timeout=settings.modbus_timeout,
            retries=settings.modbus_retries,
        )

    @property
    def is_connected(self) -> bool:
        return bool(self.client.connected)

    @property
    def endpoint(self) -> str:
        return f'{self.host}:{self.port}'

    def connect(self, retries: int = 3) -> bool:
        for attempt in range(retries):
            if self.client.connect():
                logger.info(f'Modbus TCP connected to {self.endpoint}')
                return True
            logger.warning(
                f'Failed to connect to Modbus at {self.endpoint} '
                f'(attempt {attempt + 1}/{retries})',
            )

        raise ConnectionError(
            f'Unable to connect to Modbus at {self.endpoint} after {retries} attempts. '
            'Check MODBUS_HOST/MODBUS_PORT, USR-W610 TCP Server mode, and Local Port 502.',
        )

    def close(self) -> None:
        self.client.close()

    def reconnect(self, retries: int = 3) -> None:
        self.close()
        self.connect(retries=retries)

    def ensure_connected(self, retries: int = 3) -> None:
        if not self.is_connected:
            self.reconnect(retries=retries)

    @staticmethod
    def _decode_float32(high_register: int, low_register: int) -> float:
        raw = (high_register << 16) | low_register
        value = struct.unpack('>f', raw.to_bytes(4, byteorder='big'))[0]
        if value != value:  # NaN
            raise struct.error('decoded NaN')
        return value

    def _register_kinds_to_try(self, register_kind: str) -> list[str]:
        kind = register_kind.strip().lower()
        if kind == 'auto':
            kinds = list(REGISTER_KINDS)
        elif kind in REGISTER_KINDS:
            kinds = [kind]
        else:
            logger.warning(f'Unknown register kind "{register_kind}", using input registers')
            kinds = [REGISTER_KIND_INPUT]

        preferred = self._preferred_register_kind
        if preferred and preferred in kinds:
            return [preferred] + [item for item in kinds if item != preferred]
        return kinds

    def _read_registers_chunk(
        self,
        start_address: int,
        count: int,
        register_kind: str,
    ) -> list[int] | None:
        try:
            if register_kind == REGISTER_KIND_HOLDING:
                result = self.client.read_holding_registers(
                    address=start_address,
                    count=count,
                    device_id=self.device_id,
                )
            else:
                result = self.client.read_input_registers(
                    address=start_address,
                    count=count,
                    device_id=self.device_id,
                )
        except ModbusIOException as error:
            logger.warning(
                f'No Modbus response ({register_kind}) at {start_address}+{count} '
                f'on {self.endpoint}, unit={self.device_id}: {error}. '
                'If TCP is OK, check RS485 wiring, inverter power, and slave ID.',
            )
            return None
        except Exception as error:
            logger.warning(
                f'Error reading {register_kind} registers at {start_address} '
                f'from {self.endpoint}: {error}',
            )
            return None

        if result.isError():
            logger.warning(
                f'Modbus error reading {register_kind} registers at {start_address} '
                f'from {self.endpoint}: {result}',
            )
            return None

        registers = list(result.registers)
        if len(registers) < count:
            logger.warning(
                f'Incomplete Modbus block at {start_address} ({register_kind}): '
                f'expected {count}, got {len(registers)} from {self.endpoint}',
            )
            return None

        return registers

    def _read_registers_merged(
        self,
        start_address: int,
        count: int,
        register_kind: str,
    ) -> list[int] | None:
        full_block = self._read_registers_chunk(start_address, count, register_kind)
        if full_block is not None:
            return full_block

        chunk_size = self._safe_chunk_size(settings.modbus_read_chunk_size)
        if count <= chunk_size:
            return None

        merged: list[int] = []
        offset = 0
        while offset < count:
            piece_count = min(chunk_size, count - offset)
            piece = self._read_registers_chunk(
                start_address + offset,
                piece_count,
                register_kind,
            )
            if piece is None:
                return None
            merged.extend(piece)
            offset += piece_count

        return merged

    @staticmethod
    def _safe_chunk_size(configured_chunk_size: int) -> int:
        chunk_size = max(2, configured_chunk_size)
        if chunk_size % 2 == 0:
            return chunk_size

        safe_chunk_size = chunk_size - 1
        logger.warning(
            'MODBUS_READ_CHUNK_SIZE must not split float32 register pairs; '
            f'using {safe_chunk_size} instead of {configured_chunk_size}',
        )
        return safe_chunk_size

    def read_registers_block(
        self,
        start_address: int,
        count: int,
        register_kind: str = REGISTER_KIND_INPUT,
    ) -> list[int] | None:
        for kind in self._register_kinds_to_try(register_kind):
            registers = self._read_registers_merged(start_address, count, kind)
            if registers is None:
                continue

            if self._preferred_register_kind != kind:
                logger.info(
                    f'Modbus read OK via {kind} registers '
                    f'(unit={self.device_id}, start={start_address}, count={count})',
                )
            self._preferred_register_kind = kind
            return registers

        return None

    def read_float32(self, registers: list[int] | None, offset: int, address: int) -> float | None:
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

    def read_measurement_block(
        self,
        start_address: int,
        count: int,
        register_kind: str = REGISTER_KIND_INPUT,
    ) -> InverterMeasurement:
        registers = self.read_registers_block(start_address, count, register_kind)

        if registers is None:
            return InverterMeasurement(None, None, None, None, None, None, None, None, None, None, None)

        if len(registers) < count or count < self.ERROR_OFFSET + 1:
            logger.warning(
                f'Register block too short: start={start_address}, kind={register_kind}, '
                f'expected={count}, got={len(registers)}',
            )
            return InverterMeasurement(None, None, None, None, None, None, None, None, None, None, None)

        def addr(offset: int) -> int:
            return start_address + offset

        return InverterMeasurement(
            voltage_dc=self.read_float32(registers, self.FLOAT_OFFSETS[0], addr(0)),
            current_dc=self.read_float32(registers, self.FLOAT_OFFSETS[1], addr(2)),
            power_ac=self.read_float32(registers, self.FLOAT_OFFSETS[2], addr(4)),
            temp=self.read_float32(registers, self.FLOAT_OFFSETS[3], addr(6)),
            freq=self.read_float32(registers, self.FLOAT_OFFSETS[4], addr(8)),
            pf=self.read_float32(registers, self.FLOAT_OFFSETS[5], addr(10)),
            energy_total=self.read_float32(registers, self.FLOAT_OFFSETS[6], addr(12)),
            energy_day=self.read_float32(registers, self.FLOAT_OFFSETS[7], addr(14)),
            runtime=self.read_float32(registers, self.FLOAT_OFFSETS[8], addr(16)),
            status=self.read_int16(registers, self.STATUS_OFFSET, addr(18)),
            error=self.read_int16(registers, self.ERROR_OFFSET, addr(19)),
        )
