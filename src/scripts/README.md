# Скрипты (src/scripts)

Исполняемые скрипты для работы с базой: инициализация, импорт, загрузка из API, отчёты.

Запускать из корня проекта: `python -m src.scripts.<имя>`

## Скрипты

### Инициализация

| Скрипт | Что делает |
|---|---|
| `init_db.py` | Создаёт таблицы из `src/schema.sql` (SQLite) |
| `seed.py` | Заполняет склады, магазины, роли, стартовых пользователей из `.env` |

### Загрузка данных

| Скрипт | Что делает |
|---|---|
| `import_xlsx.py` | Парсит Excel-выгрузку OZON в `product` и `listing` |
| `fetch_products.py` | Загружает список товаров из OZON API → `data/api_raw/*.json` |
| `fetch_product_details.py` | Загружает цены и остатки → обновляет `listing` |
| `fetch_postings.py` | Загружает отправления (заказы) FBS → `posting`, `posting_item` |

### Работа с остатками

| Скрипт | Что делает |
|---|---|
| `set_stock.py` | Устанавливает ручной физический остаток для товара (`--offer_id`, `--qty`) |
| `report_stock.py` | Отчёт по остаткам: физический, в пути, доступно |
| `keeper_dashboard.py` | Дашборд кладовщика (список товаров, что собрать) |
| `export_stock_csv.py` | Экспорт остатков в CSV (для Excel) |
| `fix_initial_stock.py` | Компенсация остатков (чтобы не было минусов после загрузки истории) |

### Себестоимость и маржа

| Скрипт | Что делает |
|---|---|
| `set_synthetic_cost.py` | Рассчитывает «искусственную» себестоимость (цена OZON × (1 − дисконт)) |
| `backfill_cost_history.py` | Заполняет `cost_price_at_sale` в `posting_item` для истории |
| `audit_margin.py` | Аудит маржи: валовая и чистая (после комиссии OZON) |
| `history_margin.py` | (планируется) История маржи по годам |

## Порядок первого запуска

```bash
# 1. Создать схему
python -m src.scripts.init_db

# 2. Заполнить справочники
python -m src.scripts.seed

# 3. Загрузить товары из Excel
python -m src.scripts.import_xlsx

# 4. Загрузить данные из OZON API
python -m src.scripts.fetch_products
python -m src.scripts.fetch_product_details
python -m src.scripts.fetch_postings

# 5. Заполнить историю себестоимости
python -m src.scripts.backfill_cost_history

# 6. Компенсировать остатки (чтобы не было минусов)
python -m src.scripts.fix_initial_stock

# 7. Проверить
python -m src.scripts.report_stock
python -m src.scripts.audit_margin
```

## Параметры (аргументы командной строки)

Некоторые скрипты принимают аргументы:

```bash
# set_stock
python -m src.scripts.set_stock --offer_id 1277 --qty 10

# backfill_cost_history
python -m src.scripts.backfill_cost_history --discount 0.7

# set_synthetic_cost
python -m src.scripts.set_synthetic_cost --discount 0.7
```

## Соглашения

- Все скрипты используют `get_conn()` из `src.db` — единая точка подключения
- Логирование — через `print()` (на старте), позже — через `logging`
- Ошибки — не глотать, выбрасывать наверх с понятным сообщением
- Секреты — через `settings`, не хардкодить