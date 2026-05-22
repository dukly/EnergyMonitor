# Сайт САНХОРС (код вместо конструктора)

Статическая версия [sunhors.ru](https://sunhors.ru/) на **HTML, CSS и JavaScript** без Flexbe/Tilda.

## Страницы

| Файл | Назначение |
|------|------------|
| `index.html` | Главная |
| `b2b.html` | Решения для бизнеса |
| `b2c.html` | Решения для дома |
| `company.html` | О компании |
| `contacts.html` | Офисы и заявка |
| `privacy.html` | Политика конфиденциальности |
| `legal.html` | Официальное уведомление |

## Локальный запуск

```bash
cd website
python -m http.server 8080
```

Откройте http://localhost:8080

## Формы заявок

Сейчас заявки сохраняются в `localStorage` браузера (ключ `sunhors_leads`) и открывается WhatsApp.
Для продакшена подключите CRM/API (Roistat, Bitrix, Telegram-бот и т.д.) в `js/main.js`.

## Деплой

Содержимое папки `website/` можно отдать на любой статический хостинг (nginx, GitHub Pages, S3, Netlify).

Изображения пока загружаются с `sunhors.ru/img/...`. При миграции скачайте медиа в `website/img/` и замените URL в HTML/CSS.

## Связь с EnergyMonitor

Лендинг продукта **САНХОРС Мониторинг** — в [`../portal/landing.html`](../portal/landing.html).
