# Центр цифровых продуктов САНХОРС (Digital Hub)

**Миссия:** управляемый актив после монтажа СЭС — мониторинг, алерты, отчёты, удержание клиента.

**Спонсор направления:** технический директор (технический блок САНХОРС).

## Роли и реализация

| # | Роль | Ответственность | Как реализована | Репозиторий / артефакт |
|---|------|-----------------|-----------------|------------------------|
| 1 | Product Lead | Roadmap, тарифы, KPI, PRD | Backlog, sync с продажами | `docs/PRODUCT.md` |
| 2 | Tech Lead | Архитектура, ADR, API, профили инверторов | Code review, OpenAPI | `src/inverter_profiles/`, `cloud/openapi.yaml` |
| 3 | Backend | Ingest, auth, billing, алерты | FastAPI-сервисы | `cloud/` |
| 4 | Edge / IoT | Агент, Modbus, sync, OTA | Python agent | `src/`, `install/` |
| 5 | Frontend | Личный кабинет | SPA / static portal | `portal/` |
| 6 | DevOps / SRE | CI/CD, инфра, мониторинг | GitHub Actions, compose | `.github/`, `infra/` |
| 7 | QA | Регресс, симулятор Modbus | pytest, чеклисты | `tests/` |
| 8 | Field Solutions | Установка, активация, runbook | Скрипты, KB | `docs/INSTALL.md`, `install/` |

## KPI на 9 месяцев

| KPI | Цель M9 | Владелец |
|-----|---------|----------|
| Uptime API облака | ≥ 99.5% | DevOps |
| Объектов на тарифе Бизнес+ | ≥ 30 | Product + Sales |
| Время от монтажа до данных в портале | ≤ 24 ч | Field |
| Churn подписок (годовых) | ≤ 10% | Product |
| Покрытие тестами edge | ≥ 70% | QA + Edge |
| MTTR инцидента P1 | ≤ 4 ч (тариф Про) | DevOps + Backend |

## Минимальный штат (старт)

| Роль | FTE |
|------|-----|
| Tech Lead | 0.5–1 |
| Edge / IoT | 1 |
| Backend | 1 |
| Frontend | 1 |
| DevOps | 0.5 |
| QA | 0.5 |
| Field Solutions | 1 (сервис) |
| Product Lead | 0.5 |

## Ритм работы

- Спринт 2 недели, релиз edge — раз в месяц (LTS-ветки)
- Облако — continuous deployment на staging → prod
- Еженедельно: Product + Tech Lead + Field (блокеры установок)
