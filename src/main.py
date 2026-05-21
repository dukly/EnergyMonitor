import time

from config import settings
from handler import handle_measurement
from inverter_profiles import get_profile
from libraries.database import Database
from libraries.modbus import ModbusClient
from license import LicenseClient
from logger import logger
from sync.cloud_uploader import CloudUploader


def main() -> None:
    profile = get_profile(settings.inverter_profile)
    logger.info(f'Starting {settings.app_name} (profile={profile.name}, site={settings.site_id})...')

    license_client = LicenseClient()
    license_info = license_client.validate()
    if not license_info.valid:
        logger.error(f'Invalid license: {license_info.message}')
        return
    if license_client.is_expired(license_info.expires_at):
        logger.error('License expired. Agent stopped.')
        return

    logger.info(
        f'License OK: plan={license_info.plan}, cloud_sync={license_info.cloud_sync_enabled}, '
        f'{license_info.message}'
    )

    db = None
    client = None
    uploader = CloudUploader(license_info)

    try:
        db = Database(settings.sqlite_database_path)
        logger.info(f'Connected to SQLite: {settings.sqlite_database_path}')
    except Exception as error:
        logger.error(f'Failed to initialize database: {error}', exc_info=True)
        return

    client = ModbusClient(
        settings.modbus_host,
        settings.modbus_port,
        device_id=profile.device_id,
    )

    try:
        client.connect()
        logger.info(f'Connected to Modbus at {settings.modbus_host}:{settings.modbus_port}')
    except Exception as error:
        logger.error(f'Failed to connect to Modbus: {error}', exc_info=True)
        db.close()
        return

    logger.info(f'Polling interval: {settings.modbus_poll_interval} seconds')

    try:
        while True:
            try:
                handle_measurement(db, client)
                uploader.sync_pending(db)
            except (ConnectionError, OSError) as error:
                logger.error(f'Modbus connection lost: {error}. Retrying on next cycle.', exc_info=True)
                client.close()
            except Exception as error:
                logger.error(f'Error during measurement handling: {error}', exc_info=True)

            time.sleep(settings.modbus_poll_interval)

    except KeyboardInterrupt:
        logger.info(f'Stopping {settings.app_name} (Ctrl+C pressed)')

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


if __name__ == '__main__':
    main()
