# Решения по pull request EnergyMonitor

Проверка: 18 октября 2026 года. Main на момент ревью: `195cae70a6c4583d6a009fafed5242660bad1eb2`.
Проверены все 22 открытых PR, №6–27: содержимое патчей, метаданные и CI.

## Выполнение согласованных решений

После согласования с пользователем:

- №6 переведён из draft и слит в main: `5270480933859871e01910de4f57bd51b3f49bba`.
- №7–12 и №14–27 закрыты с поясняющими комментариями: всего 20 PR.
- На №13 опубликован REQUEST_CHANGES с воспроизведением регрессии count=1;
  PR оставлен открытым для доработки.
- Проверка status/error-only телеметрии перенесена отдельно в `handler.py`.
  Добавлены тесты разных статусов и ошибок, а также сохранения нулевых
  числовых показаний.
- Итоговый локальный прогон на Python 3.12: **62 passed**, flake8 и
  `git diff --check` без ошибок.

Далее сохранены исходные выводы ревью; описания draft и статусов CI относятся
к состоянию до выполнения этих действий.

## Рекомендация

Принять **№6 после перевода из draft в ready и актуального CI**.
№7 и №8 закрыть как уже реализованные. №13 отправить на доработку.
№9–12 и №14–27 не принимать в текущем виде: они содержат ошибку восстановления
данных и существенно дублируют друг друга. Из №19–27 стоит отдельно перенести
проверку пустой числовой телеметрии, без их реализации SQLite и повторного
исправления Unit ID.

На момент ревью все 22 PR были draft. GitHub показывал успешную проверку `agent` для
проверенных head-коммитов. Это не означает, что изменения безопасны: дополнительные
тесты обнаружили потерю строк в 18 PR и регрессию fallback в №13.

## Что проверено локально

Для каждого PR восстановлено отдельное дерево из его базового коммита `8a545d3`
и полного набора патчей, полученного через GitHub. Оригинальные тесты каждого
PR прошли: 17–19 тестов в зависимости от PR. Затем исполнены дополнительные
проверки на реальной SQLite и коде соответствующего PR:

- Уже скопированная одна legacy-строка не должна копироваться снова.
- Две одинаковые legacy-строки при одной уже скопированной должны оставить две
  строки в результате, а не одну. Время в БД не уникально, одинаковые измерения
  не запрещены схемой.
- Две одинаковые строки при пустой целевой таблице должны сохраняться обе.
- Если целевая таблица содержит больше одинаковых строк, восстановление не
  должно удалять их или добавлять новые копии.
- Первичная миграция сохраняет одинаковые строки.
- Проверены NULL-значения в сравниваемых полях.
- Устройство, принимающее только count=1, должно читаться через fallback при
  разрешённом `MODBUS_READ_CHUNK_SIZE=1`.
- Проверено, считается ли набор из девяти None и доступных status/error пустой
  числовой телеметрией.

Полные патчи также проверены через `git apply --check` против текущего main.
№6 применяется; остальные 21 патч не применяются напрямую, прежде всего из-за
уже изменённых config.py и test_config.py. Это проверка применения патча, а не
доказательство невозможности разрешить конфликт трёхстороннего Git-слияния.

Для №6 отдельно выполнена интеграционная проверка: патч применён в изолированную
копию текущего main, затем **58 тестов прошли**, flake8 прошёл. Рабочий код проекта
при проверке не изменялся.

## Причины решений

### №6 — принять

