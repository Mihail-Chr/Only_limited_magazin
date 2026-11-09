# Рабочий контекст (снимок по дням)

Обновляется перед рискованным шагом и в конце сессии. Не история — только «где мы сейчас».
История решений — в `HISTORY.md`.

## 🛑 ПРАВИЛА ОБЩЕНИЯ И ПОДАЧИ МАТЕРИАЛА (КРИТИЧНО!)

1. **Только полные файлы.** Никаких «вставь сюда», «добавь в функцию такую-то строку». Если нужно изменить файл — пиши его ЦЕЛИКОМ (от первой до последней строки), чтобы я мог скопировать (`Ctrl+A` -> `Delete` -> `Paste`).
2. **Никаких «вырезок».** Если ответ не влезает в лимит символов — разбей его на логические шаги, но каждый шаг должен содержать ПОЛНЫЙ файл.
3. **Пиши по-русски.** Профессиональные термины давай в скобках на английском, но объясняй понятным языком.
4. **Не переспрашивай то, что уже решено.** Если это есть в `CONTEXT.md` или `HISTORY.md` — не задавай вопросов, а действуй.
5. **Перед тем как дать код — объясни, ЧТО и ЗАЧЕМ мы делаем.** В 2–3 предложениях. И только потом давай полные файлы.
6. **Фокус на одной задаче за раз.** Сначала чиним одно, проверяем, потом другое.

---

## 📅 2026-10-30 — Начало рефакторинга парсера (TDD)

- **Ветка:** `test/parser-target-behavior`.
- **Цель:** переписать `parse_names.py` под TDD (сначала тест, потом код).
- **Сделано:** 24 тест-кейса, вынос логики в `src/parsers/`, словари из БД, `media_type`, edition-anchor, steelbook, все платформы.
- **Статус:** 24/24 зелёных.

## 📅 2026-10-31 — Доработка парсера, правила дублей

- **Сделано:** `SINGLE_WORD_EDITION_MAP` (Platinum/Classic/Black/Tails/Knuckles), «не удалять нераспознанные скобки», `france exclusive` в `EDITION_MAP`, `de cover`/`ntsc-j`/`ntsc-u`/`pal-uk`/`pal-eu` в `REGION_MAP`.
- **Правила дублей:** `BASE_NAME` → `PLATFORM` → `EDITION` → `REGION_ID` → `MEDIA_TYPE` → `PUBLISHER`.
- **Статус:** 27/27 зелёных. 58 → 39 пар (ложные ушли).

## 📅 2026-11-01 — Product manager: план MVP, ручные продажи, миграция

- **Цель MVP:** запустить продукт, вводить товары не на площадке, вести продажи.
- **Сделано:** `merge_duplicates` отложен. Ручная продажа через `posting`/`posting_item` (`source='manual'`). `posting` += `source`, `buyer_nickname`, `buyer_id`. Создан store `manual`. Продажа без остатка запрещена.

## 📅 2026-11-02 — UI: Ручная продажа, Меню Продавца, УТ, Копирование

- **Сделано:** Ручная продажа (форма, история). Меню Продавца (поиск, фильтры, сортировка, цена OZON). УТ (фильтры в заголовках, инлайн-остатки, «Ред.»/«Копия»). Добавление/Редактирование/Копирование (единый шаблон). Инвентаризация (фильтр по платформе).
- **Статус:** UI готов, деплой на AdminVPS.

## 📅 2026-11-03 — Деплой на AdminVPS, домен, HTTPS

