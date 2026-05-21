import struct
from unittest.mock import MagicMock

from libraries.modbus import ModbusClient


def test_decode_float32() -> None:
    raw = struct.pack('>f', 230.5)
    high, low = int.from_bytes(raw[:2], 'big'), int.from_bytes(raw[2:], 'big')
    value = ModbusClient._decode_float32(high, low)
    assert abs(value - 230.5) < 0.001


def test_read_measurement_block_parses_registers() -> None:
    registers = [0] * 20
    payload = struct.pack('>f', 400.0)
    registers[0] = int.from_bytes(payload[:2], 'big')
    registers[1] = int.from_bytes(payload[2:], 'big')
    registers[18] = 1
    registers[19] = 0

    client = ModbusClient('localhost', 502)
    client.read_registers_block = lambda start, count: registers

    measurement = client.read_measurement_block(32000, 20)

    assert measurement.voltage_dc == 400.0
    assert measurement.status == 1
    assert measurement.error == 0


def test_read_measurement_block_rejects_short_response() -> None:
    client = ModbusClient('localhost', 502)
    client.read_registers_block = lambda start, count: [0, 1, 2]

    measurement = client.read_measurement_block(32000, 20)

    assert measurement.voltage_dc is None
    assert measurement.status is None


def test_handler_closes_client_on_empty_measurement(tmp_path) -> None:
    from handler import handle_measurement
    from libraries.database import Database
    from libraries.modbus import InverterMeasurement

    db = Database(str(tmp_path / 'test.db'))
    client = MagicMock(spec=ModbusClient)
    client.read_measurement_block.return_value = InverterMeasurement(
        None, None, None, None, None, None, None, None, None, None, None,
    )

    result = handle_measurement(db, client)

    assert result is None
    client.close.assert_called_once()
    db.close()
