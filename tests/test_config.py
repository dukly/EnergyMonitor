from config import Settings


def test_blank_modbus_device_id_uses_profile_default(monkeypatch) -> None:
    monkeypatch.setenv('MODBUS_DEVICE_ID', '')

    settings = Settings()

    assert settings.modbus_device_id is None


def test_modbus_device_id_parses_integer(monkeypatch) -> None:
    monkeypatch.setenv('MODBUS_DEVICE_ID', '7')

    settings = Settings()

    assert settings.modbus_device_id == 7
