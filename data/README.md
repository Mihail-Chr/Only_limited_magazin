# Данные (data)

Промежуточные и экспортированные данные. **Не коммитить в Git** (кроме этого README).

## Структура

```
data/
├── api_raw/          # Сырые JSON-ответы от OZON API
│   ├── limited_games_product_list_YYYYMMDD_HHMMSS.json
│   ├── limited_games_prices_YYYYMMDD_HHMMSS.json
│   ├── limited_games_stocks_fbs_YYYYMMDD_HHMMSS.json
│   └── limited_games_postings_YYYY_YYYYMMDD_HHMMSS.json
└── exports/          # Готовые отчёты для пользователей
    └── stock_report_YYYYMMDD_HHMMSS.csv
```

## Что внутри

### `api_raw/`
Сырые ответы от OZON API. Нужны для:
- отладки (если что-то пошло не так — можно посмотреть, что вернул API);
- повторного парсинга без повторного запроса к API;
- аудита (что именно было загружено в конкретную дату).

Файлы именуются с timestamp: `limited_games_product_list_20261024_215449.json` (магазин + метод + дата-время).

### `exports/`
Готовые отчёты для пользователей (CSV, Excel). Например, `stock_report_*.csv` — выгрузка остатков для кладовщика.

## Очистка

Файлы накапливаются. Раз в месяц можно чистить старые:
```bash
# Удалить всё старше 30 дней
find data/api_raw -name "*.json" -mtime +30 -delete
find data/exports -name "*.csv" -mtime +30 -delete
```

Но перед очисткой — убедиться, что данные уже загружены в БД (проверить счётчики через `report_stock`).

## .gitignore

```
data/api_raw/*
data/exports/*
!data/README.md
```