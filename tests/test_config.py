from config import Settings


def test_blank_modbus_device_id_uses_profile_default() -> None:
    assert Settings(modbus_device_id='').modbus_device_id is None
    assert Settings(modbus_device_id='   ').modbus_device_id is None

