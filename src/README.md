# Python-код (src)

Основной код приложения: конфигурация, подключение к БД, клиент OZON API, скрипты.

## Структура

```
src/
├── __init__.py
├── config.py             # Чтение .env, dataclasses Store и Warehouse
├── db.py                 # Подключение к SQLite, инициализация схемы
├── schema.sql            # DDL для SQLite (SQLite-версия схемы)
├── ozon_client.py        # HTTP-клиент OZON API (throttling, retry)
└── scripts/              # Исполняемые скрипты (см. scripts/README.md)
```

## Файлы

### `config.py`
Читает `.env` через `python-dotenv`. Возвращает объект `Settings` с настройками:
- подключение к БД (`db_driver`, `db_path`)
- OZON API (`ozon_base_url`, `ozon_timeout`, `ozon_rate_limit_per_sec`)
- магазины (`stores` — список `Store`: code, name, client_id, api_key, has_api)
- склады (`warehouses` — список `Warehouse`: code, name, currencies)
- пути к данным (`data_dir`, `data_api_raw`, `data_exports`)

Функции-хелперы: `get_store(code)`, `get_warehouse(code)`.

### `db.py`
Функция `get_conn()` — возвращает `sqlite3.Connection` с `row_factory = sqlite3.Row` (доступ к полям по имени). Включает `PRAGMA foreign_keys = ON`.

Функция `init_db()` — создаёт таблицы из `schema.sql`.

### `schema.sql`
DDL для SQLite. **Важно:** это упрощённая версия для локальной работы. Полная схема (34 таблицы) — в `sql/01`–`04`. SQLite не поддерживает все типы PostgreSQL (`SMALLSERIAL`, `NUMERIC`, `CHECK IN`), поэтому здесь:
- `INTEGER PRIMARY KEY AUTOINCREMENT` вместо `SERIAL`
- `TEXT` вместо `VARCHAR`
- `REAL` вместо `NUMERIC`
- `CHECK` упрощены

При переходе на PostgreSQL — использовать файлы из `sql/`.

### `ozon_client.py`
Класс `OzonClient`:
- Конструктор принимает объект `Store` (берёт `client_id`, `api_key`)
- `post(path, payload)` — отправляет POST-запрос к `https://api-seller.ozon.ru{path}`
- Throttling: не более `ozon_rate_limit_per_sec` запросов в секунду
- Retry: до `ozon_retry_max` попыток с экспоненциальной задержкой
- При 429 (rate limit) — ждёт и повторяет

## Соглашения

- Все имена таблиц и полей — **camelCase** (как в модели данных)
- При обращении к полям в SQL — **обязательны двойные кавычки**: `SELECT "goodId" FROM goods`
- Пути к данным — через `settings` (не хардкодить `./data/`)
- Секреты — только в `.env`, не в коде