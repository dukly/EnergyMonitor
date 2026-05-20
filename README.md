# САНХОРС Мониторинг (sunhors-agent)

Edge-агент для мониторинга инвертора по Modbus TCP (USR-W610) с синхронизацией в **SUNHORS Energy Cloud**.

Продукт компании **САНХОРС** — [sunhors.ru](https://sunhors.ru/)

## Компоненты репозитория

| Путь | Назначение |
|------|------------|
| [`src/`](src/) | sunhors-agent (Modbus → SQLite → cloud) |
| [`cloud/`](cloud/) | MVP API: license, telemetry, metrics |
| [`portal/`](portal/) | Личный кабинет (MVP) |
| [`infra/`](infra/) | Docker Compose: Postgres + API + portal |
| [`install/`](install/) | Установка: шлюз / Windows / Docker |
| [`docs/`](docs/) | Продукт, команда, runbook |

## Быстрый старт

### 1. Облако + портал (локально)

```bash
cd infra
docker compose up -d
```

- API: http://localhost:8000/docs  
- Портал: http://localhost:8080  

### 2. Агент на объекте

```bash
copy .env.example .env
cd src
pip install -r requirements.txt
python main.py
```

Демо-ключ: `LICENSE_KEY=demo-business-key`, `SITE_ID=demo-site`

## Тарифы

См. [docs/PRODUCT.md](docs/PRODUCT.md)

## Установка у клиентов

См. [docs/INSTALL.md](docs/INSTALL.md) — приоритет **канал A** (шлюз Raspberry Pi).

## Dev-отдел

См. [docs/TEAM.md](docs/TEAM.md)

## Тесты

```bash
pip install -r src/requirements.txt
pip install -r requirements-dev.txt
pytest
flake8 src tests
```
