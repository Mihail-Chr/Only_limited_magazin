# База данных (db)

Файл SQLite-базы. **Не коммитить в Git** (содержит реальные данные).

## Файл

`only_limited.sqlite3` — SQLite-база со всеми таблицами и данными.

## Структура

Таблицы соответствуют модели данных (см. `docs/04_модель_данных.md` и далее), но в упрощённом виде для SQLite:
- `product` — товары (карточки)
- `listing` — публикации товаров в магазинах (цены, SKU)
- `stock_manual` — ручной физический остаток
- `posting` — отправления (заказы) OZON
- `posting_item` — позиции отправлений
- `store` — магазины
- `warehouse` — склады
- `app_user`, `role`, `user_role` — пользователи и роли
- ... и другие (см. `src/schema.sql`)

## Как открыть

**DBeaver:**
1. Новое соединение → SQLite
2. Путь: `db/only_limited.sqlite3`
3. Открыть

**Командная строка (sqlite3):**
```bash
sqlite3 db/only_limited.sqlite3
.tables
.schema product
SELECT COUNT(*) FROM product;
```

## Резервная копия

Перед любыми рискованными операциями (массовое обновление, миграция):
```bash
cp db/only_limited.sqlite3 db/only_limited_backup_YYYYMMDD.sqlite3
```

## Переход на PostgreSQL

SQLite — для локальной работы. При развёртывании на сервере — PostgreSQL (полная схема в `sql/01`–`04`).

## .gitignore

```
db/*.sqlite3
db/*.sqlite3-journal
!db/README.md
```