- **Сделано:** Nginx, systemd, SSL (Let's Encrypt), домен `only-limited-magazin.ru` (A-запись на 79.133.183.30).
- **Проблемы:** Git-отставание, пустая база после `git pull`, кэш браузера.
- **Статус:** Сайт работает по `https://only-limited-magazin.ru`.

## 📅 2026-11-04 — Удаление базы из Git, `restore`, строгие дубли

- **Сделано:** `git filter-repo` (удаление базы из истории). Поле `restore` (для `(Лицензия)`). Строгое сравнение `platform` (PS4/PS5 ≠ PS4). `export_duplicates_xlsx.py` обновлён (0 пар).
- **Статус:** База больше не в Git. Дубли работают строго.

---

## 📌 Текущий этап (2026-11-04)

Ветка: `refactor/v2-schema` → merge в `main`.
Сайт: **https://only-limited-magazin.ru** (работает).
Сервер: AdminVPS (79.133.183.30), Nginx + Uvicorn (systemd).

## ✅ Решено (актуальное, НЕ переспрашивать)

- `merge_duplicates` — отложен (нет согласия владельца).
- Ручная продажа — минимум: дата, товар, кол-во, цена.
- Товар для продажи — только из существующих (`product`), с остатком > 0.
- `buyer_id` — колонка, таблица `buyer` — создана (Физлицо=1).
- ПД не храним (кроме никнейма «Физлицо»).
- `(Лицензия)` → `restore=1`, удаляется из `base_name`.
- `PS4/PS5` — отдельная сущность (строгое сравнение).
- База данных **не** в Git. При деплое — копировать вручную (`scp`).

## ⏳ Отложено

- `merge_duplicates.py` (согласие владельца).
- UI-проверка дублей при вводе (следующая задача!).
- `check_info_list_coverage.py`.
- `pipeline0` / `base_pipeline` — разделить.
- `seed_reference_data.py`: портативные платформы, `KR`.
- Переименование карточек в OZON через API.
- Удаление товара (только если нет истории продаж).
- Добавление склада (`store`) в отчёты и формы.
- Выделение роли «Администратор» (загрузка/выгрузка, дубли).
- Новая загрузка карточек (кнопка в интерфейсе).
- Поиск у Покупателя (внешние сайты, `avg_market_price`, Telegram).

## ❓ Открытые вопросы

- Как мягко называть `restore` на OZON (английская форма `Restore`).
- `K.O.`, `Remastered Edition`, `GOTY` — добавлять ли в `EDITION_MAP` (сейчас нет).

## ⏳ Отложено (добавить в Настройки)
- Редактирование названий в выпадающих списках (склады, платформы, издания, издатели). Пример: сегодня Виталий, завтра Ольга.

## Текущий этап (2026-11-04)

Ветка: `refactor/v2-schema`.
Сайт: **https://only-limited-magazin.ru** (работает, HTTPS).
Сервер: AdminVPS (79.133.183.30), Nginx + Uvicorn (systemd).

**Последние изменения:**
- **Склады:** добавлены `Виталий` (id=1) и `Вениамин` (id=4). Колонка «Склад» с выпадающим списком в Инвентаризации и УТ. В Экране Продавца — только чтение. В форме добавления/редактирования — обязательный выбор склада. Кнопка «+» для создания нового склада.
- **Delete:** кнопка «Удалить» в УТ (работает только если нет продаж).
- **Сортировка:** в УТ и Экране Продавца — стрелочки (Название, Платформа, Издание, Склад), приоритетная очередь, третье нажатие снимает сортировку.

- **Настройки:** раздел для редактирования названий в выпадающих списках (склады, платформы, издания, издатели). Пример: сегодня Виталий, завтра Ольга.
- **Pipeline:** заполнение складов (`Виталий`, `Вениамин`) через `seed_reference_data.py`, а не вручную. Убрать костыли из `add_stores.py`.

## Текущий этап (2026-11-05)

Ветка: `refactor/v2-schema`.
Сайт: **https://only-limited-magazin.ru** (работает, HTTPS).
Сервер: AdminVPS (79.133.183.30), Nginx + Uvicorn (systemd).

**Последние изменения:**
- **Меню «Настройки»** (`/settings`):
  - Загрузка данных (Площадка → Магазин → Действие: карточки / движение товаров).
  - Редактирование справочников (склады, платформы, издания, издатели, регионы).
  - Резервная копия (загрузить/восстановить базу).
- **Поле `platform` в `store`** — для фильтрации магазинов по площадке.
- **Универсальные модальные окна** — для загрузки, редактирования, уведомлений.

**Отложено:**
- Перенос выгрузки/загрузки базы из меню Кладовщика в Настройки.
- Удаление «Синхронизация OZON» из меню Продавца (после проверки нового меню).
- Редактирование названий складов (частично сделано, нужно доделать).
- Поиск у Покупателя (внешние сайты, `avg_market_price`, Telegram).

## Текущий этап (2026-11-05)

Ветка: `refactor/v2-schema`.
Сайт: **https://only-limited-magazin.ru** (работает, HTTPS, меню «Настройки»).
Сервер: AdminVPS (79.133.183.30), Nginx + Uvicorn (systemd).

**Последние изменения:**
- **Меню «Настройки»** (`/settings`): загрузка данных (Площадка → Магазин → Действие), редактирование справочников, резервная копия.
- **Поле `platform` в `store`** — для фильтрации магазинов по площадке.
- **Back Review:** начат аудит архитектуры (строки vs ID). В `product` поля `platform`, `edition`, `publisher`, `product_type`, `media_type`, `genre`, `language`, `developer`, `age_rating`, `country_of_origin` — строки, а не ID. Это костыль.

**Текущая задача:** Back Review (ревизия архитектуры). Первый шаг — аудит (`scratch/audit_schema.py`).

**Отложено:**
- Миграция на ID-поля (Вариант А).
- Перенос выгрузки/загрузки базы из меню Кладовщика в Настройки.
- Удаление «Синхронизация OZON» из меню Продавца.
- Поиск у Покупателя (внешние сайты, avg_market_price, Telegram).

## Текущий этап (2026-11-05)

Ветка: `refactor/v2-schema`.
Сайт: **https://only-limited-magazin.ru** (работает, HTTPS, меню «Настройки»).
Сервер: AdminVPS (79.133.183.30), Nginx + Uvicorn (systemd).

**Последние изменения:**
- **Меню «Настройки»** (`/settings`): загрузка данных, редактирование справочников, резервная копия.
- **Поле `platform` в `store`** — для фильтрации магазинов по площадке.
- **Back Review:** аудит показал, что в `product` 5 полей — строки (`platform`, `edition`, `publisher`, `product_type`, `media_type`). В `posting.status` — строка. Это костыли.

**Текущая задача:** Миграция на ID-поля (Вариант А).
1. Создать справочники (`mediaTypes`, `ageRatings`, `developers`, `statuses`).
2. Добавить ID-поля в `product`.
3. Миграция (заполнить ID из строк).
4. Удалить строковые поля (или оставить как денормализацию).
5. Переписать парсер, фильтры, формы, синхронизацию, редактирование.

**Отложено:**
- Перенос выгрузки/загрузки базы из меню Кладовщика в Настройки.
- Удаление «Синхронизация OZON» из меню Продавца.
- Поиск у Покупателя (внешние сайты, avg_market_price, Telegram).

## 📅 2026-11-05 — Ложка 1: принципы рефакторинга (закрыта)

**Ветка:** `refactor/schema-audit` (от `refactor/v2-schema`).

**Принципы (не переспрашивать):**
- `camelCase`.
- Нормализация А: только ID, `JOIN`. Строки удаляются.
- `platforms`: `platformVersion` не переименовываем. `revision`, `is_portable` — оставляем.
- `modules` — таблица (`moduleName TEXT PK`, `isEnabled`, `sortOrder`, `description`, `versionAdded`).
- Модули: `purchase` (0), `sale` (1), `inventory` (1), `ozon_sync` (1), `manual_sale` (1), `monitoring` (0).
- Площадки: `purchasePlatforms`, `marketplaces`, `store` (с `marketplaceId` FK).
- `manual` — отдельный маркетплейс.
- `avgSellCost`: `avgSellCost` (RUB), `avgSellCostUpdatedAt`, `avgSellCostSamples`, `avgSellCostBreakdown` (JSON, для отладки). Формула: `AVG(AVG(площадки) × курс → RUB)`.
- Тесты: pytest + CI/CD (GitHub Actions). Репозиторий публичный.
- Pipeline: после первой итерации.
- Данные из старой БД — не переносим.

**`scratch/` — судьба файлов:**

| Файл | Судьба |
|---|---|
| `check_sync.py` | Удалить |
| `add_buyer.py` | Удалить (в seed) |
| `migrate_manual_sales.py` | → `src/scripts/migrations/` |
| `check_posting.py` | Удалить |
| `check_sales_schema.py` | Удалить |
| `add_platforms.py` | Удалить (в seed) |
| `export_editions_in_db.py` | Удалить |
| `generate_sql.py` | → `src/scripts/` |
| `fetch_rawg.py` | → `src/scripts/` |
| `audit_schema.py` | → `tests/test_schema.py` |
| `add_platform_to_store.py` | → `src/scripts/migrations/` |
| `add_warehouses.py` | Удалить (в seed) |
| `export_duplicates_xlsx.py` | → `src/scripts/` |
| `add_restore.py` | → `src/scripts/migrations/` |
| `clear_and_sync.py` | Удалить |

**Следующая ложка:** Ложка 2 — аудит `schema.sql` (список правок без кода).

## 📅 2026-11-07 — Часть 4: склад, действия, возвраты (утверждено)

**Решения (не переспрашивать):**
- `stock` — `warehouseId`, `productId`, `quantity`, `countOfRepair`, `createdAt`, `updatedAt`.
- `stock_manual` — удалить. Ручной ввод — `product.offerId = NULL`.
- `stock_history` — аудит: `quantityDelta`, `reasonId`, `sourceType`, `sourceId`, `createdAt`.
- `returnReasons` — справочник причин: `reasonId`, `code`, `name`, `context`, `sortOrder`, `isActive`. Без `action`.
- `stockWriteOffs` — `productId`, `warehouseId`, `quantity`, `reasonId`, `sourceType`, `sourceId`, `writeOffDate`, `notes`, `createdAt`, `updatedAt`.
- `salesReturns` — `salesOrderId`, `productId`, `warehouseId` (NOT NULL), `quantity`, `reasonId`, `returnDate`, `refundAmount`, `notes`, `createdAt`, `updatedAt`.
- `purchaseReturns` — `purchaseOrderId`, `productId`, `warehouseId` (nullable), `quantity`, `reasonId`, `returnDate`, `refundAmount`, `notes`, `createdAt`, `updatedAt`.
- `price_history` — отложить.
- `market_offers` — удалить.
- `customs` — развести: `customsDuty`, `customsClearance`, `customsOffice`. Статус `customs` — оставить.

**Сценарий покупки (5 этапов):**
1. Заказ на сайте → отказ продавца.
2. Склад агрегатора → пересортица, некомплект.
3. Таможня экспорт → возврат отправителю (повтор / возврат / потеря).
4. Таможня импорт (РФ) → отказ (доставка возврата, повтор).
5. Получение → качество, некомплект заказа, некомплект товара.

**Причины:** см. `returnReasons` в `HISTORY.md`.

**Следующая ложка:** Часть 5 — транзакции (`posting`, `posting_item`, `buyer`, `sync_log`, `payouts`, `payoutAdjustments`).

## 📅 2026-11-08 — Тесты: инфраструктура + первые тесты (Ложка 6)

**Ветка:** `refactor/schema-audit`.

**Сделано:**

- **`schema.sql` v3.1** — 35 таблиц (Части 1–5).
- **`init_db.py`** — создаёт БД из `schema.sql`.
- **`seed_reference_data.py`** — 16 справочников.
- **`run.bat`** — для разработки (активирует venv, запускает команду).
- **`run_test.bat`** — для тестов (активирует venv, запускает `pytest`).
- **`pytest.ini`** — маркеры (`unit`, `integration`, `api`), `testpaths`.
- **Структура тестов:** `tests/unit/`, `tests/integration/`, `tests/api/`.
- **`tests/conftest.py`** — `db_conn` (function scope).
- **`tests/unit/conftest.py`** — `setup_test_db` (session scope, создаёт БД, наполняет справочниками).
- **`tests/unit/test_db.py`** — 4 теста.
- **`tests/unit/test_pragma.py`** — 3 теста.
- **`tests/unit/test_seed.py`** — 16 тестов.

**Результат:** **23/23 PASSED**.

**Принципы (не переспрашивать):**
- TDD: тесты **до** кода.
- Fixtures (тестовые данные) — must have.
- Моки — только для **внешних** API (OZON).
- Реальный API — для **интеграционных** тестов (`@pytest.mark.integration`).
- `run_test.bat` — **всегда** активирует venv (не зависит от PowerShell).

**Проблемы, которые решили:**
- `ModuleNotFoundError: No module named 'fastapi'` — `pytest` в другом окружении. Решение: `run_test.bat`.
- `no such table: warehouse` — `conftest.py` тянул `web.app` (v2). Решение: убрать.
- `PermissionError: [WinError 32]` — два `setup_test_db`. Решение: один (session scope).
- `test_pragma.py` работал с основной БД. Решение: `TEST_DB_PATH`.

**Что дальше (Ложка 6, часть 3):**
- **`tests/unit/test_parse_names.py`** — тесты парсера (пишет ID).
- **`tests/api/`** — тесты FastAPI (роутеры).
- **CI/CD** (`.github/workflows/test.yml`).

**Отложено:**
- **`tests/integration/`** — интеграционные тесты (реальный API).
- **`pipeline.py`** — после Ложки 8+.

## 📅 2026-11-08 — Конец сессии: pipeline, тесты, парсер

**Ветка:** `refactor/schema-audit`.

**Сделано:**
- `schema.sql` v3.1 (35 таблиц).
- `seed_reference_data.py` (16 справочников, 32 platforms, 22 editions).
- `fetch_products.py` (универсальный, 15 тестов).
- `fetch_postings.py` (универсальный, 23 теста).
- `parse_names.py` v3.2 (Вариант Б, создание новых изданий).
- `pipeline.py` (6 шагов, конфиг `pipeline_config.json`).
- `src/clients/base.py`, `src/clients/ozon.py`.
- Тесты: 80 (56 PASSED, 1 FAILED, 23 ERROR).

**Проблемы (на конец сессии):**
1. `fetch_postings` — 400 Bad Request (`/v4/posting/fbs/list`). Payload не тот.
2. Тесты: `First Year` уже в `seed` (FAILED). `PermissionError` каскадом (ERROR).

**Решения (следующая сессия):**
1. Убрать `First Year`, `New Year`, `GOTY` из `seed` (создаваться при разборе).
2. `try/finally` в тестах создания изданий.
3. `fetch_postings` — проверить документацию OZON (формат payload).

**Что дальше:**
1. Исправить тесты (80/80 PASSED).
2. Исправить `fetch_postings`.
3. Повторный запуск pipeline (6/6 шагов).
4. `web/app.py`, `web/routers/*`, шаблоны (TDD).
5. «Конструктор» (через веб).

**Отложено:**
- `merge_duplicates` (согласие владельца).
- `pipeline_config` — из БД (через меню «Настройки»).
- `.env.example` — обновлён (CLIENT_ID/API_KEY).

## 📅 2026-11-09 — Парсер v3.5: отказ от создания изданий

**Ветка:** `refactor/schema-audit`.

- **Источник истины** — `editionTypes` (seed). Парсер **только ищет** издания (точное нормализованное совпадение). Если не нашёл → `editionId = None`. Создание убрано.
- **Удалено:** `EDITION_MAP`, `BASE_EDITIONS`, `SINGLE_WORD_EDITION_MAP`, `_find_or_create_edition`.
- **Добавлено:** `normalize_edition(s)` — агрессивная нормализация (`lower`, убрать `' . - _`, схлопнуть пробелы). Например, `Collector's` = `collectors`, `K.O.` = `ko`.
- **`GOTY`** и **`Game of the Year`** — оба лежат в `editionTypes` (в данных встречаются оба написания).
- **`seed_editionTypes`** — заполнен максимально полно (46 изданий: базовые, составные, `GOTY`, `First Year`, `Survivor Steelbook`, одиночные в скобках типа `Platinum`).
- **API-тесты удалены** (старые v2). В будущем напишем с нуля.
- **Тесты:** переписаны под новую логику. Проверяют поиск (а не создание). 87/87 PASSED.

## 📌 Текущий этап (2026-11-09)

**Ветка:** `refactor/schema-audit`.
**Сайт:** **https://only-limited-magazin.ru** (работает, но на сервере пока **старый** v2).
**Сервер:** AdminVPS (79.133.183.30), Nginx + Uvicorn (systemd).

**Что готово:**
- `schema.sql` (35 таблиц).
- `seed_reference_data.py` (16 справочников, 46 изданий).
- `parse_names.py` v3.5 (пишет ID, не создаёт издания).
- `fetch_products.py` (универсальный, 15 тестов).
- `fetch_postings.py` (универсальный, 23 теста).
- **87/87 PASSED** (все юнит-тесты).

**Ближайшие задачи:**
1. `fetch_postings` — 400 Bad Request на `/v4/posting/fbs/list` (неверный payload). Проверить документацию OZON.
2. `web/app.py`, `web/routers/*`, шаблоны — переписать под v3.1 (TDD).
3. Проверить pipeline end-to-end (6 шагов) после v3.5.

## 2026-11-09 — Итог по парсеру v3.6 (80%) и начало API-тестов

**Текущий статус:** парсер разобран на 80%. Оставшиеся косяки требуют ручной правки или отложены на этап «Конструктора».

**Что починили в v3.6:**

- **Заглушки:** алгоритм удаления переписан. Теперь он удаляет товары с `name LIKE 'Товар %'` или `baseGameName LIKE 'Товар %'` **вместе с их позициями в заказах** (независимо от того, были ли продажи). Это очищает базу от мусора (удалили 413 заглушек).
- **Платформа Dreamcast:** добавлены `sega dreamcast`, `dreamcast`, `dc`, `sega saturn` в `PLATFORM_MAP`, чтобы парсер видел платформу.
- **Очистка от «Edition»:** если слово `Edition` не распознано как издание, оно удаляется из `baseGameName` в конце.
- **`Bundle`:** если в названии есть `bundle`, `trilogy` и т.д. — тип устанавливается в `bundle` (переопределяет `game`).
- **`Overkill Edition`:** теперь издание ищется по якорю `Edition`, даже если до него нет `Edition` в `seed` (сработала нормализация).

**Что НЕ исправлено (известные баги, 20%):**

1. **Огрызки от издателя в скобках.** `( Run Games)` вместо `(Limited Run Games)`.
   - *Причина:* при поиске издателя в скобках парсер не вырезает его из строки, а просто ставит `publisherId`.
   - *Решение:* нужно вырезать `bracket_text` целиком, если издатель найден.
2. **`Deluxe` не вырезается.** Пример: `Angry Video Game Nerd 1 & 2 Deluxe`.
   - *Причина:* слова `Deluxe` нет в `seed`, поэтому парсер не знает, что это издание.
   - *Решение:* добавить `Deluxe` в `seed_editionTypes`.
3. **`Stellar` не вырезается.** Пример: `Everspace 2: Stellar Steelbook Edition` → осталось `Everspace 2: Stellar`.
   - *Причина:* слова `Stellar` нет в `seed`. Аналогично `Deluxe`.

**Итог:** Парсер отрабатывает 80% данных корректно. Остальные 20% — это уникальные издания (вроде `Stellar`, `Journey`, `Crimson Knight`), которые пока не в `seed`. В «Настройках» можно будет добавить их вручную.

**Следующий шаг:** API-тесты (`tests/test_api.py`) и обновление Git (фиксация текущего состояния ветки).