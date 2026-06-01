# Установка агента EnergyMonitor

## Linux (шлюз / Raspberry Pi)

Скрипты: [`install/gateway/`](../install/gateway/)

| Шаг | Действие |
|-----|----------|
| 1 | Скопировать репозиторий на устройство |
| 2 | RS485 → USR-W610 → LAN, прописать `MODBUS_HOST` в `.env` |
| 3 | `sudo bash install/gateway/install.sh` |
| 4 | Отредактировать `/opt/energy-monitor-agent/.env` |
| 5 | `sudo systemctl enable --now energy-monitor-agent` |

## Windows

Скрипт: [`install/windows/install.ps1`](../install/windows/install.ps1)

## Проверка на объекте

- [ ] USR-W610: TCP Server, порт **502**
- [ ] Ping `MODBUS_HOST` с хоста агента
- [ ] В `logs/monitor.log` появляются строки `Measurement saved`
- [ ] В SQLite есть новые строки: `SELECT * FROM measurements ORDER BY id DESC LIMIT 5;`

## Эскалация

- Modbus timeout: проверить кабель RS485, unit ID, профиль `INVERTER_PROFILE`
- Пустые значения: карта регистров не совпадает с инвертором — сменить профиль или добавить новый в `src/inverter_profiles/`