[Fix idempotent SQLite legacy migration recovery](https://github.com/dukly/EnergyMonitor/pull/6)

Это единственный предложенный вариант восстановления, который учитывает число
экземпляров одинаковой строки. ROW_NUMBER сопоставляет уже имеющиеся экземпляры
и копирует недостающие; обычная миграция остаётся отдельным путём.
Все дополнительные сценарии количества строк прошли. Вместе с текущим main
прошли 58 тестов и lint. Сначала перевести draft в ready и получить CI для
актуального состояния ветки; сам по себе review не выполняет слияние.

### №7 — закрыть как уже реализованный

[Fix blank Modbus device ID startup crash](https://github.com/dukly/EnergyMonitor/pull/7)

Нормализация пустого/пробельного Unit ID уже есть в `Settings.empty_device_id`
после `195cae7`, вместе с проверкой допустимого диапазона. Повторный валидатор
не добавляет нужного поведения.

### №8 — закрыть как дубликат №7 и текущего main

[Fix blank Modbus device ID config](https://github.com/dukly/EnergyMonitor/pull/8)

Производственное изменение совпадает с №7; задача уже решена в main.

### №9 — не принимать

[Fix SQLite recovery duplication and blank Modbus device ID](https://github.com/dukly/EnergyMonitor/pull/9)

`_copy_legacy_rows`: NOT EXISTS проверяет наличие хотя бы одной строки, не число
экземпляров. При двух legacy-копиях и одной целевой сохраняется одна вместо двух;
затем legacy-таблица удаляется. Unit ID уже исправлен в main. Выбрать №6.

### №10 — не принимать

[Fix legacy migration recovery duplicates](https://github.com/dukly/EnergyMonitor/pull/10)

NULL-safe сравнение через равенство/IS NULL не устраняет ошибку кратности:
воспроизведено 1 вместо 2 строк. Unit ID уже исправлен. Выбрать №6.

### №11 — не принимать

[Fix migration recovery data duplication](https://github.com/dukly/EnergyMonitor/pull/11)

Та же потеря второго экземпляра в `_copy_legacy_rows`; дополнительная обработка
rowcount не исправляет выбор строк. Unit ID уже исправлен. Выбрать №6.

### №12 — не принимать

[Fix Modbus config crash and migration recovery duplication](https://github.com/dukly/EnergyMonitor/pull/12)

Повторяет подход №10: при восстановлении 1 вместо 2 строк. Unit ID уже исправлен.
Выбрать №6.

### №13 — отправить на доработку

[Fix critical Modbus chunking and device ID config bugs](https://github.com/dukly/EnergyMonitor/pull/13)

`ModbusClient._safe_chunk_size` принудительно увеличивает 1 до 2. На устройстве,
принимающем только одиночные чтения, старый fallback работает, а этот PR
возвращает None вместо блока. Это воспроизведено на настоящем методе клиента
с подменой только ответа устройства. Чётные границы могут быть полезны для
целостности float32, но нужно сохранить явно заданный одиночный режим и
покрыть его тестом. Нормализация Unit ID уже есть в main.

### №14 — не принимать

[Fix migration recovery and blank device ID](https://github.com/dukly/EnergyMonitor/pull/14)

Та же потеря кратности NOT EXISTS: 1 вместо 2. SELECT changes() исправляет только
счётчик вставки. Unit ID уже исправлен. Выбрать №6.

### №15 — не принимать

[Fix startup config parsing and migration recovery duplication](https://github.com/dukly/EnergyMonitor/pull/15)

NOT EXISTS теряет второй экземпляр строки. Исправление Unit ID уже в main.
Выбрать №6.

### №16 — не принимать

[Fix critical config and migration recovery bugs](https://github.com/dukly/EnergyMonitor/pull/16)

NOT EXISTS теряет второй экземпляр строки. Дополнительные тесты PR не покрывают
этот сценарий. Исправление Unit ID уже в main. Выбрать №6.

### №17 — не принимать

[Fix blank device ID startup and migration recovery duplicates](https://github.com/dukly/EnergyMonitor/pull/17)

NOT EXISTS с алиасами m/l имеет ту же ошибку: 1 вместо 2. Unit ID уже исправлен.
Выбрать №6.

### №18 — не принимать

[Fix migration recovery duplication and blank device ID startup crash](https://github.com/dukly/EnergyMonitor/pull/18)

NOT EXISTS теряет второй экземпляр строки. Unit ID уже исправлен. Выбрать №6.

### №19 — не принимать целиком

[Fix critical recovery and telemetry validation regressions](https://github.com/dukly/EnergyMonitor/pull/19)

SQLite: 1 вместо 2 строк; Unit ID уже исправлен. Изменение `_is_empty_measurement`,
исключающее status/error из признаков наличия числовой телеметрии, полезно и
прошло дополнительную проверку; его следует перенести отдельно.

### №20 — не принимать целиком

[Fix telemetry startup and recovery regressions](https://github.com/dukly/EnergyMonitor/pull/20)

Те же выводы: потеря строки в SQLite, повтор Unit ID. Проверку status-only
можно вынести отдельно, она эквивалентна предложению №19.

### №21 — не принимать целиком

[Fix telemetry recovery data corruption](https://github.com/dukly/EnergyMonitor/pull/21)

SQLite теряет второй экземпляр; Unit ID уже исправлен. Отдельно сохранить
идею проверки status-only, без повторного внесения остальных изменений.

### №22 — не принимать целиком

[Fix telemetry recovery data corruption](https://github.com/dukly/EnergyMonitor/pull/22)

SQLite: 1 вместо 2 строк. Unit ID повторяет main. Полезный handler-фрагмент
дублирует №19–21 и может быть перенесён одним отдельным изменением.

### №23 — не принимать целиком

[Fix critical telemetry recovery regressions](https://github.com/dukly/EnergyMonitor/pull/23)

Положительное отличие: дедупликация включается только при recovery, а не при
первичной миграции. Но skip_existing всё равно использует проверку наличия
вместо количества и теряет вторую строку. Полезный handler-фрагмент вынести.

### №24 — не принимать целиком

[Fix critical telemetry startup and recovery regressions](https://github.com/dukly/EnergyMonitor/pull/24)

Та же потеря кратности при recovery. Исправления кавычек Windows-задачи и Unit ID
уже реализованы в main; старый участок установщика переработан. Из полезного
остаётся отдельная проверка status-only, аналогичная №19–23.

### №25 — не принимать целиком

[Fix critical telemetry recovery regressions](https://github.com/dukly/EnergyMonitor/pull/25)

skip_existing ограничен recovery, но NOT EXISTS всё равно оставляет 1 вместо 2.
Unit ID уже исправлен; handler-фрагмент вынести отдельно.

### №26 — не принимать целиком

[Fix telemetry startup and recovery data corruption](https://github.com/dukly/EnergyMonitor/pull/26)

Та же ошибка кратности recovery. Unit ID уже исправлен; проверка status-only
полезна отдельно и дублирует предыдущие варианты.

### №27 — не принимать целиком

[Fix telemetry startup and recovery regressions](https://github.com/dukly/EnergyMonitor/pull/27)

Та же потеря второй строки при recovery. Unit ID уже исправлен. Можно взять
только handler-проверку с регрессионным тестом; остальные подобные PR после
этого закрыть как дубликаты.

## Уже закрытые PR

- [№1](https://github.com/dukly/EnergyMonitor/pull/1) и
  [№5](https://github.com/dukly/EnergyMonitor/pull/5) уже merged.
- [№2](https://github.com/dukly/EnergyMonitor/pull/2),
  [№3](https://github.com/dukly/EnergyMonitor/pull/3),
  [№4](https://github.com/dukly/EnergyMonitor/pull/4) закрыты без слияния.

Для них проверен исторический статус. Нового решения о слиянии они не требуют;
их изменения отдельно не перепроверялись на текущем main.

## Ограничения

Проверка выполнена на Python 3.12 в изолированных временных каталогах. БД —
настоящая SQLite; ответы устройств в fallback-проверке подменены. Оборудование
не использовалось. Патчи получены через GitHub и сопоставлены с проверенными
head SHA, отражёнными в CI. После согласования на №13 опубликован REQUEST_CHANGES;
остальные действия перечислены в начале отчёта. Отдельный Canvas не создавался: его SDK и каталог
проектов недоступны в этой среде; результаты сохранены в Markdown.
