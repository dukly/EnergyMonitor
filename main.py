import struct
import traceback
import time
import json
from datetime import datetime
from pymodbus.client import ModbusTcpClient


def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print("⚠ Ошибка: не удалось загрузить config.json. Используются значения по умолчанию.")
        return {
            "inverter_ip": "192.168.0.100",
            "inverter_port": 502,
            "poll_interval": 5,
            "log_file": "log.txt",
            "error_log": "error_log.txt"
        }


config = load_config()

INVERTER_IP = config["inverter_ip"]
INVERTER_PORT = config["inverter_port"]
POLL_INTERVAL = config["poll_interval"]
LOG_FILE = config["log_file"]
ERROR_LOG = config["error_log"]

REGISTER_MAP = {
    "Напряжение DC": (32000, "float"),
    "Ток DC": (32002, "float"),
    "Мощность AC": (32004, "float"),
    "Температура корпуса": (32006, "float"),
    "Частота сети": (32008, "float"),
    "Коэффициент мощности": (32010, "float"),
    "Общая энергия": (32012, "float"),
    "Энергия за день": (32014, "float"),
    "Время работы": (32016, "float"),
    "Статус инвертера": (32018, "int"),
    "Код ошибки": (32019, "int")
}

STATUS_MAP = {
    0: "Отключён",
    1: "Работает",
    2: "Ожидание",
    3: "Ошибка",
    4: "Тестирование"
}

ERROR_MAP = {
    0: "Нет ошибок",
    1: "Перегрев",
    2: "Перенапряжение",
    3: "Недостаточное напряжение",
    4: "Ошибка связи"
}

def log_error(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def log_data(lines):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n\n")


def read_float32(client, address, name):
    try:
        r1 = client.read_input_registers(address)
        r2 = client.read_input_registers(address + 1)

        if r1.isError() or r2.isError():
            log_error(f"Ошибка чтения FLOAT32 {address} ({name})")
            return "Ошибка чтения"

        regs = [r1.registers[0], r2.registers[0]]
        raw = struct.pack(">HH", regs[0], regs[1])
        value = struct.unpack(">f", raw)[0]
        return round(value, 2)

    except Exception:
        log_error(f"Исключение FLOAT32 {address} ({name}):\n{traceback.format_exc()}")
        return "Исключение"


def read_int16(client, address, name):
    try:
        r = client.read_input_registers(address)

        if r.isError():
            log_error(f"Ошибка чтения INT16 {address} ({name})")
            return "Ошибка чтения"

        return r.registers[0]

    except Exception:
        log_error(f"Исключение INT16 {address} ({name}):\n{traceback.format_exc()}")
        return "Исключение"


def connect_with_retry():
    while True:
        client = ModbusTcpClient(INVERTER_IP, port=INVERTER_PORT)
        if client.connect():
            print("✔ Подключение установлено")
            return client
        else:
            print("✖ Не удалось подключиться. Повтор через 5 сек...")
            log_error("Не удалось подключиться к инвертеру")
            time.sleep(5)

def poll_inverter_loop():
    client = connect_with_retry()

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_lines = [f"[{timestamp}]"]

        try:
            if not client.connect():
                raise ConnectionError("Потеряна связь с инвертером")

            for name, (address, dtype) in REGISTER_MAP.items():
                if dtype == "float":
                    value = read_float32(client, address, name)
                else:
                    value = read_int16(client, address, name)

                if isinstance(value, str):
                    log_lines.append(f"{name}: {value}")
                elif name == "Статус инвертера":
                    log_lines.append(f"{name}: {value} ({STATUS_MAP.get(value, 'Неизвестно')})")
                elif name == "Код ошибки":
                    log_lines.append(f"{name}: {value} ({ERROR_MAP.get(value, 'Неизвестно')})")
                else:
                    log_lines.append(f"{name}: {value}")

            log_data(log_lines)
            print("✔ Данные записаны")

        except Exception as e:
            log_error(f"Потеря связи или ошибка: {e}")
            print("⚠ Потеря связи. Переподключение...")
            client.close()
            client = connect_with_retry()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    poll_inverter_loop()

