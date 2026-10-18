import pytest
from pydantic import ValidationError

from config import Settings


@pytest.mark.parametrize('encoding', ['utf-8', 'utf-8-sig'])
def test_env_encodings(tmp_path, encoding):
    env = tmp_path / '.env'
    env.write_text('MODBUS_HOST=192.0.2.10\nMODBUS_DEVICE_ID=\n', encoding=encoding)
    settings = Settings(_env_file=env)
    assert settings.modbus_host == '192.0.2.10'
    assert settings.modbus_device_id is None


@pytest.mark.parametrize('field,value', [
    ('modbus_host', '  '), ('modbus_host', 'host name'),
    ('modbus_port', 0), ('modbus_port', 65536),
    ('modbus_poll_interval', 0), ('modbus_poll_interval', -1),
    ('modbus_poll_interval', float('inf')), ('modbus_poll_interval', float('nan')),
    ('modbus_timeout', 0), ('modbus_timeout', float('inf')),
    ('modbus_retries', -1), ('modbus_retries', 101),
    ('modbus_device_id', 0), ('modbus_device_id', 248),
    ('modbus_read_chunk_size', 0), ('modbus_read_chunk_size', 126),
    ('log_max_bytes', 0), ('log_backup_count', 0),
    ('sqlite_database_path', ''),
])
def test_invalid_settings_fail_before_start(field, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})


def test_valid_boundary_settings():
    settings = Settings(
        _env_file=None, modbus_poll_interval=0.1, modbus_timeout=0.1,
        modbus_retries=0, modbus_port=65535, modbus_device_id=247,
        modbus_read_chunk_size=125,
    )
    assert settings.modbus_poll_interval == 0.1
