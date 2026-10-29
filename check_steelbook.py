import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')
conn.row_factory = sqlite3.Row

# Ищем товары, в названии или baseGameName которых есть "Steelbook"
rows = conn.execute("""
    SELECT id, offer_id, name, baseGameName, product_type, platform, edition
    FROM product
    WHERE name LIKE '%Steelbook%' 
       OR baseGameName LIKE '%Steelbook%'
    ORDER BY id
    LIMIT 20
""").fetchall()

print(f"Найдено товаров со словом 'Steelbook': {len(rows)}")
print()
for r in rows:
    print(f"ID: {r['id']}")
    print(f"  offer_id: {r['offer_id']}")
    print(f"  name: {r['name']}")
    print(f"  baseGameName: {r['baseGameName']}")
    print(f"  type: {r['product_type']}, platform: {r['platform']}, edition: {r['edition']}")
    print()