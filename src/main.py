import time
from datetime import datetime

from config import settings
from libraries.database import Database
from handler import handle_measurement
from logger import logger
from libraries.modbus import ModbusClient

datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def main():
    """Main function to initialize database and Modbus client, and continuously handle measurements at the specified polling interval."""

    # Log the startup message
    logger.info('Starting Energy Monitor...')

    # Initialize database connection
    db = Database(settings.sqlite_database_path)

    # Initialize Modbus client
    client = ModbusClient(settings.modbus_host, settings.modbus_port)

    # Continuously handle measurements at the specified polling interval
    while True:
        # Handle measurement and save to database
        handle_measurement(db, client)

        # Wait for the next polling interval
        time.sleep(settings.modbus_poll_interval)


if __name__ == '__main__':
    # Start the main function
    main()
