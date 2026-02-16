import sqlite3
import time
import json
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        print("Не удалось загрузить config.json, используются значения по умолчанию")
        return {
            "inverter_ip": "192.168.0.100",
            "inverter_port": 502,
            "poll_interval": 5
        }


config = load_config()

def init_db():
    conn = sqlite3.connect("energymonitor.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            timestamp TEXT,
            voltage_dc REAL,
            current_dc REAL,
            power_ac REAL,
            temp REAL,
            freq REAL,
            pf REAL,
            energy_total REAL,
            energy_day REAL,
            runtime REAL,
            status INTEGER,
            error INTEGER
        )
    """)

    conn.commit()
    conn.close()


init_db()


def read_float32(client, address):
    try:
        r1 = client.read_input_registers(address, 1)
        r2 = client.read_input_registers(address + 1, 1)

        if isinstance(r1, ModbusIOException) or isinstance(r2, ModbusIOException):
            return None

        raw = (r1.registers[0] << 16) | r2.registers[0]
        import struct
        return struct.unpack(">f", raw.to_bytes(4, byteorder="big"))[0]

    except:
        return None


def read_int16(client, address):
    try:
        r = client.read_input_registers(address, 1)
        if isinstance(r, ModbusIOException):
            return None
        return r.registers[0]
    except:
        return None


def save_to_db(values):
    conn = sqlite3.connect("energymonitor.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO measurements (
            timestamp, voltage_dc, current_dc, power_ac, temp, freq, pf,
            energy_total, energy_day, runtime, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        values["voltage_dc"],
        values["current_dc"],
        values["power_ac"],
        values["temp"],
        values["freq"],
        values["pf"],
        values["energy_total"],
        values["energy_day"],
        values["runtime"],
        values["status"],
        values["error"]
    ))

    conn.commit()
    conn.close()


def main():
    client = ModbusTcpClient(config["inverter_ip"], port=config["inverter_port"])

    while True:
        if not client.connect():
            print("Ошибка подключения. Повтор через 5 секунд...")
            time.sleep(5)
            continue

        data = {
            "voltage_dc": read_float32(client, 32000),
            "current_dc": read_float32(client, 32002),
            "power_ac": read_float32(client, 32004),
            "temp": read_float32(client, 32006),
            "freq": read_float32(client, 32008),
            "pf": read_float32(client, 32010),
            "energy_total": read_float32(client, 32012),
            "energy_day": read_float32(client, 32014),
            "runtime": read_float32(client, 32016),
            "status": read_int16(client, 32018),
            "error": read_int16(client, 32019)
        }

        save_to_db(data)

        print("Данные сохранены:", data)

        time.sleep(config["poll_interval"])


if __name__ == "__main__":
    main()

