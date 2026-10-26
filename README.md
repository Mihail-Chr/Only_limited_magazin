# Only_limited_magazin

Система учёта товаров и аналитики продаж для виртуального магазина игр, аксессуаров и коллекционных изданий.

## 🚀 Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 3. Инициализировать базу
python -m src.scripts.init_db
python -m src.scripts.seed

# 4. Загрузить справочники
# (выполнить SQL из sql/11_data_reference.sql и sql/12_data_geo_game.sql в DBeaver)

# 5. Загрузить данные из OZON API (для каждого магазина)
python -m src.scripts.fetch_products limited_games
python -m src.scripts.fetch_products console_games
python -m src.scripts.fetch_product_details limited_games
python -m src.scripts.fetch_product_details console_games
python -m src.scripts.fetch_postings limited_games 2022-01-01 2022-12-31
python -m src.scripts.fetch_postings console_games 2026-01-01 2026-12-31

# 6. Разобрать названия (тип, платформа, издание)
python -m src.scripts.parse_names

# 7. Запустить веб-интерфейс
uvicorn web.app:app --reload
```

## 📚 Документация

| Документ | Что внутри |
|---|---|
| [`docs/`](docs/README.md) | Вся документация проекта |
| [`docs/00_глоссарий.md`](docs/00_глоссарий.md) | Термины проекта |
| [`docs/01_общие_сведения.md`](docs/01_общие_сведения.md) | Контекст, цели, границы |
| [`docs/02_бизнес-процессы.md`](docs/02_бизнес-процессы.md) | Закупка, продажа, потери, возвраты |
| [`docs/04_модель_данных.md`](docs/04_модель_данных.md) | Справочники (часть 1) |
| [`docs/041_модель_данных.md`](docs/041_модель_данных.md) | Товары и склад (часть 2) |
| [`docs/042_модель_данных.md`](docs/042_модель_данных.md) | Закупка (часть 3) |
| [`docs/043_модель_данных.md`](docs/043_модель_данных.md) | Продажа (часть 4) |
| [`diagrams/`](docs/diagrams/README.md) | ER-диаграммы (Mermaid) |

## 🗂 Структура проекта

```
Only_limited_magazin/
├── docs/                    # Документация (markdown)
├── diagrams/                # ER-диаграммы
├── sql/                     # SQL-скрипты (схема + справочники + тесты)
├── src/                     # Python-код (приложение)
│   ├── scripts/             # Скрипты (импорт, загрузка, отчёты)
│   ├── config.py            # Чтение .env
│   ├── db.py                # Подключение к БД
│   ├── ozon_client.py       # HTTP-клиент OZON API
│   └── schema.sql           # DDL для SQLite
├── web/                     # Веб-интерфейс (FastAPI)
│   ├── app.py               # Точка входа
│   ├── routers/             # Роутеры (keeper, seller, api)
│   ├── templates/           # HTML-шаблоны (Jinja2)
│   └── static/              # CSS, JS
├── data/                    # Данные (экспорты, сырые JSON)
├── db/                      # Файл SQLite
├── scratch/                 # Временные скрипты (не в Git)
├── .env.example             # Шаблон конфигурации
└── README.md                # Этот файл
```

## 🛠 Технологии

- **Python 3.11+** — основной язык
- **SQLite** — база данных на старте (позже — PostgreSQL)
- **requests** — HTTP-клиент для OZON API
- **openpyxl** — парсинг Excel
- **DBeaver** — визуальный клиент БД
- **Git + Markdown** — версионирование и документация

## 📋 Статус

- ✅ Спроектирована модель данных (34 таблицы для PostgreSQL)
- ✅ Создана SQLite-база для локальной работы
- ✅ Загружены справочники (страны, платформы, жанры, издатели)
- ✅ Интеграция с OZON API (товары, цены, заказы)
- ✅ Загружены данные с двух магазинов:
  - LimitedGames: 1035 товаров, 5808 отправлений (2022–2026).
  - Console Games: 573 товара, 421 отправление (2026).
- ✅ Разбор названий (тип, платформа, издание)
- ✅ Веб-интерфейс для кладовщика (инвентаризация, добавление товара)
- 🔄 В работе: роль Продавца (корзина цен)
- 📅 Далее: развёртывание на сервере (VicroCode), роль Покупателя, агент закупок
