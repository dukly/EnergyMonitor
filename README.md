# EnergyMonitor

Агент сбора телеметрии инвертора по **Modbus TCP** (например USR-W610 в режиме TCP Server, порт 502) с записью в **SQLite**.

## Структура

| Путь | Назначение |
|------|------------|
| [`src/`](src/) | Агент: Modbus → SQLite, логи |
| [`src/inverter_profiles/`](src/inverter_profiles/) | Карты регистров (default, deye, goodwe) |
| [`install/gateway/`](install/gateway/) | Установка на Linux (systemd) |
| [`install/windows/`](install/windows/) | Установка на Windows (Планировщик задач) |
| [`docs/INSTALL.md`](docs/INSTALL.md) | Краткий runbook установки |

## Быстрый старт

```bash
copy .env.example .env
# Отредактируйте MODBUS_HOST, INVERTER_PROFILE

cd src
pip install -r requirements.txt
python main.py
```

Данные: `data/monitor.db` (по умолчанию). Логи: `logs/monitor.log`, `logs/error.log`.

### USR-W610

- RS485 к инвертору (обычно 9600 8N1)
- Режим **TCP Server (TCPS)**, **Local Port = 502**
- В `.env`: `MODBUS_HOST` — IP модуля (часто `192.168.1.1`)

## Профили инверторов

`INVERTER_PROFILE`: `default`, `deye`, `goodwe`

При неверном значении агент завершится с ошибкой в логе.

## Тесты

```bash
pip install -r src/requirements.txt
pip install -r requirements-dev.txt
pytest
flake8 src tests
```
