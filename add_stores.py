import sqlite3
from src.config import settings

conn = sqlite3.connect('db/only_limited.sqlite3')

# Добавляем магазины из config (все площадки)
for platform, stores in settings.stores.items():
    for code, store in stores.items():
        conn.execute(
            "INSERT OR IGNORE INTO store (code, name, client_id, has_api, is_active) VALUES (?, ?, ?, 1, 1)",
            (code, store.name, store.store_id)
        )
        print(f"Добавлен магазин: {code} ({store.name}) на площадке {platform}")

# Добавляем склад
conn.execute(
    "INSERT OR IGNORE INTO warehouse (code, name, default_currency, is_active) VALUES ('main_warehouse', 'Основной склад', 'RUB', 1)"
)

conn.commit()
print("Магазины и склад добавлены.")