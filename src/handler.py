from datetime import datetime

from database import Database
from logger import logger
from modbus import ModbusClient


def handle_measurement(db: Database, client: ModbusClient) -> None:
    # Try to connect to Modbus server, if it fails, log the error and retry after 5 seconds
    try:
        client.connect(timeout=5, retries=3)
    except ConnectionError as e:
        logger.error(f'Unable to connect to Modbus server: {e}. Measurement skipped.', exc_info=True)
        return

    # Read data from Modbus registers and save to database
    db.save_measurement(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        voltage_dc=client.read_float32(32000),
        current_dc=client.read_float32(32002),
        power_ac=client.read_float32(32004),
        temp=client.read_float32(32006),
        freq=client.read_float32(32008),
        pf=client.read_float32(32010),
        energy_total=client.read_float32(32012),
        energy_day=client.read_float32(32014),
        runtime=client.read_float32(32016),
        status=client.read_int16(32018),
        error=client.read_int16(32019),
    )

    # Close Modbus connection
    client.close()
