import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')

# Добавляем магазины
conn.execute("INSERT OR IGNORE INTO store (code, name, client_id, has_api, is_active) VALUES ('limited_games', 'LimitedGames', '428109', 1, 1)")
conn.execute("INSERT OR IGNORE INTO store (code, name, client_id, has_api, is_active) VALUES ('console_games', 'Console Games', '3887994', 1, 1)")

# Добавляем склад (если его нет)
conn.execute("INSERT OR IGNORE INTO warehouse (code, name, default_currency, is_active) VALUES ('main_warehouse', 'Основной склад', 'RUB', 1)")

conn.commit()
print("Магазины и склад добавлены.")