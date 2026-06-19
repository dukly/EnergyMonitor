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
    client.read_registers_block = lambda start, count, kind='input': registers

    measurement = client.read_measurement_block(32000, 20, register_kind='input')

    assert measurement.voltage_dc == 400.0
    assert measurement.status == 1
    assert measurement.error == 0


def test_read_measurement_block_rejects_short_response() -> None:
    client = ModbusClient('localhost', 502)
    client.read_registers_block = lambda start, count, kind='input': [0, 1, 2]

    measurement = client.read_measurement_block(32000, 20, register_kind='input')

    assert measurement.voltage_dc is None
    assert measurement.status is None


def test_read_registers_block_auto_fallback() -> None:
    client = ModbusClient('localhost', 502)

    def fake_merged(start: int, count: int, kind: str) -> list[int] | None:
        if kind == 'holding':
            return None
        return [0] * count

    client._read_registers_merged = fake_merged  # type: ignore[method-assign]

    registers = client.read_registers_block(32000, 20, register_kind='auto')

    assert registers is not None
    assert len(registers) == 20
    assert client._preferred_register_kind == 'input'


def test_read_registers_block_reads_in_chunks() -> None:
    client = ModbusClient('localhost', 502)
    chunk_calls: list[tuple[int, int, str]] = []

    def fake_chunk(start: int, count: int, kind: str) -> list[int] | None:
        chunk_calls.append((start, count, kind))
        if count == 20:
            return None
        return [start + index for index in range(count)]

    client._read_registers_chunk = fake_chunk  # type: ignore[method-assign]

    registers = client.read_registers_block(32000, 20, register_kind='input')

    assert registers is not None
    assert len(registers) == 20
    assert chunk_calls[0] == (32000, 20, 'input')
    assert chunk_calls[1] == (32000, 10, 'input')
    assert chunk_calls[2] == (32010, 10, 'input')


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


def test_handler_closes_client_on_status_only_measurement(tmp_path) -> None:
    from handler import handle_measurement
    from libraries.database import Database
    from libraries.modbus import InverterMeasurement

    db = Database(str(tmp_path / 'test.db'))
    client = MagicMock(spec=ModbusClient)
    client.read_measurement_block.return_value = InverterMeasurement(
        None, None, None, None, None, None, None, None, None, 1, 0,
    )

    result = handle_measurement(db, client)

    assert result is None
    client.close.assert_called_once()
    db.cur.execute('SELECT COUNT(*) FROM measurements')
    assert db.cur.fetchone()[0] == 0
    db.close()
