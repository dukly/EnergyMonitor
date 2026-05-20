from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent


def resolve_project_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


class Settings(BaseSettings):
    """Settings for SUNHORS sunhors-agent."""

    app_name: str = 'sunhors-agent'

    site_id: str = 'demo-site'
    license_key: str = ''
    inverter_profile: str = 'default'

    modbus_host: str = 'localhost'
    modbus_port: int = 502
    modbus_poll_interval: int = 5
    modbus_device_id: int = 1
    modbus_register_start: int = 32000
    modbus_register_count: int = 20

    license_api_url: str = 'http://localhost:8000'
    cloud_api_url: str = 'http://localhost:8000'
    cloud_request_timeout: float = 10.0
    cloud_sync_batch_size: int = 50

    sqlite_database_path: str = 'data/sunhors.db'

    log_file_path: str = 'logs/monitor.log'
    error_log_file_path: str = 'logs/error.log'
    log_max_bytes: int = 1_048_576
    log_backup_count: int = 3

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / '.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

    @field_validator(
        'sqlite_database_path',
        'log_file_path',
        'error_log_file_path',
        mode='before',
    )
    @classmethod
    def resolve_paths(cls, value: str) -> str:
        return str(resolve_project_path(value))


settings = Settings()
