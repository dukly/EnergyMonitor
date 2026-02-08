import struct
import traceback
from datetime import datetime
from pymodbus.client import ModbusTcpClient

INVERTER_IP = "192.168.0.100"
INVERTER_PORT = 502

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
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")

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

def poll_inverter():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"[{timestamp}]"]

    try:
        client = ModbusTcpClient(INVERTER_IP, port=INVERTER_PORT)

        if not client.connect():
            log_error("Не удалось подключиться к инвертеру")
            log_lines.append("Ошибка: нет подключения к инвертеру.")
        else:
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

            client.close()

    except Exception:
        log_error(f"Критическая ошибка:\n{traceback.format_exc()}")
        log_lines.append("Критическая ошибка выполнения скрипта.")

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n\n")

if __name__ == "__main__":
    poll_inverter()
