import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')

# 1. Добавляем колонку baseGameName (если её нет)
try:
    conn.execute("ALTER TABLE product ADD COLUMN baseGameName TEXT")
    print("Колонка baseGameName добавлена.")
except sqlite3.OperationalError:
    print("Колонка baseGameName уже существует.")

# 2. Заполняем её названиями из поля name (отрезаем по первой скобке)
rows = conn.execute("SELECT id, name FROM product").fetchall()
updated = 0
for row in rows:
    # Берем всё до первого '('
    base_name = row[1].split('(')[0].strip()
    conn.execute("UPDATE product SET baseGameName = ? WHERE id = ?", (base_name, row[0]))
    updated += 1

conn.commit()
print(f"Обновлено {updated} товаров.")