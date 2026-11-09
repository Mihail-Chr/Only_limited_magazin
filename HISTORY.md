# История проекта

Журнал ключевых решений и прогресса. **Правило:** перед каждым потенциально «зависающим» шагом (долгий скрипт, миграция, сложный рефакторинг) — сначала обновить этот файл, потом действовать. Так при обрыве диалога контекст восстанавливается за 30 секунд.

**Как читать:** идём сверху вниз (от старых записей к новым). Последняя запись — текущий статус.

---

## 2026-10-22 — Старт проекта, документация
- Создан репозиторий `Only_limited_magazin`.
- Написаны документы: глоссарий, общие сведения, бизнес-процессы, модель данных (4 части).
- Созданы 9 ER-диаграмм (Mermaid).
- Зафиксированы ключевые решения:
  - Два независимых контура: закупка и продажа (через `stock`).
  - PostgreSQL как OLTP, DuckDB/ClickHouse для аналитики.
  - Минимизация ПД (только никнейм, город, возрастная группа).
  - `buyerNickname NOT NULL`, гостям — автогенерация.

## 2026-10-23 — SQL-схема для PostgreSQL
- Созданы файлы `sql/01`–`04` (34 таблицы).
- Заполнены справочники (`11_data_reference.sql`, `12_data_geo_game.sql`).
- Создана роль `operator` (кладовщик + продавец).
- Протестирован сквозной сценарий (`13_data_test.sql`).

## 2026-10-24 — Переход на Python + SQLite, первые данные
- Создан каркас Python-проекта (`src/`).
- Написан `src/schema.sql` — упрощённая схема для SQLite.
- Скрипты: `init_db.py`, `seed.py`, `import_xlsx.py`, `fetch_products.py`.
- Загружены товары из Excel: **1686 карточек**.
- Первый запрос к OZON API: **1705 товаров**.
- Добавлены скрипты `set_stock.py`, `report_stock.py`, `keeper_dashboard.py`.
- Созданы таблицы `stock_manual`, `posting`, `posting_item`.

## 2026-10-25 — Загрузка истории продаж, работа с себестоимостью
- Загружены цены и остатки из OZON API (`fetch_product_details.py`).
- Загружены отправления FBS за 2022–2026: **5804 заказа** (`fetch_postings.py`).
- Заполнена история себестоимости (`cost_price_at_sale`) — **6319 записей**.
- Компенсированы остатки (`fix_initial_stock.py`) — 1242 товара, 5460 единиц.
- **Итог:** физический остаток 5473, в пути 5464, доступно 9.
- Создан `.env.example`, `.gitignore`.
- **DBeaver:** проблема с отображением данных (кэш соединения). Решение — переподключиться или проверить через терминал.

## 2026-10-26 — MVP кладовщика, форма добавления
- Рефакторинг на роутеры (`keeper`, `api`, `seller`).
- Умные поля формы (скрытие лишних для аксессуаров).
- Чеклист подтверждения, логическая валидация (год версии не раньше релиза).
- Кнопки «+» для новых типов, изданий, издателей, платформ.
- Названия очищены от «Видеоигра».

## 2026-10-27 — Деплой на Timeweb, потом AdminVPS
- Успешный деплой на Timeweb Cloud (App Platform). Решили проблемы с портом 80 и `.env`.
- Пережили провал App Platform, атаку на FirstVDS.
- Переехали на AdminVPS (IP 79.133.183.30).
- Переписали `schema.sql`, создали `upgrade_db.py`.

## 2026-10-28 — Стабилизация интерфейса и схемы
- Исправили баг с `stock_manual`.
- Привели кнопки к единому стилю.
- Добавили проверку пустых справочников.
- **Уроки:** не деплоить пока не работает локально, всегда иметь актуальную `schema.sql`, тестировать negative testing.

## 2026-10-30 — Ветка под рефакторинг парсера, тест-кейсы
- Переход на TDD: сначала тест-кейс, потом код.
- Создана ветка `test/parser-target-behavior`.
- Переписан `parse_name`: словари из БД, `media_type`, edition по якорю, steelbook, платформы, хвост описания, заглушки.
- **Тесты:** 24/24 зелёных.

## 2026-10-31 — Парсер: steelbook premium, vengeance, xbox series x/s
- `EDITION_MAP` += `steelbook premium`, `vengeance`, `france exclusive`, `картонный бокс`.
- `PLATFORM_MAP`: `xbox series x` → `Xbox Series X` (и S).
- `extract_platforms`: `matched_keys` (чтобы `xbox series` не матчился внутри `xbox series x`).
- `export_duplicates_xlsx.py`: правила `BASE_NAME → PLATFORM → EDITION → REGION_ID → MEDIA_TYPE → PUBLISHER`. Попарно, `PRICE`/`PRICE_SOURCE`.
- **Тесты:** 27/27. Результат: 58 → 39 пар (ложные ушли).
- Влито в `main` (коммит `54247c8`), запушено на GitHub.

## 2026-11-01 — Product manager: план MVP, ручные продажи, миграция
- **Цель MVP:** запустить, вводить товары не на площадке, вести продажи.
- `merge_duplicates` отложен (нет согласия владельца).
- Ручная продажа — минимум: дата, товар, кол-во, цена. Через `posting`/`posting_item` (`source='manual'`).
- `posting` += `source`, `buyer_nickname`, `buyer_id`. Создан store `manual`.
- `buyer_id=1` («Физлицо»), таблицу `buyer` пока не создаем (сделаем при пересборке).
- Продажа без остатка запрещена (alert + переход к Кладовщику).
- Исправлен баг парсинга `Battletoads` (`Game Boy`).

## 2026-11-02 — UI: Ручная продажа, Меню Продавца, УТ, Копирование
- **Ручная продажа:** форма, история, списание остатков, `source='manual'`.
- **Меню Продавца:** поиск, фильтры (Платформа, Издание), сортировка, цена OZON (с fallback на последнюю продажу).
- **УТ (Управление товарами):** все фильтры вынесены наверх (Платформа, Издание, Регион, Издатель), инлайн-изменение остатка, кнопки «Редактировать»/«Скопировать».
- **Добавление/Редактирование/Копирование:** полностью переписан `add_product.html` (единый шаблон), исправлены ошибки с `platformVersion`, возврат в правильное меню.
- **Инвентаризация:** добавлен выпадающий фильтр по платформе.
- Стили приведены в порядок.
- **Отложено:** проверка дублей при вводе, `merge_duplicates.py`, `check_info_list_coverage.py`.

## 2026-11-02 (продолжение) — Стабилизация UI: Продавец, УТ, Копирование, Ручная продажа

**Что сделано:**
- **Ручная продажа (Продавец):** форма, история, списание остатков. Проверка: если остаток 0 — alert + переход к Кладовщику.
- **Экран Продавца:** поиск, фильтр по платформе (в заголовке колонки), сортировка, цена OZON (с fallback на последнюю продажу).
- **УТ (Управление товарами):** поиск, фильтры в заголовках (Платформа, Издание, Регион, Издатель), инлайн-остатки, кнопки «Ред.» / «Копия». Колонки: Цена учёта, Цена OZON, Остаток.
- **Добавление / Редактирование / Копирование:** единый шаблон `add_product.html` (режимы: add, edit, copy). Исправлены баги с `platformVersion`, сохранением и возвратом в нужное меню.
- **Инвентаризация:** добавлен фильтр по платформе.
- **Парсер:** 27/27 тестов. Добавлен `'gameboy'` в `PLATFORM_MAP` (баг Battletoads).

**Технические решения:**
- Все фильтры работают по принципу «AND» (поиск + селекты). Не сбрасывают друг друга.
- Сохранение формы унифицировано через `/keeper/save_product` с параметром `mode` (add/edit/copy).
- `add_product.html` теперь единый для всех действий (один поддерживаемый шаблон).

**Отложено:**
- `merge_duplicates` (склейка).
- Проверка дублей при вводе (поиск похожих карточек).

## 2026-11-02 (продолжение) — Начало рефакторинга v2: утверждение плана

**Решение:** Переходим к масштабному рефакторингу БД и кода.
**Причина:** Текущая схема не позволяет гибко вести учёт продаж (под заказы), не поддерживает картинки локально, не имеет полноценного `buyer` и автотестов.
**Стратегия:** «Всё как в бою». Старую базу не переносим. Создаём новую схему, заново загружаем данные из OZON.

**Утверждённый план (Шаги):**
1. Обновить `schema.sql` (новые поля и таблицы).
2. Обновить `seed_reference_data.py`.
3. Пересборка базы (pipeline0).
4. Обновить код (`parse_names.py`, `keeper.py`, `seller.py`).
5. Написать автотесты (pytest).
6. Сделать «шестерёнку» (инструмент дублей).

**Ключевые изменения схемы v2:**
- `posting` += `is_preorder` (товары под заказ), `platform_set` (JSON для дублей).
- Новая таблица `sync_log` (даты синхронизации).
- Новая таблица `buyer` (вместо колонки `buyer_id`).
- `platforms` += `is_portable` (для GB/GBA/NDS), `revision` (для Series X/S).
- `product` += `photo_filename` (локальные картинки).

**Зафиксированные решения:**
- Автоматическую склейку дублей НЕ делаем (< 1% дублей). Вместо этого — инструмент «шестерёнка» для ручной проверки.
- Портативные платформы не выносим в отдельную сущность (чтобы не ломать интерфейсы).
- Продажи синхронизируем в `posting`, остатки `stock_manual` не трогаем (физика отдельно от истории).
- Автотесты пишем после рефакторинга БД.

## 2026-11-03 — Успешный деплой на AdminVPS, домен и HTTPS

