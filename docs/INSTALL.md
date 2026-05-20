# Установка sunhors-agent у клиентов

**Приоритетный канал:** **A — шлюз САНХОРС** (Raspberry Pi / мини-ПК).  
Каналы B и C — для дома и IT-зрелых объектов.

## Канал A: шлюз «под ключ» (рекомендуется B2B)

Скрипты: [`install/gateway/`](../install/gateway/)  
**Закрытый репозиторий для Raspberry Pi:** `sunhors-agent-rpi` (рядом с EnergyMonitor, только пакет шлюза)

| Шаг | Действие |
|-----|----------|
| 1 | Прошить образ / установить пакет агента на шлюз |
| 2 | RS485 → USR-W610 → LAN, прописать `MODBUS_HOST` в `.env` |
| 3 | Активация: `SITE_ID` + `LICENSE_KEY` (QR → portal) |
| 4 | `sudo systemctl enable --now sunhors-agent` |
| 5 | Проверить телеметрию в портале через 5–15 мин |

## Канал B: Windows на объекте

Скрипт: [`install/windows/sunhors-install.ps1`](../install/windows/sunhors-install.ps1)

- Установка Python-зависимостей и задачи Планировщика / службы
- Мастер: IP USR-W610, лицензия

## Канал C: Docker

Файл: [`install/docker/docker-compose.yml`](../install/docker/docker-compose.yml)

- Для NAS/сервера клиента, исходящий HTTPS 443

## Runbook Field Solutions

### До выезда

- [ ] В портале создан объект (`SITE_ID`)
- [ ] Выдан `LICENSE_KEY` и тариф
- [ ] Известен тип инвертора → `INVERTER_PROFILE`

### На объекте

- [ ] USR-W610 в TCP Server, порт 502
- [ ] Ping `MODBUS_HOST` с шлюза
- [ ] `.env` скопирован из `.env.example`
- [ ] Агент запущен, в `logs/monitor.log` нет ERROR

### Сдача

- [ ] В портале видна последняя точка телеметрии
- [ ] Клиенту передан доступ в portal
- [ ] Тикет закрыт с номером `site_id`

### Эскалация в Edge-команду

- Modbus timeout > 30 мин
- Несовпадение регистров → смена `INVERTER_PROFILE` или новый профиль
