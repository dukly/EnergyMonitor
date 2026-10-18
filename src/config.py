from pathlib import Path

from pydantic import Field, field_validator
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

    modbus_host: str = Field(default='localhost', min_length=1)
    modbus_port: int = Field(default=502, ge=1, le=65535)
    modbus_poll_interval: float = Field(default=5, gt=0, allow_inf_nan=False)
    modbus_timeout: float = Field(default=10.0, gt=0, allow_inf_nan=False)
    modbus_retries: int = Field(default=5, ge=0, le=100)
    modbus_device_id: int | None = Field(default=None, ge=1, le=247)
    modbus_read_chunk_size: int = Field(default=10, ge=1, le=125)

    sqlite_database_path: str = 'data/monitor.db'

    log_file_path: str = 'logs/monitor.log'
    error_log_file_path: str = 'logs/error.log'
    log_max_bytes: int = Field(default=1_048_576, gt=0)
    log_backup_count: int = Field(default=3, ge=1)

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / '.env',
        env_file_encoding='utf-8-sig',
        case_sensitive=False,
    )

    @field_validator('modbus_host')
    @classmethod
    def validate_host(cls, value: str) -> str:
        value = value.strip()
        if not value or any(char.isspace() for char in value):
            raise ValueError('MODBUS_HOST must be a hostname or IP address without whitespace')
        return value

    @field_validator('modbus_device_id', mode='before')
    @classmethod
    def empty_device_id(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator(
        'sqlite_database_path',
        'log_file_path',
        'error_log_file_path',
        mode='before',
    )
    @classmethod
    def resolve_paths(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError('Path must not be empty')
        return str(resolve_project_path(value))


settings = Settings()
