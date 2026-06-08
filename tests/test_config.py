from config import Settings


def test_settings_treats_blank_modbus_device_id_as_profile_default() -> None:
    settings = Settings(modbus_device_id='')

    assert settings.modbus_device_id is None

