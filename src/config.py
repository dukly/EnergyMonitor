from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for the Energy Monitor application."""

    # Modbus
    modbus_host: str = 'localhost'
    modbus_port: int = 502
    modbus_poll_interval: int = 5

    # SQLite
    sqlite_database_path: str = 'energymonitor.db'

    # Configuration for loading settings from environment variables or .env file
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )


# Load settings from environment variables or .env file
settings = Settings()
