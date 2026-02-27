import time
from datetime import datetime

from config import settings
from libraries.database import Database
from libraries.modbus import ModbusClient
from handler import handle_measurement
from logger import logger


def main():
    logger.info("Starting Energy Monitor (console mode)...")

    # Initialize database
    try:
        db = Database(settings.sqlite_database_path)
        logger.info(f"Connected to SQLite: {settings.sqlite_database_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # Initialize Modbus client
    client = ModbusClient(settings.modbus_host, settings.modbus_port)

    # Try to connect to Modbus
    try:
        client.connect()
        logger.info(f"Connected to Modbus at {settings.modbus_host}:{settings.modbus_port}")
    except Exception as e:
        logger.error(f"Failed to connect to Modbus: {e}")
        return

    logger.info(f"Polling interval: {settings.modbus_poll_interval} seconds")

    try:
        while True:
            try:
                # Your handler reads Modbus and saves to DB
                handle_measurement(db, client)

            except Exception as e:
                logger.error(f"Error during measurement handling: {e}")

            time.sleep(settings.modbus_poll_interval)

    except KeyboardInterrupt:
        logger.info("Stopping Energy Monitor (Ctrl+C pressed)")

    finally:
        try:
            client.close()
            logger.info("Modbus connection closed")
        except:
            pass


if __name__ == "__main__":
    main()
