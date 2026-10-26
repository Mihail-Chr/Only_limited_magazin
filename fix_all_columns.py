import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')

# Список полей, которые могут отсутствовать в SQLite-версии
columns_to_add = [
    ("product", "baseGameName", "TEXT"),
    ("product", "is_active", "INTEGER DEFAULT 1"),
    ("product", "cost_price_synthetic", "REAL"),
    ("product", "cost_price_real", "REAL"),
    ("product", "avg_market_price", "REAL"),
    ("product", "avg_market_price_updated_at", "TEXT"),
    ("listing", "commission_rate", "REAL DEFAULT 0.45"),
    ("listing", "payout_amount", "REAL"),
    ("posting_item", "cost_price_at_sale", "REAL"),
    ("stock_manual", "updated_at", "TEXT")
]

for table, col_name, col_type in columns_to_add:
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
        print(f"Добавлено: {table}.{col_name}")
    except sqlite3.OperationalError:
        print(f"Уже существует: {table}.{col_name}")

conn.commit()
print("Готово! Все необходимые поля на месте.")