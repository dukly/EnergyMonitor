from datetime import datetime

from config import settings
from inverter_profiles import get_profile
from libraries.database import Database
from libraries.modbus import InverterMeasurement, ModbusClient
from logger import logger
from status_labels import decode_error, decode_status


def _is_empty_measurement(measurement: InverterMeasurement) -> bool:
    return all(value is None for value in (
        measurement.voltage_dc,
        measurement.current_dc,
        measurement.power_ac,
        measurement.temp,
        measurement.freq,
        measurement.pf,
        measurement.energy_total,
        measurement.energy_day,
        measurement.runtime,
        measurement.status,
        measurement.error,
    ))


def handle_measurement(db: Database, client: ModbusClient) -> int | None:
    profile = get_profile(settings.inverter_profile)
    client.device_id = (
        settings.modbus_device_id
        if settings.modbus_device_id is not None
        else profile.device_id
    )

    client.ensure_connected(retries=3)

    measurement = client.read_measurement_block(
        start_address=profile.register_start,
        count=profile.register_count,
        register_kind=profile.register_kind,
    )

    if _is_empty_measurement(measurement):
        logger.error(
            'All Modbus values are empty (no valid register block). '
            'Closing connection for reconnect on next cycle.',
        )
        client.close()
        return None

    status_text = decode_status(measurement.status)
    error_text = decode_error(measurement.error)

    return db.save_measurement(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        voltage_dc=measurement.voltage_dc,
        current_dc=measurement.current_dc,
        power_ac=measurement.power_ac,
        temp=measurement.temp,
        freq=measurement.freq,
        pf=measurement.pf,
        energy_total=measurement.energy_total,
        energy_day=measurement.energy_day,
        runtime=measurement.runtime,
        status=measurement.status,
        error=measurement.error,
        status_text=status_text,
        error_text=error_text,
    )
