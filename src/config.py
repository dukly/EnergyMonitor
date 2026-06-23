from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_project_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


class Settings(BaseSettings):
    """Settings for the EnergyMonitor telemetry agent."""

    app_name: str = 'energy-monitor-agent'
    inverter_profile: str = 'default'

    modbus_host: str = 'localhost'
    modbus_port: int = 502
    modbus_poll_interval: int = 5
    modbus_timeout: float = 10.0
    modbus_retries: int = 5
    modbus_device_id: int | None = None
    modbus_read_chunk_size: int = 10

    sqlite_database_path: str = 'data/monitor.db'

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

    @field_validator('modbus_device_id', mode='before')
    @classmethod
    def normalize_blank_device_id(cls, value: object) -> object:
        if isinstance(value, str) and value.strip() == '':
            return None
        return value


settings = Settings()
