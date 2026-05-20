import struct

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
