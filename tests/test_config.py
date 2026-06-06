from config import Settings


def test_empty_modbus_device_id_uses_profile_default(tmp_path) -> None:
    env_file = tmp_path / '.env'
    env_file.write_text('MODBUS_DEVICE_ID=\n', encoding='utf-8')

    settings = Settings(_env_file=env_file)

    assert settings.modbus_device_id is None