**Что сделано (полный путь):**
1. **Timeweb Cloud (App Platform):** Изначально приложение деплоилось туда. Домен `.ru` был привязан к Timeweb Cloud, сертификат выдавался автоматически (Let's Encrypt).
2. **Переезд на AdminVPS (IP 79.133.183.30):**
   - Остановлен старый `app.service` на сервере.
   - В `/var/www/only_limited` склонирован репозиторий из ветки `refactor/v2-schema`.
   - Создано виртуальное окружение `venv`, установлены зависимости из `requirements.txt`.
   - Скопирована база данных с локального компьютера на сервер.
   - Создан файл `.env` с ключами OZON.
3. **Настройка Nginx:**
   - Установлен `nginx`.
   - Настроен конфиг `/etc/nginx/sites-available/default` с `proxy_pass` на `127.0.0.1:8000`.
   - Удалены старые симлинки (`only-limited`, `only_limited`), оставлен только `default`.
4. **Настройка systemd:**
   - Создан `/etc/systemd/system/only_limited.service`.
   - Сервис запускает `uvicorn` из `/var/www/only_limited/venv/bin/uvicorn`.
   - Включен автозапуск (`systemctl enable only_limited`).
5. **SSL и домен:**
   - В Timeweb Cloud изменена A-запись для `only-limited-magazin.ru` на `79.133.183.30` (с помощью удаления старой и создания новой).
   - Установлен `certbot` и получен сертификат для `only-limited-magazin.ru` и `www`.
   - Сертификат обновлён (certbot расширил старый, добавив `www`).
6. **Обновление кода:**
   - Обнаружено, что сервер отстаёт на 1 коммит (не был залит `sync_ozon.html`).
   - Сделан `git pull` на сервере (после `git checkout` для сброса локальных изменений в базе).

**Итог:** Сайт доступен по `https://only-limited-magazin.ru`, работает на AdminVPS, HTTPS с зелёным замочком, все новые функции (синхронизация OZON, товары под заказ) на месте.

**Проблемы, которые решили:**
- `address already in use` (порт 8000 был занят старым процессом — убили через `pkill`).
- `ERR_CONNECTION_REFUSED` (Nginx не слушал 443 — certbot переписал конфиг, но пришлось исправлять).
- Кэш браузера (долго не обновлялся — помогло только полное закрытие и открытие в режиме инкогнито).
- Git: сервер отставал, потому что локально не был запушен файл `sync_ozon.html` (файл был в `Untracked`, но не добавлен в коммит).

**Технические решения:**
- Nginx как прокси перед Uvicorn.
- Systemd для автозапуска.
- Certbot для SSL.
- Домен `.ru` управляется через Timeweb Cloud (A-запись на IP AdminVPS).

## 2026-11-04 — Доработка поиска дублей (restore, строгое сравнение платформ)

**Что сделано:**
1. **Добавлено поле `restore` в таблицу `product`** (через `ALTER TABLE` и обновление `schema.sql`).
   - Парсер теперь распознаёт `(Лицензия)` и ставит `restore = 1`, удаляя слово из названия.
   - В будущем на OZON будем писать `Restore` (английская форма) — это мягче для покупателей.
2. **Исправлено сравнение платформ в поиске дублей.**
   - Раньше: `PS4/PS5` и `PS4` считались дублями (по вхождению).
   - Теперь: строгое сравнение строк. `PS4/PS5` и `PS4` — **не** дубли. `PS4/PS5` и `PS4/PS5` — дубли.
3. **Обновлён `export_duplicates_xlsx.py`:**
   - Добавлен учёт `restore` (товары с лицензией не склеиваются с обычными).
   - Добавлено строгое сравнение платформ.
   - Добавлена колонка `RESTORE` в выгрузку.
   - Проверка: 0 пар дублей (все товары уникальны по новым правилам).
4. **Обновлён `check_duplicates` в `keeper.py`:**
   - Добавлен учёт `restore` (поиск только среди товаров с таким же флагом).
   - Строгое сравнение платформ (через `WHERE p.platform = ?`).

**Тесты:**
- Копирование товара (100% совпадение) — дубли выскакивают.
- Изменение платформы (с `PS4/PS5` на `PS4`) — дубли не выскакивают.
- Excel-выгрузка — 0 пар дублей (товары уникальны).

**Решения:**
- `(Лицензия)` в названии = `restore = 1`. На OZON пишем `Restore`.
- `PS4/PS5` — отдельная сущность, не считается дублем `PS4` или `PS5`.
- Удаление товара: только если нет истории продаж (`posting_item` пуст). Иначе — `is_active = 0`.

## 2026-11-04 (продолжение) — Восстановление базы на сервере после git pull

**Проблема:** После `git pull` на сервере база данных оказалась пустой (0 байт), так как мы убрали её из Git, а при обновлении файл перезаписался пустой заглушкой.

**Решение:**
1. Скопировали рабочую базу с локального компьютера на сервер через `scp`.
2. Перезапустили сервис `only_limited`.
3. Сайт заработал, поиск дублей с учётом `restore` и строгим сравнением платформ работает.

**Урок:** База данных не должна быть в Git. При обновлении сервера нужно вручную копировать базу (или делать бэкап/восстановление).

## 2026-11-04 (продолжение) — База данных полностью удалена из Git

**Проблема:** Файл `db/only_limited.sqlite3` оставался в истории Git, и его можно было скачать по прямой ссылке на коммит, даже после `git rm --cached`.

**Решение:**
1. Сделали чистый клон репозитория в отдельную папку `clean_copy`.
2. Установили `git-filter-repo` (с проблемами на Windows, но решили через ручное копирование файла).
3. Выполнили `git filter-repo --path db/only_limited.sqlite3 --invert-paths` — удалили файл из **всей** истории.
4. Запушили переписанную историю на GitHub с флагом `--force`.
5. Синхронизировали основную папку с новой историей (через `git pull --rebase`).

**Итог:** Базы больше нет ни в текущей версии, ни в истории Git. Доступа к ней через GitHub нет.

**Урок:** Если файл нужно удалить навсегда — `git rm --cached` недостаточно. Нужен `git filter-repo` (или `git filter-branch`).

## 2026-11-04 (продолжение) — Склады (добавление, редактирование, отображение), Delete, сортировка

**Что сделано:**

1. **Склады:**
   - В таблицу `warehouse` добавлены два склада: `id=1` (Виталий) и `id=4` (Вениамин).
   - В `listing` добавлено поле `warehouse_id` (уже было), все листинги привязаны к `id=1`.
   - В **Инвентаризации** (Кладовщик) добавлена колонка «Склад» с выпадающим списком (можно менять склад прямо в таблице, изменения сохраняются через `/keeper/update_warehouse_inline`).
   - В **УТ** добавлена колонка «Склад» с выпадающим списком (аналогично).
   - В **Экране Продавца** добавлена колонка «Склад» (только для чтения).
   - В **Добавлении/Редактировании** товара добавлен выпадающий список «Склад» (обязательное поле).
   - В **Добавлении** товара добавлена кнопка «+» для создания нового склада (модальное окно, `add_warehouse`).
   - **Отложено:** редактирование названия склада (в разделе «Настройки»).

2. **Delete (удаление товара):**
   - В `keeper.py` добавлен эндпоинт `/keeper/delete_product/{product_id}`.
   - Удаление работает **только** если у товара нет продаж (`posting_item` пуст). Если есть — возвращает ошибку.
   - В УТ добавлена кнопка «Удалить» (рядом с «Ред.» и «Копия»).
   - При удалении удаляются записи из `listing`, `stock_manual` и `product`.

3. **Сортировка:**
   - В УТ добавлены стрелочки для сортировки по: Название, Платформа, Издание, Склад.
   - Сортировка работает как **приоритетная очередь** (последний клик — самый главный).
   - Третье нажатие снимает сортировку (возвращает исходный порядок).
   - В Экране Продавца добавлены стрелочки для сортировки по: Наименование, Платформа (с той же логикой).

**Технические решения:**
- `update_warehouse_inline` — обновляет `warehouse_id` в `listing` для `store_id=1`.
- `add_warehouse` — создаёт новый склад в `warehouse` (code генерируется автоматически: `wh_<timestamp>`).
- `delete_product` — проверяет наличие продаж, удаляет из `listing`, `stock_manual`, `product`.
- Сортировка — сохраняет исходный порядок строк (`originalOrder`) и восстанавливает его при пустом стеке.

## 2026-11-04 (продолжение) — Заполнение складов через pipeline (а не костыль)

**Проблема:** Склады `Виталий` (id=1) и `Вениамин` (id=4) были добавлены вручную через SQL-команды. Это неправильно — при пересборке базы (pipeline0) они потеряются.

**Решение:** Добавить в `seed_reference_data.py` (или в отдельный скрипт `seed_warehouses.py`) заполнение складов:
- `warehouse1` → `Виталий` (id=1)
- `warehouse2` → `Вениамин` (id=2)

**Также:** Убрать из `add_stores.py` или `init_db.py` ручное создание склада «Основной склад» (если оно есть), чтобы не было дублей.

**Статус:** Запланировано. Сделать при следующей пересборке базы (pipeline0).

## 2026-11-05 — Меню «Настройки»: загрузка данных, редактирование справочников, резервная копия

**Что сделано:**

1. **Меню «Настройки»** (`/settings`):
   - **Загрузка данных:** универсальное меню (Площадка → Магазин → Действие). Действия: «Загрузить карточки», «Загрузить движение товаров». Результат — в модальном окне.
   - **Редактирование справочников:** склады, платформы, издания, издатели, регионы — выпадающий список + кнопка «Редактировать» + модальное окно.
   - **Резервная копия:** кнопки «Загрузить» (скачать базу) и «Восстановить» (загрузить базу из файла).
   
2. **Поле `platform` в таблице `store`** (добавлено через `ALTER TABLE`, в `schema.sql` тоже есть). Привязка: `store.platform = 'ozon'` для всех магазинов.

3. **Загрузка данных через интерфейс** — работает через `subprocess.run` с `cwd` = корень проекта и `env["PYTHONPATH"]` = корень проекта.

**Проблемы, которые решили:**
- `ModuleNotFoundError: No module named 'src'` — добавили `env["PYTHONPATH"]`.
- `can't open file ...` — исправили путь к скрипту (через `Path(__file__).resolve().parent.parent.parent`).
- Модальные окна не закрывались — добавили `addEventListener` на кнопку «ОК» и `closeModalOnly`/`closeModalAndSave`.
- Редактирование платформ дублировало версию — сделали отдельную функцию `editPlatform` с двумя полями (название и версия).
- `alert` заменён на модальные окна в стиле приложения.

**Технические решения:**
- `settings.py` — роутер `/settings` с эндпоинтами: `/`, `/stores_by_platform`, `/run_action`, `/update_item`, `/update_warehouse`, `/load_status`, `/load_products`.
- `settings_menu.html` — универсальные модальные окна, редактирование через `addEventListener`, два блока рядом (Загрузка данных + Резервная копия).
- `schema.sql` — добавлено поле `platform` в `store`.

**Отложено:**
- Редактирование названий складов (частично сделано, но нужно доделать).
- Перенос выгрузки/загрузки базы из меню Кладовщика в Настройки.
- Удаление кнопки «Синхронизация OZON» из меню Продавца.

## 2026-11-05 (продолжение) — Back Review: аудит архитектуры (строки vs ID)

**Решение:** остановиться и провести ревизию архитектуры БД, чтобы убрать костыли (строки вместо ID).

**Проблема:** в `product` поля `platform`, `edition`, `publisher`, `product_type`, `media_type`, `genre`, `language`, `developer`, `age_rating`, `country_of_origin` — строки (TEXT), а не ID (ссылки на справочники). Из-за этого:
- Изменение названия в справочнике не отражается на товарах.
- Фильтры в Инвентаризации и УТ не видят новых значений.
- Парсер пишет строки, а не ID.

**План ревизии:**
1. Аудит схемы (`scratch/audit_schema.py`) — все таблицы и поля.
2. Аудит кода — где используются строки вместо ID (keeper.py, seller.py, parse_names.py, settings.py, шаблоны).
3. Решение: Вариант А (правильный, добавить ID-поля) или Вариант Б (быстрый фикс, каскадное обновление строк).
4. Если Вариант А — создать недостающие справочники (mediaTypes, ageRatings, developers, statuses, substatuses), добавить ID-поля, миграция, переписать парсер/фильтры/формы/синхронизацию/редактирование.

**Текущий статус:** на сервере обновлённая версия (меню «Настройки» работает), но архитектурная проблема со строками осталась.

**Отложено:**
- Back Review (аудит и миграция) — начать с `scratch/audit_schema.py`.
- Перенос выгрузки/загрузки базы из меню Кладовщика в Настройки.
- Удаление «Синхронизация OZON» из меню Продавца.
- Поиск у Покупателя (внешние сайты, avg_market_price, Telegram).

## 2026-11-05 (продолжение) — Back Review: аудит показал костыли

**Аудит (`scratch/audit_schema.py`):**

**`product` (2011 записей):**
- `platform` — 21 уникальных, 1965 записей → **строка**, надо `platformId`
- `edition` — 30 уникальных, 341 запись → **строка**, надо `editionId`
- `publisher` — 8 уникальных, 358 записей → **строка**, надо `publisherId`
- `product_type` — 3 уникальных, 2011 записей → **строка**, надо `typeGoodId`
- `media_type` — 2 уникальных, 6 записей → **строка**, надо `mediaTypeId`
- `genre`, `language`, `developer`, `age_rating`, `country_of_origin` — **0 записей** (не используются, можно отложить)

**`posting`:**
- `status` — 4 уникальных, 190 записей → **строка**, надо `statusId`
- `substatus` — 0 записей (не используется)

**`posting_item`:**
- `currency` — 1 уникальное, 216 записей → **строка**, надо `currencyId` (можно отложить)

**`warehouse`:**
- `default_currency` — 1 уникальное, 2 записи → **строка**, надо `currencyId` (можно отложить)

**`listing`:**
- `status` — 1 уникальное, 2212 записей → **строка**, надо `statusId` (можно отложить)

**Решение:** Вариант А (правильный, добавить ID-поля). Приоритет — `product` (5 полей) и `posting.status`.

**План:**
1. Создать недостающие справочники (`mediaTypes`, `ageRatings`, `developers`, `statuses`).
2. Добавить ID-поля в `product`.
3. Миграция (заполнить ID из строк).
4. Удалить строковые поля (или оставить как денормализацию).
5. Переписать парсер, фильтры, формы, синхронизацию, редактирование.

**Текущий статус:** аудит завершён, план готов, миграция не начата.

**Отложено:**
- Миграция на ID-поля (Вариант А) — следующий шаг.
- Перенос выгрузки/загрузки базы из меню Кладовщика в Настройки.
- Удаление «Синхронизация OZON» из меню Продавца.
- Поиск у Покупателя (внешние сайты, avg_market_price, Telegram).

## 2026-11-05 — Аудит архитектуры: принципы рефакторинга (Ложка 1)

**Контекст:** аудит схемы показал костыли (строки вместо ID). Принято решение: полный рефакторинг под «конструктор» (саморазворачивающееся приложение для одного предприятия).

**Договорённости (принципы):**

1. **Стиль именования:** `camelCase` для всех полей (`platformId`, `createdAt`, `isEnabled`).
2. **Нормализация:** Вариант А — только ID, без строк. `product.platform` (строка) удаляется → `product.platformId`. То же для `edition`, `publisher`, `product_type`, `media_type`. `posting.status` (строка) удаляется → `posting.statusId`. При чтении — `JOIN`.
3. **`platforms`:** `platformVersion` не переименовываем. `revision`, `is_portable` — оставляем (аналитика).
4. **`modules` — отдельная таблица:** `moduleName TEXT PK`, `isEnabled`, `sortOrder`, `description`, `versionAdded` (опц.). Не путать с `isActive` в справочниках. Проверка флага — декоратор `@require_module(name)`.
5. **Модули на старте:** `purchase` (0), `sale` (1), `inventory` (1), `ozon_sync` (1), `manual_sale` (1), `monitoring` (0).
6. **Площадки — три таблицы:** `purchasePlatforms` (покупка), `marketplaces` (продажа), `store` (наш магазин на площадке). `store.platform` (TEXT) → `store.marketplaceId` (FK).
7. **Avito:** и `purchasePlatform`, и `marketplace`. `hasApi = 1` (при подключённом тарифе — операционное, не структурное).
8. **`manual`:** отдельный маркетплейс (`code='manual'`, `name='Ручная продажа (Others)'`, `commission=0`, `hasApi=0`).
9. **`avgSellCost`:** поля в `product`: `avgSellCost` (RUB), `avgSellCostUpdatedAt`, `avgSellCostSamples`, `avgSellCostBreakdown` (JSON, для отладки, не для UI). Формула: `AVG(AVG(площадки) × курс → RUB)`. История — отложить.
10. **Тесты:** `audit_schema.py` → pytest (`tests/test_schema.py`). CI/CD — GitHub Actions. Репозиторий публичный.
11. **Pipeline:** физический `pipeline.py` — после первой итерации рефакторинга.
12. **`scratch/`:** правило — временное в `scratch/`, нужное в `src/scripts/` или `tests/`. Судьба 15 файлов определена (см. таблицу в CONTEXT.md).
13. **Ветка:** `refactor/schema-audit` (от `refactor/v2-schema`). Все изменения — в ней.
14. **Данные из старой БД — не переносим.** Чистый лист: OZON + parse.
15. **Порядок:** «слон ложками». Обсуждение → код → проверка. Не перескакиваем.

**Что дальше:** Ложка 2 — аудит `schema.sql` (список правок без кода). Ложка 3 — новая `schema.sql`. Ложка 4 — миграция. Ложка 5 — pipeline. Ложка 6 — тесты. Ложка 7 — CI/CD. Ложка 8+ — переписывание кода по модулям.

## 2026-11-07 — Часть 4: склад, действия, возвраты (утверждено)

**Контекст:** разобрали сценарий покупки (5 этапов: заказ → склад агрегатора → таможня экспорт → таможня импорт → получение). Выявлены «беды» на каждом этапе. Решили разделить справочник причин и действия.

**Решения:**

1. **`stock`** — переделать: `warehouseId`, `productId`, `quantity`, `countOfRepair`, `createdAt`, `updatedAt`. Без `avgCost*`.
2. **`stock_manual`** — удалить. Ручной ввод — через `product.offerId = NULL`.
3. **`stock_history`** — оставить (аудит): `quantityDelta`, `reasonId`, `sourceType`, `sourceId`, `createdAt`.
4. **`returnReasons`** — добавить (справочник причин): `reasonId`, `code`, `name`, `context` (`'purchase'`/`'sale'`/`'both'`), `sortOrder`, `isActive`. **Без `action`** (логика — в коде).
5. **`stockWriteOffs`** — переделать: `productId`, `warehouseId`, `quantity`, `reasonId`, `sourceType`, `sourceId`, `writeOffDate`, `notes`, `createdAt`, `updatedAt`.
6. **`salesReturns`** — переделать: `salesOrderId`, `productId`, `warehouseId` (NOT NULL), `quantity`, `reasonId`, `returnDate`, `refundAmount`, `notes`, `createdAt`, `updatedAt`.
7. **`purchaseReturns`** — добавить: `purchaseOrderId`, `productId`, `warehouseId` (nullable), `quantity`, `reasonId`, `returnDate`, `refundAmount`, `notes`, `createdAt`, `updatedAt`.
8. **`price_history`** — отложить.
9. **`market_offers`** — удалить.
10. **`customs`** — развести термины: `customsDuty` (пошлина), `customsClearance` (очистка), `customsOffice` (орган). Статус `customs` — оставить (короткое имя).

**Сценарий покупки (5 этапов):**
1. Заказ на сайте → беда: отказ продавца.
2. Склад агрегатора (Shopogolic, Pochtoy) → беда: пересортица, некомплект.
3. Таможня экспорт → беда: возврат отправителю (3 варианта: повтор, возврат, потеря).
4. Таможня импорт (РФ) → беда: отказ (последствия: доставка возврата, повтор).
5. Получение → беда: качество, некомплект заказа, некомплект товара.

**Причины (`returnReasons`):**
- Покупка: `seller_refusal`, `wrong_item`, `incomplete_order`, `incomplete_item`, `customs_rejected`, `customs_refusal`, `lost_in_transit`, `returned_to_buyer`, `defect_on_receipt`.
- Продажа: `customer_refusal`, `damaged`, `wrong_item`, `not_as_described`, `lost_in_delivery`, `lost_in_return`.

## 2026-11-07 — Часть 4: склад, действия, возвраты (утверждено, финал)

**Решения (финал):**

1. `stock` — `warehouseId`, `productId`, `quantity`, `countOfRepair`, `createdAt`, `updatedAt`.
2. `stock_manual` — **удалить**. Ручной ввод — `product.offerId = NULL`.
3. `stock_history` — `quantityDelta`, `reasonId`, `sourceType`, `sourceId`, `createdAt`. Активна (заполняется).
4. `returnReasons` — `reasonId`, `code`, `name`, `context` (`'purchase'`/`'sale'`/`'both'`), `sortOrder`, `isActive`. **Без `action`** (логика — в коде). `wrong_item` — две записи (`wrong_item_purchase`, `wrong_item_sale`).
5. `stockWriteOffs` — `productId`, `warehouseId`, `quantity`, `reasonId`, `sourceType`, `sourceId`, `writeOffDate`, `notes`, `createdAt`, `updatedAt`. **Структура есть, логика — позже.**
6. `salesReturns` — `salesOrderId`, `productId`, `warehouseId` (NOT NULL), `quantity`, `reasonId`, `returnDate`, `refundAmount`, `notes`, `createdAt`, `updatedAt`. **Структура есть, логика — позже.**
7. `purchaseReturns` — `purchaseOrderId`, `productId`, `warehouseId` (nullable), `quantity`, `reasonId`, `returnDate`, `refundAmount`, `notes`, `createdAt`, `updatedAt`. **Структура есть, логика — позже.**
8. `price_history` — **отложить** (не создавать).
9. `market_offers` — **удалить** (не создавать).
10. `customs` — развести: `customsDuty` (пошлина), `customsClearance` (очистка), `customsOffice` (орган). Статус `customs` — оставить.

**Обработка возвратов (MVP):** **не делаем.** Структура готова, логика — после MVP. Влияние на MVP незначительное.

**Сценарий покупки (5 этапов):** см. `HISTORY.md` (2026-11-07).

**Следующая ложка:** Часть 5 — транзакции (`posting`, `posting_item`, `buyer`, `sync_log`, `payouts`, `payoutAdjustments`).

## 2026-11-07 — Часть 5: транзакции (утверждено). Аудит схемы завершён.

**Решения:**

1. `buyers` — `buyerId`, `buyerNickname`, `buyerCity`, `ageGroupId` (FK → `ageGroups`), `createdAt`, `updatedAt`, `isActive`.
2. `salesOrders` — `salesOrderId`, `buyerId`, `marketplaceId`, `marketplaceOrderId`, `currencyId`, `payoutId`, `notes`, `createdAt`, `updatedAt`. Без `orderDate`.
3. `salesOrderItems` — `salesOrderItemId`, `salesOrderId`, `productId`, `quantity`, `salePrice`, `warehouseId`, `notes`, `createdAt`. Без `costAtSale`, `updatedAt`.
4. `salesOrderStatusHistory` — `historyId`, `salesOrderId`, `statusId`, `statusDate`, `comment`. Без `createdAt`.
5. `payouts` — `payoutId`, `marketplaceId`, `periodStart`, `periodEnd`, `paidAt`, `totalAmount`, `reportNumber`, `notes`, `createdAt`, `updatedAt`.
6. `payoutAdjustments` — `adjustmentId`, `payoutId`, `salesOrderId`, `adjustmentTypeId` (FK → `adjustmentTypes`), `amount`, `notes`, `createdAt`.
7. `sync_log` — `id`, `syncType`, `dateFrom`, `dateTo`, `recordsCount`, `syncedAt`.
8. `posting` / `posting_item` — **удалить**.
9. `purchaseOrders` / `shipments` / `shipmentLosses` — **отложить**.
10. Таблицы — **мн.ч.** (`products`, `buyers`, `salesOrders`, ...). Поля — ед.ч. (`productId`, `buyerId`).

**Добавлено в Часть 1:**
- `ageGroups` — возрастные группы (5 строк, по умолчанию `25-34`).
- `adjustmentTypes` — типы корректировок (7 строк).

**Аудит схемы завершён.** Все 5 частей утверждены. Следующая ложка — Ложка 3: новая `schema.sql` + обновление `04`/`041`/`042`/`043`.

## 2026-11-07 — Принцип: однозначность справочников

**Решение:** все справочники, у которых есть `code` (ISO / короткий код) и `name` (полное название), **всегда выводятся в UI парой**: `code` + `name`. Например: «USD — Доллар США», «EU — Европа».

**Причина:** уважение к пользователю. Короткий код (`USD`) — для машин, полное название (`Доллар США`) — для людей. Одно без другого — неоднозначно.

**Структурные ограничения:**
- `UNIQUE` на `code` (ISO / короткий код) — обязательно.
- `UNIQUE` на `name` (полное название) — обязательно (для справочников, где название — идентификатор).
- Композитный `UNIQUE (code, name)` — **не нужен** (избыточен, если `code` и `name` уже уникальны).

**Справочники, к которым применяется:**
- `currencies` — `currencyCode` + `currencyName`.
- `regions` — `regionCode` + `regionName`.
- `marketplaces` — `code` + `name`.
- `purchasePlatforms` — `code` + `name`.
- `stores` — `code` + `name`.
- `warehouses` — `code` + `name`.
- `platforms` — `platformName` + `platformVersion` (композитный `UNIQUE`).
- `typeGoods` — `typeGoodName` (без `code`).
- `editionTypes` — `editionName` (без `code`).
- `publishers` — `publisherName` (без `code`).
- `mediaTypes` — `mediaTypeName` (без `code`).
- `ageGroups` — `ageGroupName` (без `code`).
- `adjustmentTypes` — `code` + `name`.
- `statuses` — `statusName` + `statusType` (композитный `UNIQUE`).
- `returnReasons` — `code` + `name`.

**Правило для UI:** везде, где выводится справочник, — выводить `code` + `name` (или `ISO` + `name`). Никогда только `code` или только `name`.

**Правило для seed:** в `seed_reference_data.py` — **всегда** полное название («Доллар США», «Канадский доллар», «Европа (расширенная)»). Не «Доллар», не «Европа».

## 2026-11-07 — Pipeline отложен

**Решение:** физический `pipeline.py` — **отложить** до момента, когда приложение с новой БД (v3.1) «встанет на ноги». Причина: скрипты (`fetch_products`, `fetch_postings`, `parse_names`) — старые (v2), их надо переписать (Ложка 8+). Тогда pipeline обретёт смысл.

**Когда вернёмся:** после Ложки 8+.

## 2026-11-08 — Тесты: инфраструктура, TDD, первые тесты (Ложка 6, часть 1)

**Контекст:** схема v3.1 готова (35 таблиц), справочники заполнены. Переходим к тестам. Подход — **TDD** («тесты сначала, код потом»). Цель — «обложить всё тестами» (разумно) + CI/CD.

**Принципы (зафиксированы):**

1. **Тестовые данные (fixtures) — must have.** Тесты **не зависят** от реальной БД (которая меняется). Fixtures создают **детерминированную** тестовую БД.
2. **Два типа тестов:**
   - **Юнит-тесты** (`tests/unit/`) — быстрые, без API, с моками. Запускаются **всегда** (CI/CD).
   - **Интеграционные** (`tests/integration/`) — медленные, с реальным API (`.env`). Запускаются **вручную** (`@pytest.mark.integration`).
   - **API-тесты** (`tests/api/`) — тесты FastAPI (роутеры). Позже.
3. **Моки** — только для **внешних** API (OZON), чтобы тесты были быстрыми и не зависели от сети.
4. **Реальный API** (`.env`) — для **интеграционных** тестов (медленные, вручную).

**Структура тестов:**

```
tests/
├── conftest.py              ← общие фикстуры (db_conn)
├── unit/
│   ├── conftest.py          ← setup_test_db (session scope, создаёт БД)
│   ├── test_db.py           ← тесты src/db.py
│   ├── test_pragma.py       ← тесты PRAGMA foreign_keys
│   └── test_seed.py         ← тесты seed_reference_data.py (планируется)
├── integration/             ← (пока пусто)
└── api/                     ← (пока пусто)
```

**`pytest.ini`** (маркеры):

```ini
[pytest]
markers =
    unit: юнит-тесты (быстрые, без API)
    integration: интеграционные (медленные, с API)
    api: тесты FastAPI (роутеры)
testpaths = tests
```

**`run_test.bat`** — запуск тестов в venv (отдельно от `run.bat` для разработки).

**`run.bat`** — для локального запуска (разработка): `init_db`, `seed`, `uvicorn`.
**`run_test.bat`** — для тестов: `pytest`.

**Что сделано:**

1. **`tests/conftest.py`** — `db_conn` (function scope). Соединение с тестовой БД.
2. **`tests/unit/conftest.py`** — `setup_test_db` (session scope). Создаёт тестовую БД из `schema.sql`, наполняет справочниками (через `seed_reference_data`).
3. **`tests/unit/test_db.py`** — 4 теста:
   - `test_get_conn_returns_connection` — `get_conn()` возвращает соединение.
   - `test_get_conn_enables_foreign_keys` — `PRAGMA foreign_keys = ON`.
   - `test_get_conn_row_factory` — `row_factory = sqlite3.Row`.
   - `test_init_db_creates_tables` — все 34 таблицы созданы.
4. **`tests/unit/test_pragma.py`** — 3 теста:
   - `test_foreign_keys_pragma_enabled` — `PRAGMA` = 1.
   - `test_foreign_key_constraint_works` — FK-констрейнт (`IntegrityError`).
   - `test_cascade_delete_works` — CASCADE.
5. **`pytest.ini`** — маркеры + `testpaths`.
6. **`run_test.bat`** — запуск тестов в venv.

**Результат:** **7/7 PASSED** (`test_db.py` — 4, `test_pragma.py` — 3).

**Проблемы, которые решили:**

- `ModuleNotFoundError: No module named 'fastapi'` — `pytest` запускался в **другом** окружении (`python 312 test for text`). Решение: `run_test.bat` (всегда активирует `venv` проекта).
- `sqlite3.OperationalError: no such table: warehouse` — `conftest.py` тянул `web.app` (старый, v2). Решение: **убрать** `web.app` из `conftest.py` (для unit-тестов не нужен).
- `PermissionError: [WinError 32]` — **два** `setup_test_db` (в `tests/conftest.py` и `tests/unit/test_db.py`) **конфликтовали**. Решение: **один** `setup_test_db` (в `tests/unit/conftest.py`, session scope), `db_conn` — в `tests/conftest.py` (function scope).
- `test_pragma.py` работал с **основной** БД (`db/only_limited.sqlite3`), а не с тестовой. Решение: использовать `TEST_DB_PATH`.

**Уроки:**

- **Один** `setup_test_db` (session scope) — иначе конфликт файлов.
- **`conftest.py`** не должен тянуть **весь** `web.app` (старый v2). Для unit-тестов — только БД.
- **`run_test.bat`** — гарантия, что `pytest` запускается в **правильном** venv (не зависит от PowerShell).
- **TDD** — тесты **до** кода. «Подзатыльник коду»: тест **описывает** желаемое поведение, код **подгоняется**.
- **Моки** — только для **внешних** API. Для `db.py` / `seed` — **не нужны** (нет API).

**Что дальше (Ложка 6, часть 2):**

- **`tests/unit/test_seed.py`** — тесты для `seed_reference_data.py` (16 справочников).
- **`tests/unit/test_parse_names.py`** — тесты парсера (пишет ID, а не строки).
- **`tests/api/`** — тесты FastAPI (роутеры: keeper, seller, settings).
- **CI/CD** (`.github/workflows/test.yml`) — запуск `pytest` на push.

**Отложено:**

- **`tests/integration/`** — интеграционные тесты (реальный API OZON).
- **`pipeline.py`** — физический pipeline (после Ложки 8+).
- **`test_pragma.py`** — изоляция (использовать `TEST_DB_PATH`, уже сделано).

## 2026-11-08 — Тесты: `test_seed.py` (Ложка 6, часть 2)

**Сделано:**

**`tests/unit/test_seed.py`** — 16 тестов (все справочники):

1. `test_modules_seeded` — 6 модулей, `isEnabled` (sale=1, purchase=0).
2. `test_currencies_seeded` — 5 валют, RUB id=1.
3. `test_regions_seeded` — 9 регионов, с `regionName`.
4. `test_platforms_seeded` — 30+, `PlayStation 4/5`, `isPortable`.
5. `test_typeGoods_seeded` — 12 типов.
6. `test_editionTypes_seeded` — 19 изданий.
7. `test_publishers_seeded` — 29 издателей.
8. `test_statuses_seeded` — 10 статусов (5 продажа + 5 закупка).
9. `test_mediaTypes_seeded` — 6 типов.
10. `test_ageGroups_seeded` — 5 групп, `25-34` id=2.
11. `test_adjustmentTypes_seeded` — 7 типов.
12. `test_warehouses_seeded` — 2 склада (Виталий id=1, Вениамин id=2).
13. `test_marketplaces_seeded` — 5 площадок.
14. `test_purchasePlatforms_seeded` — 10 площадок.
15. `test_stores_seeded` — 3 магазина.
16. `test_buyers_seeded` — 1 покупатель (Физлицо id=1).

**Обновлён `tests/unit/conftest.py`:** вызывает `seed_reference_data` (все `seed_*` функции), а не дублирует вставки.

**Результат:** **23/23 PASSED** (`test_db.py` — 4, `test_pragma.py` — 3, `test_seed.py` — 16).

**Урок:** тесты для `seed` — **простые** (проверка количества + ключевых записей). Не надо проверять **все** поля (только критичные).

## 2026-11-08 — Тесты: справочники, `conn`, «мусор»

**Справочники в тестах:**
- **Тестовая** БД (`db/test_only_limited.sqlite3`) — **создаётся** из `schema.sql`, **наполняется** через `seed_reference_data` (те **же** справочники, что и продакшн).
- **Обновляется** при **каждом** запуске тестов (session scope).
- **Не** «свои» — **те же**, что в продакшн.

**`parse_name(name, conn)`:**
- **Принимает** `conn` (соединение с БД).
- **Читает** справочники **из** `conn`.
- **Тест** передаёт **тестовую** БД. **Продакшн** — **продакшн** БД.
- **Не** глобальные переменные (проще, гибче).

**Тесты `test_parse_names.py` (10 + «мусор»):**
1. `platformId` (PS4)
2. `platformId` (PS4/PS5)
3. `editionId` (Deluxe)
4. `publisherId` (Sony)
5. `typeGoodId` (game)
6. `mediaTypeId` (physical)
7. `regionId` (US)
8. `baseGameName`
9. `restore` (Лицензия)
10. `Ultra`/`Unreal` (не удалять)

**«Мусор» (2-3 теста):**
- `"ку-ку товарищ (майор), кто здесь?"` — не падает.
- `""` (пустая строка) — не падает.
- `"(PS4)"` (только скобки) — не падает.

**Принцип:** тест **читает** ID из БД (`SELECT ...`), **сравнивает** с `parse_name`. **Не** хардкодит ID (надёжнее).

**Тест на «мусор»:** проверяет **устойчивость** (не падает), **не** точность.
## 2026-11-08 — `parse_names.py` v3.1 (Ложка 8+, часть 1)

**Сделано:**

**`src/scripts/parse_names.py`** — переписан под v3.1.

**Что изменилось:**
- `parse_name(name, conn=None)` — принимает `conn`, читает справочники **из него**.
- Возвращает **ID** (`platformId`, `editionId`, `publisherId`, `typeGoodId`, `mediaTypeId`, `regionId`), а не строки.
- `baseGameName` — очищенное название.
- `load_dictionaries(conn)` — загружает справочники из БД (в словари `строка → ID`).
- `main()` — обновляет `products` (`typeGoodId`, `baseGameName`, `platformId`, `editionId`, `publisherId`, `regionId`, `mediaTypeId`, `restore`).

**Исправлены баги (v2):**
- `Sony` — **вырезается** из `baseGameName` (было: оставался).
- `(Physical)` — **распознаётся** как `mediaTypeId` (было: `base_name = "God of War ()"`).
- `PS4/PS5` — **одна** платформа (`PlayStation 4/5`), а не две.
- `Steelbook` — **тип** (в начале названия), **издание** (в скобках или с `Edition`).
- `stub` — **убрано** (не обрабатываем).

**Тесты:**

**`tests/unit/test_parse_names.py`** — 13 тестов:
- **10 позитивных:** `platformId` (PS4), `platformId` (PS4/PS5), `editionId` (Deluxe), `publisherId` (Sony), `typeGoodId` (game), `mediaTypeId` (physical), `regionId` (US), `baseGameName`, `restore` (Лицензия), `Unreal` (не удалять).
- **3 негативных:** «мусор» (`"ку-ку товарищ (майор), кто здесь?"`), пустая строка, только скобки (`"(PS4)"`).

**TDD:** сначала **тесты** (13), потом **код** (подгонка). **13/13 PASSED**.

**Уроки:**
- TDD **работает**: тесты **описывают** желаемое, код **подгоняется**.
- **Негативные тесты** — **важны** (устойчивость к «мусору»).
- **Справочники** — из БД (через `conn`), **не** глобальные (гибкость для тестов).
- **Чтение ID из БД** (`SELECT ...`) — **надёжнее**, чем хардкод (`4`).

**Что дальше (Ложка 8+, часть 2):**
- **`fetch_products.py`** — переписать под v3.1 (TDD: `test_fetch_products.py`).
- **`fetch_postings.py`** — переписать под v3.1 (TDD: `test_fetch_postings.py`).
- **`web/app.py`** — переписать под v3.1 (TDD: `test_api.py`).
- **`web/routers/keeper.py`**, **`seller.py`**, **`settings.py`** — переписать под v3.1.
- **Шаблоны** — обновить.

## 2026-11-08 — Структура `tests/unit/` (уточнение)

**Вопрос:** «Избыточно ли дробить `tests/unit/` на подкаталоги (`db/`, `parse/`, ...)?»

**Ответ:** **Пока** — **нет**. **Плоско** (`tests/unit/test_*.py`):
- `test_db.py`
- `test_pragma.py`
- `test_seed.py`
- `test_parse_names.py`
- `test_fetch_products.py` (скоро)

**6 файлов** — **мало**. **Плоско** — **читаемо**.

**Когда дробить:** **больше 15-20** файлов. **Тогда** — `unit/db/`, `unit/parse/`, ...

**Сейчас** — **рано**.
## 2026-11-08 — `fetch_products.py`: тесты (TDD, 15/15 упали)

**Сделано:**

**`tests/unit/test_fetch_products.py`** — 15 тестов:
- **5 позитивных:** создание `products`, `listings`, обновление `name`, сохранение `rawJson`, возврат `counts`.
- **10 негативных:** магазин не найден, `hasApi=0`, нет `.env`, «мусор» в `.env`, ошибка API (500), пустой ответ, «мусор» в `offerId`, «сломанный» JSON, `hasApi=1` + нет `.env`, `hasApi=0` + есть `.env`.

**`src/clients/base.py`** — `BaseClient` (абстрактный):
- `get_products()` — список товаров.
- `get_product_info(offer_ids)` — названия.

**`src/clients/ozon.py`** — `OzonClient` (наследует `BaseClient`):
- `get_products()` — `/v3/product/list` (все страницы, проверка `total`).
- `get_product_info(offer_ids)` — `/v3/product/info/list` (батчами по 1000).
- `_post(path, payload)` — POST-запрос (обработка 401, 500, невалидный JSON).

**Результат:** **15/15 FAILED** (`ImportError: cannot import name 'fetch_products'`). **Это нормально** (TDD). Старый `fetch_products.py` — **скрипт** (не функция). **Тесты** **ждут** функцию.

**Проблема:** `fetch_products.py` — **не** имеет функции `fetch_products` (там `main()`). **Тесты** **ждут** `from src.scripts.fetch_products import fetch_products`. **ImportError.**

**Что дальше:** переписать `fetch_products.py` — **функция** `fetch_products(platform, store_code, client=None)`. **Подгонка** под тесты.

**Урок:** TDD **работает**. **15 тестов** — **карта**. **Потом** — код.

## 2026-11-08 — Изоляция тестов (исправление)

**Проблема:** `setup_test_db` — **session scope** (БД **создаётся** **один раз**). Тесты **не** чистят **за собой**. `TEST-001` — **висит** **между** тестами. `test_fetch_products_creates_listings` **падает** (`inserted = 0`).

**Это** — **неряшливость**. «Сделал дело — убери за собой».

**Решение:** `setup_test_db` — **function scope** (БД **создаётся** **перед** **каждым** тестом). **После** — **удаляется**.

**Цена:** **медленнее** (30 тестов × 0.1 сек = 3 сек). **Не** критично.

**Плюс:** **изоляция** (каждый тест — **чистая** БД).

**Урок:** **session scope** — **быстро**, но **не** изолированно. **function scope** — **правильно**.

## 2026-11-08 — Баги: соединение не закрыто, `updated` не считает

**Проблема 1: `PermissionError` (соединение не закрыто)**

**Симптом:** `PermissionError: [WinError 32] ... 'db/test_only_limited.sqlite3'`.

**Причина:** `sqlite3.Connection` **не** закрывается **автоматически** при выходе из `with` (контекстный менеджер **делает** `commit`/`rollback`, **не** `close`).

**Решение:** **изменить `get_conn`** на **контекстный менеджер** (`@contextmanager`, `try/finally`, `conn.close()`).

**Или:** **явно** `conn.close()` **после** `with`.

**Проблема 2: `updated = 0` (вместо `1`)**

**Симптом:** `test_fetch_products_updates_names` — `assert result["updated"] == 1`. **Получено:** `0`.

**Причина:** `updated` **считает** **существующие** `products` (не **созданные**). **Но** `name` **обновляется** **отдельно** (в шаге 7).

**Решение:** `updated` — **считать** **в** шаге 7 (**info** → **name**). **`inserted`** — **созданные**. **`updated`** — **обновлённые** `name`.

**Урок:** `sqlite3` **не** закрывает **соединение** автоматически. **Надо** **явно**.

## 2026-11-08 — `@contextmanager` и тесты (исправление)

**Проблема:** `get_conn()` — **`@contextmanager`**. **Тесты** **используют** `conn = get_conn()` (без `with`). **`get_conn()`** возвращает `_GeneratorContextManager` (не `conn`). **`.execute`** — **нет**. **`AttributeError`.**

**Решение:** **все** **тесты** — **`with get_conn() as conn:`** (не `conn = get_conn()`).

**Урок:** `@contextmanager` — **правильно** (закрывает **всегда**). **Но** **тесты** **надо** **обновить** (`with`).

## 2026-11-08 — `test_db.py` (исправление под `@contextmanager`)

**Проблема:** `get_conn()` — **`@contextmanager`**. `test_db.py` **использует** `conn = get_conn()` (без `with`). **`AttributeError`** (`_GeneratorContextManager`).

**Решение:** `test_db.py` — **`with get_conn() as conn:`** (не `conn = get_conn()`).

**Результат:** **51/51 PASSED** (после исправления).
## 2026-11-08 — 51/51 PASSED (Ложка 8+, части 1–2)

**Результат:** **51/51 PASSED** (все юнит-тесты).

**Что сделано:**

**Схема (v3.1):**
- `schema.sql` — 35 таблиц (мн.ч., camelCase, нормализация А).

**Справочники:**
- `seed_reference_data.py` — 16 справочников (модули, валюты, регионы, платформы, типы, издания, издатели, статусы, носители, возрастные группы, типы корректировок, склады, маркетплейсы, площадки закупки, магазины, покупатели).

**Парсер:**
- `parse_names.py` — пишет ID (platformId, editionId, publisherId, typeGoodId, mediaTypeId, regionId), baseGameName, restore.
- `parse_name(name, conn=None)` — принимает conn, читает справочники из него.
- Баги исправлены: Sony вырезается, (Physical) распознаётся, PS4/PS5 — одна платформа, Steelbook — тип/издание.

**Загрузка товаров:**
- `fetch_products.py` — универсальная (через BaseClient).
- `src/clients/base.py` — BaseClient (абстрактный).
- `src/clients/ozon.py` — OzonClient (реализация).
- Проверка .env (префикс площадки), hasApi, «мусор» (пустой offerId — пропуск), прогресс (print, 4 шага).

**БД:**
- `src/db.py` — `@contextmanager` (закрывает всегда).

**Тесты (51):**
- `test_db.py` — 4 (get_conn, PRAGMA, row_factory, init_db).
- `test_pragma.py` — 3 (PRAGMA, FK, CASCADE).
- `test_seed.py` — 16 (все справочники).
- `test_parse_names.py` — 13 (10 позитивных + 3 негативных).
- `test_fetch_products.py` — 15 (5 позитивных + 10 негативных).

**Проблемы, которые решили:**
- `PermissionError` — `@contextmanager` (закрывает всегда).
- `AttributeError: _GeneratorContextManager` — тесты (`with get_conn()`).
- `updated = 0` — считать в шаге 7 (info → name).
- `_is_valid_offer_id` — только на пустоту (странный offerId — валидный).
- `hasApi` vs `.env` — `.env` истина, `hasApi` — подсказка.

**Уроки:**
- TDD работает: тесты описывают желаемое, код подгоняется.
- `@contextmanager` — правильно (закрывает всегда).
- Изоляция тестов — критично (setup_test_db — function scope).
- Универсальность — через BaseClient (позже YmClient — без изменения fetch_products).
- Негативные тесты — важны (устойчивость к «мусору», расхождение hasApi/.env).

**Что дальше:**
- `fetch_postings.py` — переписать под v3.1 (TDD: test_fetch_postings.py).
- `web/app.py` — переписать под v3.1 (TDD: test_api.py).
- `web/routers/keeper.py`, `seller.py`, `settings.py` — переписать под v3.1.
- Шаблоны — обновить.

## 2026-11-08 — `fetch_postings.py`: логика (перед тестами)

**Вопрос:** «В HISTORY надо было сначала логику записать?»

**Ответ:** **Да.** **Порядок** (TDD): **логика** → **логика тестов** → **код тестов** → **код основного**. **Я** **пропустил** **шаг** «логика в HISTORY». **Исправляю.**

### Назначение

**`fetch_postings`** — **универсальная** **загрузка** **отправлений** (продаж) с **площадки** (OZON, YM, WB, ...). **Создаёт** `salesOrders`, `salesOrderItems`, `salesOrderStatusHistory`.

### Сигнатура

```python
fetch_postings(platform, store_code, date_from, date_to, client=None) -> dict
```

### Выход

```python
{
    "ok": True | False,
    "inserted": int,        # создано salesOrders
    "errors": list[str],    # ошибки (не критические)
}
```

### Шаги

1. **Проверить** **магазин** в БД (`stores`).
2. **Проверить** **площадку** (`platform` — `ozon`, `ym`, ...).
3. **Прочитать** `.env` (ключи, префикс площадки).
4. **Проверить** `hasApi` vs `.env`.
5. **Создать** клиент (если `client` не передан).
6. **Загрузить** **отправления** (`client.get_postings(date_from, date_to)`).
   - **Разбить** **по** **годам** (если период > 1 года).
7. **Сохранить** **сырой** JSON в `data/api_raw/{platform}_{store_code}_postings_{date_from}_{timestamp}.json`.
8. **Для** **каждого** **отправления**:
   - **Пропустить** **«мусор»** (`postingNumber = None`, `products = []`).
   - **`warehouseId = 1`** (константа).
   - **Найти** или **создать** `salesOrders` (`buyerId` — из API, иначе `1`).
   - **Создать** `salesOrderStatusHistory` (`statusId` — из `statuses` по `statusName`).
   - **Для** **каждого** **товара**:
     - **`quantity`**: `>0` — как есть; `0` — `0`; `<0` — `abs`, в `errors`; `""`/`None`/`"abc"` — `0`, в `errors`.
     - **`price`**: `>0` — как есть; `0` — `0`; `<0` — `abs`, в `errors`; `""`/`None`/`"abc"` — `0`, в `errors`.
     - **Найти** или **создать** `products` (по `offerId`, если нет — заглушка).
     - **Создать** `salesOrderItems`.
9. **Вернуть** результат.

### Негативные сценарии (тесты)

1. **Магазин не найден** → `ok = False`.
2. **Площадка не найдена** → `ok = False`.
3. **`hasApi = 0`** → `ok = False`.
4. **Нет ключей в `.env`** → `ok = False`.
5. **«Мусор» в `.env`** → `ok = False`.
6. **Ошибка API** (500) → `ok = False`.
7. **Пустой ответ** (`[]`) → `ok = True`, `inserted = 0`.
8. **`None` в ответе** → пропуск.
9. **«Сломанный» JSON** → `ok = False`.
10. **Отрицательное** `quantity` → `abs`, в `errors`.
11. **Пустое** `quantity` → `0`, в `errors`.
12. **Отрицательное** `price` → `abs`, в `errors`.
13. **Пустое** `price` → `0`, в `errors`.

### Позитивные сценарии (тесты)

1. Создаёт `salesOrders`.
2. Создаёт `salesOrderItems`.
3. Создаёт `salesOrderStatusHistory`.
4. Сохраняет сырой JSON.
5. Возвращает `inserted`.
6. Несколько заказов.
7. `buyer_nickname` из API.
8. Fallback `buyerId = 1`.
9. Товар не загружен → заглушка.
10. Несколько товаров в заказе.

**Итого:** **10 позитивных + 13 негативных = 23 теста.**

## 2026-11-08 — `test_fetch_postings.py`: 23/23 FAILED (TDD)

**Сделано:**

**`tests/unit/test_fetch_postings.py`** — 23 теста:
- **10 позитивных:** создание `salesOrders`, `salesOrderItems`, `salesOrderStatusHistory`, сохранение JSON, возврат `counts`, несколько заказов, `buyer_nickname` из API, fallback `buyerId=1`, товар не загружен → заглушка, несколько товаров.
- **13 негативных:** магазин не найден, площадка не найдена, `hasApi=0`, нет `.env`, «мусор» в `.env`, ошибка API (500), пустой ответ, `None` в ответе, «сломанный» JSON, отрицательное `quantity`, пустое `quantity`, отрицательное `price`, пустое `price`.

**Результат:** **23/23 FAILED** (`TypeError: fetch_postings() got multiple values for argument 'client'`).

**Причина:** `fetch_postings.py` — **старый** (v2). **Сигнатура** — **другая** (`fetch_postings(client, ...)`, а не `fetch_postings(platform, store_code, date_from, date_to, client=None)`). **Тесты** передают `client=client` — `TypeError`.

**Это нормально** (TDD). Тесты описывают желаемое. Старый код — не соответствует.

**Что дальше:** переписать `fetch_postings.py` — **функция** `fetch_postings(platform, store_code, date_from, date_to, client=None)`. **Подгонка** под тесты.

## 2026-11-08 — `fetch_postings.py`: 2 падения (исправление)

**Проблема 1: `status = "delivered"` нет в справочнике**

**Симптом:** `test_fetch_postings_creates_status_history` — `assert 0 == 1` (history).

**Причина:** Тест использует `status = "delivered"`. В справочнике `statuses` (seed) — нет `"delivered"` (есть `paid`, `shipped`, `received`, `refusal`, `cancelled`). `_find_status_id` возвращает `None`. `salesOrderStatusHistory` — не создаётся.

**Решение:** Тест использует статус из справочника (`"received"` вместо `"delivered"`). Код не меняем. Позже — маппинг статусов OZON → наши (`delivered` → `received`).

**Проблема 2: `CHECK constraint failed: quantity > 0`**

**Симптом:** `test_fetch_postings_empty_quantity` — `sqlite3.IntegrityError`.

**Причина:** В `schema.sql` — `salesOrderItems.quantity INTEGER NOT NULL CHECK (quantity > 0)`. `_parse_quantity("")` возвращает `0`. `INSERT` с `quantity = 0` — `IntegrityError`.

**Решение:** Изменить схему — `CHECK (quantity >= 0)`. `0` — разрешён (товар есть, но количество 0 — описка площадки).

**Итог:** 23/23 PASSED (после исправлений).
## 2026-11-08 — `fetch_postings.py`: 2 падения (решение)

**Проблема 1: `status = "delivered"` нет в справочнике**

**Решение (Б — конструктор):** `_find_or_create_status` — **создаёт** неизвестный статус в `statuses` автоматически (`statusType = 'sale'`, `sortOrder = 999`, `isActive = 1`). Площадка вольна (как с `offerId`).

**Проблема 2: `quantity = 0` → `CHECK constraint failed`**

**Решение:** Схема — **не** меняем (`CHECK (quantity > 0)` логичен: продажа с `quantity = 0` бессмысленна). `quantity = 0` — **ошибка** (в `errors`), `salesOrderItems` — **не** создаём.

**Логика `quantity`:**
- `>0` — создаём.
- `=0` — ошибка (в `errors`), не создаём.
- `<0` — abs (в `errors`), создаём (если abs > 0).
- `""` / `None` / `"abc"` — 0 (в `errors`), не создаём.

**Итог:** 23/23 PASSED (после исправлений).
## 2026-11-08 — Статусы и `quantity = 0` (стандарты)

**Статусы у разных площадок — разные:**
- OZON: `delivered`, `delivering`, `awaiting_deliver`, ... [citation:2][citation:8].
- Яндекс.Маркет: `DELIVERED`, `SHIPPED`, `CANCELLED`, ... [citation:11].

**Решение:** `_find_or_create_status` (Б — конструктор) — создаёт неизвестный статус в `statuses` автоматически (`statusType = 'sale'`). Позже — маппинг (`delivered` OZON → `received` наш).

**`quantity = 0` — стандарты:**
- ERP.net: `quantity == 0` — neutral operation, не создаёт заказы/счета [citation:17].
- Salesforce: `quantity = 0` — отменённая строка, по умолчанию отклоняется [citation:23].
- Embrace: `quantity = 0` — строка отменена (X = Cancelled), не загружается [citation:18].
- 1С: `quantity = 0` — не движение ТМЦ (нет изменения остатка) .

**Вывод:** `quantity = 0` в продаже — стандартно НЕ допускается. Схема `CHECK (quantity > 0)` — правильная. `quantity = 0` — ошибка (в `errors`), `salesOrderItems` — не создаём.

**Итог:** 23/23 PASSED (после исправлений).
## 2026-11-08 — `fetch_postings.py` v3.1 (23/23 PASSED)

**Сделано:**

**`src/scripts/fetch_postings.py`** — переписан под v3.1:
- **Функция** `fetch_postings(platform, store_code, date_from, date_to, client=None)` (не скрипт).
- **Универсально** (через `_create_client`: `OzonClient`, `YmClient`, ...).
- **Проверка** `.env` (префикс площадки).
- **Проверка** `hasApi` vs `.env`.
- **Проверка** площадки (`ozon`, `ym`, `wb`).
- **`_find_or_create_status`** — создаёт неизвестный статус в `statuses` (конструктор, площадка вольна).
- **`_find_or_create_buyer`** — из API (`buyer_nickname`), иначе `1` (Физлицо).
- **`_find_or_create_product`** — из `offerId`, иначе заглушка.
- **`_parse_quantity`** — `>0` (создаём), `=0` (ошибка, не создаём), `<0` (abs, ошибка), `""`/`None`/`"abc"` (0, ошибка).
- **`_parse_price`** — `>0` (создаём), `=0` (0), `<0` (abs, ошибка), `""`/`None`/`"abc"` (0, ошибка).
- **`warehouseId = 1`** (константа).
- **Прогресс** (print, 4 шага).
- **Возврат** `{"ok", "inserted", "errors"}`.

**Тесты:**

**`tests/unit/test_fetch_postings.py`** — 23 теста:
- **10 позитивных:** создание `salesOrders`, `salesOrderItems`, `salesOrderStatusHistory`, сохранение JSON, возврат `counts`, несколько заказов, `buyer_nickname` из API, fallback `buyerId=1`, товар не загружен → заглушка, несколько товаров.
- **13 негативных:** магазин не найден, площадка не найдена, `hasApi=0`, нет `.env`, «мусор» в `.env`, ошибка API (500), пустой ответ, `None` в ответе, «сломанный» JSON, отрицательное `quantity`, пустое `quantity`, отрицательное `price`, пустое `price`.

**Результат:** **23/23 PASSED**.

**Решения:**
- `_find_or_create_status` (конструктор) — статусы у разных площадок разные (OZON: `delivered`, `delivering`, ...; YM: `DELIVERED`, ...). Создаём неизвестный статус автоматически. Позже — маппинг.
- `quantity = 0` — ошибка (не создаём `salesOrderItem`). Схема `CHECK (quantity > 0)` — логична (стандарты ERP подтверждают: `quantity = 0` — не продажа).
- `quantity < 0` — `abs` (в `errors`), создаём (если `abs > 0`).
- `price = 0` — 0 (создаём, если `quantity > 0`).
- `price < 0` — `abs` (в `errors`), создаём.

**Проблемы, которые решили:**
- `TypeError: fetch_postings() got multiple values for argument 'client'` — старый код (v2), другая сигнатура. Решение: переписали под v3.1.
- `status = "delivered"` нет в справочнике — `_find_or_create_status` (конструктор).
- `CHECK constraint failed: quantity > 0` — `quantity = 0` — ошибка (не создаём).
- `AttributeError: module 'src.scripts.fetch_postings' has no attribute 'DATA_API_RAW'` — фикстура `cleanup_api_raw` зависит от модуля. Решение: работает с `data/api_raw` напрямую.

**Уроки:**
- TDD работает: тесты описывают желаемое, код подгоняется.
- Универсальность: через `_create_client` (позже YmClient — без изменения fetch_postings).
- `_find_or_create_status` — конструктор (площадка вольна).
- `quantity = 0` — ошибка (стандарты ERP подтверждают).
- Полный файл: частичное обновление — ошибка (потеряли тесты).

## 2026-11-08 — Pipeline (end-to-end) — следующий шаг

**Проблема:** «В бою» не видно. Тесты — есть, код — есть, но end-to-end pipeline — не проверен.

**Что готово (v3.1):**
- `schema.sql` (35 таблиц).
- `db.py` (get_conn, init_db).
- `seed_reference_data.py` (16 справочников).
- `parse_names.py` (пишет ID).
- `fetch_products.py` (универсальный).
- `fetch_postings.py` (универсальный).
- `src/clients/base.py`, `src/clients/ozon.py`.

**Итого:** 71 тест (все PASSED).

**Что НЕ готово (v3.1):**
- `web/app.py`, `web/routers/*`, шаблоны (старые, v2).
- `pipeline.py` (нет).
- `add_stores.py` (старый, v2).

**Решение:** сначала pipeline (вручную), потом веб.

**Pipeline (физический, вручную):**
1. `init_db` — создать БД.
2. `seed_reference_data` — справочники.
3. `fetch_products ozon limited_games` — товары.
4. `fetch_products ozon console_games` — товары.
5. `fetch_postings ozon limited_games 2022-01-01 2026-12-31` — продажи.
6. `fetch_postings ozon console_games 2026-01-01 2026-12-31` — продажи.
7. `parse_names` — разбор названий.
8. Проверка — `SELECT COUNT(*) FROM products`, `salesOrders`, ... .

**Запуск:** `python pipeline.py` (вручную).

**Плюс:** быстро (не надо веб). Видно результат (в БД).
**Минус:** не «конструктор» (позже — через веб).

**Что дальше:**
- `pipeline.py` (физический).
- Проверка (end-to-end).
- `web/app.py`, `web/routers/*`, шаблоны (TDD).
- «Конструктор» (через веб).

## 2026-11-08 — Pipeline: первый запуск (fetch_products упал на .env)

**Результат:**
- `init_db` — ✅ (35 таблиц).
- `seed_reference_data` — ✅ (16 справочников).
- `fetch_products` — ❌ (`hasApi=1`, но нет ключей в `.env`).
- Pipeline остановлен (критично).

**Причина:** В `.env` нет ключей `OZON_LIMITED_GAMES_CLIENT_ID`, `OZON_LIMITED_GAMES_API_KEY`, `OZON_CONSOLE_GAMES_CLIENT_ID`, `OZON_CONSOLE_GAMES_API_KEY`.

**Это правильное поведение.** Логика сработала: `hasApi=1` + нет ключей → остановка (критично).

**Что дальше:** настроить `.env` (ключи OZON для двух магазинов). Потом — повторный запуск pipeline.

## 2026-11-08 — Pipeline: первый успешный запуск (парсер — дыры)

**Результат pipeline:**
- `init_db` — ✅ (35 таблиц).
- `seed_reference_data` — ✅ (16 справочников).
- `fetch_products` — ✅ (LimitedGames: 1705, ConsoleGames: 608, итого 2313).
- `fetch_postings` — ❌ (`OzonClient` нет `get_postings` — метод не реализован).
- `parse_names` — ✅ (2313 товаров разобрано).
- Проверка — ✅ (2313 products, 2313 listings, 0 salesOrders, 0 salesOrderItems).

**Проблемы парсера:**

1. **`XO/XS` не разобрано** (`platformId = None`).
   - **Причина:** в `PLATFORM_MAP` есть `"xo/xs"`, но в `platforms` нет записи `"Xbox One / Xbox Series"`.
   - **Решение:** добавить в `platforms` запись `"Xbox One / Xbox Series"`.

2. **`NSW/NSW2` не разобрано** (`platformId = None`).
   - **Причина:** в `PLATFORM_MAP` есть `"nsw/nsw2"`, но в `platforms` нет записи `"Nintendo Switch 1 / Nintendo Switch 2"`.
   - **Решение:** добавить в `platforms` запись `"Nintendo Switch 1 / Nintendo Switch 2"`.

3. **`Injustice 2 Legendary Edition Steelbook` — `editionId = 6` (Steelbook), а должно быть `Legendary Edition Steelbook`.**
   - **Причина:** `Steelbook` — часть названия (`Legendary Edition Steelbook`). Парсер вырезает `Steelbook` как издание, а `Legendary Edition` — не распознаёт.
   - **Решение:** добавить в `EDITION_MAP` фразу `"legendary edition steelbook"` (и другие комбинации). В `extract_edition` — приоритет длинных фраз.

4. **`fetch_postings` — `OzonClient` нет `get_postings`.**
   - **Причина:** метод не реализован в `OzonClient`.
   - **Решение:** добавить `get_postings` в `OzonClient` (TDD: тесты уже есть).

**Что дальше:**
- Добавить в `platforms` записи `"Xbox One / Xbox Series"`, `"Nintendo Switch 1 / Nintendo Switch 2"`.
- Добавить в `EDITION_MAP` `"legendary edition steelbook"` (и другие).
- Добавить `get_postings` в `OzonClient` (TDD).
- Повторный запуск pipeline.

**Урок:** Парсер — не идеален. Нужны тесты на реальные данные (из pipeline).

## 2026-11-08 — Парсер: платформы, Edition, .env.example (исправления)

**1. `platforms` — добавить две новые записи:**
- `("Xbox", "One / Series", None, 0)` — совместимая.
- `("Nintendo Switch", "1 / 2", None, 0)` — совместимая.

**Причина:** `XO/XS` и `NSW/NSW2` не разбирались (`platformId = None`), потому что в `platforms` не было записей `"Xbox One / Series"`, `"Nintendo Switch 1 / 2"`.

**2. `parse_names.py` — приоритет Edition выше Steelbook:**
- Сначала `extract_edition` (якорь `Edition` — 3-2-1 слова до + слово после, если в `EDITION_MAP`).
- Потом `Steelbook` (отдельно — если не вырезан в edition).

**Пример:** `"Injustice 2 Legendary Edition Steelbook (PS4/PS5)"` → `extract_edition` находит `Legendary Edition Steelbook` (3 слова до `Edition` + `Steelbook` после). `editionId = Legendary Edition Steelbook`. `Steelbook` — не вырезается отдельно.

**В `EDITION_MAP` добавить:**
- `"legendary edition steelbook": "Legendary Edition Steelbook"`.
- `"legendary edition": "Legendary Edition"`.

**3. `OzonClient.get_postings` — добавить:**
- Метод `get_postings(date_from, date_to)` — запрос `/v4/posting/fbs/list` (с пагинацией).
- TDD (тесты уже есть).

**4. `.env.example` — заменить форматы и названия:**
- Было: `OZON_LIMITED_GAMES_ID`, `OZON_LIMITED_GAMES_KEY`.
- Стало: `OZON_LIMITED_GAMES_CLIENT_ID`, `OZON_LIMITED_GAMES_API_KEY`.
- Аналогично для `console_games`.
- Обновить комментарии (форматы, названия).

## 2026-11-08 — Edition в seed (уточнение)

**Вопрос:** «Разве Edition в seed не загружаются?»

**Ответ:** Загружаются, но `Legendary Edition` и `Legendary Edition Steelbook` — **не** в списке (19 изданий в `seed_reference_data.py`). Забыли добавить.

**Решение (А + Б):**

**А. `seed_reference_data.py` — добавить в `editions`:**
- `'Legendary Edition'` (id новый, sortOrder 200).
- `'Legendary Edition Steelbook'` (id новый, sortOrder 210).

**Б. `parse_names.py` — добавить в `EDITION_MAP`:**
- `"legendary edition steelbook": "Legendary Edition Steelbook"`.
- `"legendary edition": "Legendary Edition"`.

**Причина:** Без `seed` — `_find_edition_id` не найдёт ID (вернёт `None`). Без `EDITION_MAP` — парсер не распознает фразу.

**Согласовано.**

## 2026-11-08 — Pipeline: 3 проблемы (fetch_postings, platformId, Anniversary Collection)

**1. `fetch_postings` — 404 (`/v3/posting/fbs/list` не найден).**

**Причина:** OZON изменил путь (с `/v3` на `/v4` или `/v2`).

**Решение:** попробовать `/v4/posting/fbs/list`. Если 404 — `/v2/posting/fbs/list`.

**2. `platformId = 162` — для `NSW/NSW2` (не `Nintendo Switch 1 / 2`).**

**Причина:** `_find_platform_id` вернул 162. Значит, в БД была запись с id=162 (остаток от предыдущих тестов? `seed` не очищает таблицы, `INSERT OR IGNORE`). `init_db` создаёт БД с нуля, но `seed` не удаляет старые записи.

**Решение:** `init_db` должен удалять БД перед созданием. Или `pipeline.py` удаляет БД перед `init_db`.

**3. `Anniversary Collection` — нет в `EDITION_MAP`.**

**Причина:** в `EDITION_MAP` есть `"anniversary": "Anniversary"`, но нет `"anniversary collection": "Anniversary Collection"`. Парсер не распознаёт фразу.

**Решение:** добавить в `EDITION_MAP` `"anniversary collection": "Anniversary Collection"`.

**Согласовано.**

## 2026-11-08 — Парсер: логика создания новых изданий (Вариант Б)

**1. Механика создания нового издания:**
- `extract_edition` находит фразу до `Edition` (3-2-1 слова).
- Если фраза не в `EDITION_MAP` — проверяет, есть ли базовое издание в фразе (`Limited`, `Steelbook`, ...).
- Если есть — `_find_or_create_edition(conn, фраза)` создаёт запись в `editionTypes` (sortOrder = 999).
- Если нет — оставляет в `baseGameName` (`editionId = None`).

**2. Фраза до `Edition` (3-2-1 слова). Слово после `Edition` — пока не берём.**
- `"Legendary Edition Steelbook"` → `editionId = Legendary` (не `Legendary Edition Steelbook`).
- `"Survivor Steelbook Edition"` → `editionId = Survivor Steelbook` (создаём новое, есть `Steelbook`).

**3. `Year` — не издание. `First Year`, `New Year` — издания.**
- Добавить в `EDITION_MAP`: `"first year"`, `"new year"`.
- `"game of the year"`, `"goty"` — тоже издания. Добавить.

**4. `Collection` и `Collection's` — не в базисе.**
- `"collector's"` — есть. `"collection"` — нет.
- Добавить в `EDITION_MAP`: `"collection"`.
- Добавить в `seed_reference_data.py`: `'Collection'`.

**Согласовано.**

## 2026-11-08 — Тесты: проверка создания нового Edition

**Принцип:** тест проверяет не только результат (`editionId`), но и факт создания новой записи в `editionTypes`.

**Пример теста (`First Year`):**
1. До разбора — нет "First Year" в `editionTypes`.
2. Разбираем `"Game First Year Edition (PS5)"`.
3. `editionId` — не `None`.
4. В `editionTypes` — появилась запись `"First Year"`.
5. `after["editionId"] == result["editionId"]`.

**Аналогично — для `Survivor Steelbook Edition`, `Limited Steelbook Edition` (создание нового издания с базовым).**

**Итого:** тесты проверяют и результат, и создание.

## 2026-11-08 — Тесты: PermissionError + First Year в seed

**Проблема 1: PermissionError (23 ERROR).**

**Причина:** тест `test_parse_name_creates_new_edition_first_year` упал (AssertionError), но не закрыл соединение (`conn.close()` не вызван). Соединение висит. Следующий тест не может удалить файл (занят).

**Решение:** в тесте `test_parse_name_creates_new_edition_first_year` — закрывать соединение в `finally` (или через фикстуру).

**Проблема 2: `First Year` уже есть в `editionTypes` (AssertionError).**

**Причина:** в `seed_reference_data.py` добавлено `('First Year', 240)` в `editionTypes`. `conftest.py` наполняет тестовую БД через `seed_reference_data` (все справочники). Значит, `First Year` уже есть до разбора.

**Решение:** убрать `First Year` из `seed_reference_data.py` (создаваться должно только при разборе). Тест проверит создание (конструктор).

**Согласовано.**

## 2026-11-08 — Итог сессии: pipeline, тесты, парсер (80 тестов, 56 PASSED, 1 FAILED, 23 ERROR)

**Что сделано за сессию:**

**Схема (v3.1):**
- `schema.sql` — 35 таблиц (мн.ч., camelCase, нормализация А).
- `init_db` — удаляет БД перед созданием (чистая БД каждый раз).

**Справочники:**
- `seed_reference_data.py` — 16 справочников.
- Добавлены: `Xbox One / Series`, `Nintendo Switch 1 / 2` (platforms), `Legendary Edition`, `Legendary Edition Steelbook`, `Anniversary Collection`, `Collection`, `First Year`, `New Year`, `GOTY` (editions), `Super Rare Games` (publishers).

**Клиенты:**
- `src/clients/base.py` — `BaseClient` (абстрактный).
- `src/clients/ozon.py` — `OzonClient` (`get_products`, `get_product_info`, `get_postings`).

**Загрузка:**
- `fetch_products.py` — универсальный (TDD, 15 тестов PASSED).
- `fetch_postings.py` — универсальный (TDD, 23 теста PASSED).
- `pipeline.py` — end-to-end (6 шагов, конфиг `pipeline_config.json`).
- `pipeline_config.json` — временный (позже — из меню «Настройки»).

**Парсер:**
- `parse_names.py` — v3.2 (пишет ID).
- Вариант Б: новые издания создаются в `editionTypes` (только с известным базовым).
- `EDITION_MAP` += `Legendary Edition Steelbook`, `Legendary Edition`, `First Year`, `New Year`, `GOTY`, `Game of the Year` (маппинг на GOTY), `Three Fairies`, `Three Fairies Edition`, `Collection`, `Anniversary Collection`.
- `BASE_EDITIONS` — базовые издания для создания новых.
- `extract_edition` — проверяет слово после `Edition` (если в `EDITION_MAP`).
- `combo` — добавлен в список bundle.
- `Испания` — не регион (страна, `regionId = None`).

**Тесты (80):**
- `test_db.py` — 4.
- `test_pragma.py` — 3.
- `test_seed.py` — 16.
- `test_parse_names.py` — 18 (11 позитивных + 3 негативных + 4 создания).
- `test_fetch_products.py` — 15.
- `test_fetch_postings.py` — 23.

**Pipeline — результат:**
- `init_db` — ✅ (35 таблиц).
- `seed_reference_data` — ✅ (16 справочников, 32 platforms, 22 editions).
- `fetch_products` — ✅ (LimitedGames: 1705, ConsoleGames: 608, итого 2313).
- `fetch_postings` — ❌ (400 Bad Request на `/v4/posting/fbs/list` — payload не тот).
- `parse_names` — ✅ (2313 товаров разобрано).
- Проверка — ✅ (2313 products, 2313 listings, 0 salesOrders).

**Проблемы (на конец сессии):**

1. **`fetch_postings` — 400 Bad Request** (`/v4/posting/fbs/list`). Payload не тот. Надо проверить документацию OZON (актуальный формат: `filter`, `limit`, `cursor`).

2. **Тесты: 1 FAILED, 23 ERROR.**
   - **FAILED:** `test_parse_name_creates_new_edition_first_year` — `First Year` уже есть в `editionTypes` (из `seed`).
   - **ERROR (23):** `PermissionError` — тест упал, но не закрыл соединение (`conn.close()` не вызван). Следующий тест не может удалить файл.

**Решения (на следующую сессию):**

1. **Убрать `First Year`, `New Year`, `GOTY` из `seed_reference_data.py`** (создаваться должны только при разборе, через `_find_or_create_edition`). Тест проверит создание (конструктор).

2. **В тестах `test_parse_name_creates_new_edition_*`, `test_parse_name_goty`, `test_parse_name_collection`, `test_parse_name_combo_is_bundle` — `try/finally`** (закрывать соединение). Иначе `PermissionError` каскадом.

3. **`fetch_postings` — проверить документацию OZON** (актуальный формат `/v4/posting/fbs/list`). Возможно, `filter` → `filter` с `since`/`to`, `limit` → `limit`, `cursor` → `cursor`. Или `/v3/posting/fbs/list` с `offset`.

**Уроки:**
- TDD работает: тесты описывают желаемое, код подгоняется.
- `@contextmanager` — правильно (закрывает всегда).
- Изоляция тестов — критично (`setup_test_db` — function scope).
- Полный файл: частичное обновление — ошибка (потеряли тесты).
- `try/finally` в тестах — обязательно (иначе `PermissionError` каскадом).
- `seed` — только базовые справочники. Новые издания создаются при разборе (конструктор).
- `.env` — не присылать ключи в чат (даже если «никому не нужны»).

**Что дальше (следующая сессия):**
1. Исправить тесты (убрать `First Year` из `seed`, `try/finally`).
2. Исправить `fetch_postings` (формат payload).
3. Повторный запуск тестов (80/80 PASSED).
4. Повторный запуск pipeline (6/6 шагов).
5. `web/app.py`, `web/routers/*`, шаблоны (TDD).
6. «Конструктор» (через веб).

## 2026-11-09 — Парсер: отказ от создания, источник истины — `editionTypes` (v3.5)

**Контекст:** `GOTY` / `Game of the Year` / `First Year` / `Survivor Steelbook` — неоднозначно. Решение: **не создавать** издания в парсере. Источник истины — `editionTypes` (seed). Парсер **ищет** точное (нормализованное) совпадение. Не нашёл → `editionId = None` (правится в «Настройках»).

**Что удалено:**
- `EDITION_MAP` (в `parse_names.py`).
- `BASE_EDITIONS` (в `parse_names.py`).
- `SINGLE_WORD_EDITION_MAP` (в `parse_names.py`).
- `_find_or_create_edition` (в `parse_names.py`).
- `test_parser_logic` (в `tests/test_api.py`, старый v2).
- `tests/test_api.py` (целиком — API-тесты отложены).

**Что добавлено:**
- **`normalize_edition(s)`** — агрессивная нормализация: `lower`, `’`/`‘`→`'`, убрать `' . - _`, схлопнуть пробелы.
- **`_DICTIONARIES["editions"]`** — ключ **нормализованный** `editionName`, значение `editionId`.
- **`extract_edition`** — только поиск:
  1. Якорь `Edition`: n=4, 3, 2, 1 — точное (нормализованное) в `editionTypes`.
  2. Без якоря: все `editionName` (длинные приоритетнее), точное (нормализованное) вхождение.
  3. Не нашли → `(None, full_name)`.
- **`GOTY`** и **`Game of the Year`** — **оба** в `editionTypes` (разные написания в данных). Парсер найдёт **любой**.
- **`seed_editionTypes`** — **46** изданий (все, что парсер может найти): базовые, составные, `GOTY` + `Game of the Year`, `First Year`, `New Year`, `Three Fairies`, `Survivor Steelbook`, `Survivor`, `Legendary`, одиночные в скобках (`Platinum`, `Black`, `Tails`, `Knuckles`).

**Тесты:**
- `test_seed.py` — `>= 30` платформ, `>= 45` изданий (не жёстко).
- `test_parse_names.py` — 27 тестов:
  - **end-to-end:** `"Видеоигра Test Game (PS5)"` → `typeGoodId = game`, `platformId = PS5`, `baseGameName = "Test Game"`.
  - **поиск:** `Deluxe`, `GOTY`, `Game of the Year`, `First Year`, `Anniversary Collection`.
  - **негативные:** неизвестное издание → `None`; «мусор» / пустая строка / только скобки — не падает.
  - **нормализация:** `Collector's` = `Collectors`; `K.O.` = `ko`; двойной пробел = один.
- **Удалены** (создания нет): `test_parse_name_creates_new_edition_first_year`, `test_parse_name_creates_new_edition_survivor_steelbook`, `test_parse_name_goty` (старый — создание).

**Результат:** **87/87 PASSED** (все юнит-тесты).

**Уроки:**
- Один источник истины (`editionTypes`) — нет рассинхрона.
- Агрессивная нормализация — меньше пропусков (`Collector's` = `Collectors`), цена ошибки низкая.
- Парсер **не создаёт** — правится в «Настройках» (текущее приложение), не в Конструкторе (будущий продукт).
- `GOTY` и `Game of the Year` — **оба** (разные написания в данных), не дубли по смыслу (разные записи).
- API-тесты — **удалены** (старые, v2). Позже — с нуля под v3.1.

**Что дальше:**
- `fetch_postings` — 400 Bad Request на `/v4/posting/fbs/list` (payload). Проверить документацию OZON.
- `web/app.py`, `web/routers/*`, шаблоны — переписать под v3.1 (TDD).
- «Конструктор» (через веб) — после MVP.

## 2026-11-09 — Итог по парсеру v3.6 (80%) и начало API-тестов

**Текущий статус:** парсер разобран на 80%. Оставшиеся косяки требуют ручной правки или отложены на этап «Конструктора».

**Что починили в v3.6:**

- **Заглушки:** алгоритм удаления переписан. Теперь он удаляет товары с ``name LIKE 'Товар %'`` или ``baseGameName LIKE 'Товар %'`` **вместе с их позициями в заказах** (независимо от того, были ли продажи). Это очищает базу от мусора (удалили 413 заглушек).
- **Платформа Dreamcast:** добавлены ``sega dreamcast``, ``dreamcast``, ``dc``, ``sega saturn`` в ``PLATFORM_MAP``, чтобы парсер видел платформу.
- **Очистка от «Edition»:** если слово ``Edition`` не распознано как издание, оно удаляется из ``baseGameName`` в конце.
- **``Bundle``:** если в названии есть ``bundle``, ``trilogy`` и т.д. — тип устанавливается в ``bundle`` (переопределяет ``game``).
- **``Overkill Edition``:** теперь издание ищется по якорю ``Edition``, даже если до него нет ``Edition`` в ``seed`` (сработала нормализация).

**Что НЕ исправлено (известные баги, 20%):**

1. **Огрызки от издателя в скобках.** ``( Run Games)`` вместо ``(Limited Run Games)``.
   - *Причина:* при поиске издателя в скобках парсер не вырезает его из строки, а просто ставит ``publisherId``.
   - *Решение:* нужно вырезать ``bracket_text`` целиком, если издатель найден (код я давал, но он не применился из-за отступов).
2. **``Deluxe`` не вырезается.** Пример: ``Angry Video Game Nerd 1 & 2 Deluxe``.
   - *Причина:* слова ``Deluxe`` нет в ``seed``, поэтому парсер не знает, что это издание.
   - *Решение:* добавить ``Deluxe`` в ``seed_editionTypes``.
3. **``Stellar`` не вырезается.** Пример: ``Everspace 2: Stellar Steelbook Edition`` → осталось ``Everspace 2: Stellar``.
   - *Причина:* слова ``Stellar`` нет в ``seed``. Аналогично ``Deluxe``.

**Итог:** Парсер отрабатывает 80% данных корректно. Остальные 20% — это уникальные издания (вроде ``Stellar``, ``Journey``, ``Crimson Knight``), которые пока не в ``seed``. Мы не создаем их на лету (это отложено в Конструктор). В «Настройках» можно будет добавить их вручную.

**Следующий шаг:** API-тесты (``tests/test_api.py``) и обновление Git (фиксация текущего состояния ветки).

## 2026-11-09 — API-тесты и автоматизация (идея для Конструктора)

**Проблема:** OZON меняет структуру API регулярно (по отзывам — раз в месяц). Если формат ответа меняется, наш парсер и загрузчик молча теряют данные (как было с ценами и лимитом 100). 

**Сделано (текущее):** 
- Написаны API-тесты. Создана папка `tests/api/` с тестами для проверки структуры ответов.
- `tests/api/test_ozon_schema.py` — тест на контракт (JSON Schema). Проверяет, что реальный ответ OZON соответствует ожидаемому формату (наличие `posting_number`, `products` и т.д.). Если OZON меняет API, тест падает, и мы узнаем об этом до потери данных.
- `tests/api/test_api.py` — базовый тест «здоровья» (health-check) для FastAPI.

**Идея для Конструктора (автоматизация):** 
- Использовать **OpenAPI Generator**. OZON публикует свою схему (swagger.json). 
- Вместо ручного написания клиента (`ozon.py`) мы берем схему от OZON и генерируем код автоматически.
- **Плюсы:** скорость, безопасность типов (нельзя передать `limit=1000`, если схема говорит `max=100`), автоматическая синхронизация при обновлении API.
- **Когда внедрять:** когда запросов к OZON станет много (не только постинги, но и товары, отзывы, цены). Пока что ручной клиент + тест на схему — это нормально.

**Следующий шаг:** API-тест (проверка схемы) должен стать обязательным шагом в `pipeline.py` (чтобы пайплайн падал, если OZON изменил формат).