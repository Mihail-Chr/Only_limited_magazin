import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')
conn.row_factory = sqlite3.Row

# Считаем, сколько заглушек было до удаления
before_count = conn.execute("SELECT COUNT(*) FROM product WHERE name = 'Новый товар (ожидает заполнения)'").fetchone()[0]
print(f"Заглушек до удаления: {before_count}")

# Ищем товары-заглушки
stubs = conn.execute("""
    SELECT id FROM product 
    WHERE name = 'Новый товар (ожидает заполнения)'
""").fetchall()

skipped = 0

for stub in stubs:
    product_id = stub['id']
    
    # Проверяем, есть ли на этот товар ссылки в заказах (posting_item)
    has_postings = conn.execute(
        "SELECT COUNT(*) FROM posting_item WHERE product_id = ?", (product_id,)
    ).fetchone()[0]
    
    # Если товар продавался — удалять нельзя, пропускаем
    if has_postings > 0:
        skipped += 1
        continue
    
    # Если товар не продавался — удаляем его из listing и из product
    conn.execute("DELETE FROM listing WHERE product_id = ?", (product_id,))
    conn.execute("DELETE FROM product WHERE id = ?", (product_id,))

conn.commit()

# Считаем, сколько заглушек осталось после удаления
after_count = conn.execute("SELECT COUNT(*) FROM product WHERE name = 'Новый товар (ожидает заполнения)'").fetchone()[0]
deleted_count = before_count - after_count

print(f"Заглушек после удаления: {after_count}")
print(f"Удалено (по разнице): {deleted_count}")
print(f"Пропущено (есть ссылки в заказах): {skipped}")