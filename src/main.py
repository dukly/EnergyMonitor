import time

from config import settings
from handler import handle_measurement
from inverter_profiles import get_profile
from libraries.database import Database
from libraries.modbus import ModbusClient
from logger import logger


def main() -> int:
    try:
        profile = get_profile(settings.inverter_profile)
    except ValueError as error:
        logger.error(str(error))
        return 1

    logger.info(f'Starting {settings.app_name} (profile={profile.name})...')

    db = None
    client = None

    try:
        db = Database(settings.sqlite_database_path)
        logger.info(f'Connected to SQLite: {settings.sqlite_database_path}')
    except Exception as error:
        logger.error(f'Failed to initialize database: {error}', exc_info=True)
        return 1

    device_id = (
        settings.modbus_device_id
        if settings.modbus_device_id is not None
        else profile.device_id
    )
    logger.info(f'Polling interval: {settings.modbus_poll_interval} seconds')

    try:
        client = ModbusClient(
            settings.modbus_host,
            settings.modbus_port,
            device_id=device_id,
        )
        while True:
            try:
                handle_measurement(db, client)
            except (ConnectionError, OSError) as error:
                logger.error(f'Modbus unavailable: {error}. Retrying on next cycle.', exc_info=True)
                client.close()
            except Exception as error:
                logger.error(f'Error during measurement handling: {error}', exc_info=True)

            time.sleep(settings.modbus_poll_interval)

    except KeyboardInterrupt:
        logger.info(f'Stopping {settings.app_name} (Ctrl+C pressed)')

    except Exception as error:
        logger.error(f'Agent failed: {error}', exc_info=True)
        return 1

    finally:
        if client is not None:
            try:
                client.close()
                logger.info('Modbus connection closed')
            except Exception as error:
                logger.error(f'Failed to close Modbus connection: {error}', exc_info=True)

        if db is not None:
            db.close()
            logger.info('Database connection closed')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
