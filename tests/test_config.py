from config import Settings


def test_blank_modbus_device_id_uses_profile_default() -> None:
    settings = Settings(modbus_device_id='')

    assert settings.modbus_device_id is None


def test_whitespace_modbus_device_id_uses_profile_default() -> None:
    settings = Settings(modbus_device_id='  ')

    assert settings.modbus_device_id is None
