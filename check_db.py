import sqlite3

# Подключаемся к базе
conn = sqlite3.connect('db/only_limited.sqlite3')

# Получаем список таблиц
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

print("Таблицы в базе:")
for t in tables:
    print(f" - {t}")

if 'stock_manual' in tables:
    print("\n✅ Таблица stock_manual НАЙДЕНА.")
else:
    print("\n❌ Таблицы stock_manual НЕТ.")