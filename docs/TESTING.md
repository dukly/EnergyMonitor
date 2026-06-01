# Тестирование EnergyMonitor

## 1) Автотесты без оборудования

Запуск из корня репозитория:

```bash
pip install -r src/requirements.txt -r requirements-dev.txt
pytest
flake8 src tests
```

Ожидаемый результат: все тесты проходят, `flake8` без ошибок.

## 2) Подготовка стенда с USR-W610 и инвертором

1. Подключить инвертор к USR-W610 по RS485 (A/B, скорость обычно 9600 8N1).
2. На USR-W610 выставить:
   - режим `TCP Server (TCPS)`;
   - `Local Port = 502`;
   - привязку канала к COM1-485.
3. На хосте агента проверить доступность:
   - `ping MODBUS_HOST`;
   - `Test-NetConnection MODBUS_HOST -Port 502` (Windows) или `nc -zv MODBUS_HOST 502` (Linux).

## 3) Конфиг для полевого теста

Создать `.env` из шаблона:

```bash
copy .env.example .env
```

Минимально проверить значения:

```env
INVERTER_PROFILE=deye
MODBUS_HOST=192.168.1.1
MODBUS_PORT=502
MODBUS_DEVICE_ID=1
```

Если инвертор использует другой slave ID, изменить `MODBUS_DEVICE_ID`.

## 4) Ручной запуск агента

```bash
cd src
python main.py
```

Признаки успешного опроса в `logs/monitor.log`:

- `Modbus TCP connected ...`
- `Modbus read OK via ...`
- `Measurement saved [#...]`

Проверка данных в SQLite:

```sql
SELECT id, timestamp, power_ac, status_text
FROM measurements
ORDER BY id DESC
LIMIT 5;
```

## 5) Типовые проблемы и действия

- **`ConnectionError ... Unable to connect`**: нет TCP-доступа к USR-W610 (IP/порт/сеть).
- **`No response received after retries`**: TCP есть, но по RS485 нет ответа от инвертора (кабель, питание, slave ID).
- **`All Modbus values are empty`**: не удалось прочитать валидный блок; проверить `INVERTER_PROFILE`, `MODBUS_DEVICE_ID`, настройки W610.

## 6) Правило чистого теста логов

Перед ручной проверкой очистить старый лог, чтобы не смешивать предыдущие прогоны:

```bash
del logs\monitor.log
```

