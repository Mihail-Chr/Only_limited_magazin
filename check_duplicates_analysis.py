import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')
conn.row_factory = sqlite3.Row

# Берем первые 5 групп дублей (по названию + платформе)
duplicates = conn.execute("""
    SELECT 
        baseGameName, 
        platform, 
        COUNT(*) as cnt,
        GROUP_CONCAT(id) as ids
    FROM product
    WHERE baseGameName IS NOT NULL 
      AND baseGameName != ''
      AND platform IS NOT NULL
    GROUP BY baseGameName, platform
    HAVING cnt > 1
    ORDER BY cnt DESC
    LIMIT 5
""").fetchall()

for d in duplicates:
    print(f"\n{'='*60}")
    print(f"ГРУППА: {d['baseGameName']} ({d['platform']}) — {d['cnt']} шт.")
    print(f"ID: {d['ids']}")
    print(f"{'='*60}")
    
    ids = [int(x) for x in d['ids'].split(',')]
    
    for product_id in ids:
        print(f"\n  --- Товар ID: {product_id} ---")
        
        prod = conn.execute("SELECT * FROM product WHERE id = ?", (product_id,)).fetchone()
        if prod:
            print(f"    name: {prod['name']}")
            print(f"    offer_id: {prod['offer_id']}")
        
        # Листинги
        listings = conn.execute("""
            SELECT s.name AS store_name, l.price, l.status 
            FROM listing l
            JOIN store s ON s.id = l.store_id
            WHERE l.product_id = ?
        """, (product_id,)).fetchall()
        print(f"    Листинги ({len(listings)}):")
        for l in listings:
            print(f"      - {l['store_name']}: {l['price']} ({l['status']})")
        
        # Продажи
        sales = conn.execute("""
            SELECT COUNT(*) as cnt, SUM(quantity) as total_qty
            FROM posting_item
            WHERE product_id = ?
        """, (product_id,)).fetchone()
        print(f"    Продажи: {sales['cnt']} раз, {sales['total_qty'] or 0} шт.")
        
        # Остаток
        stock = conn.execute("""
            SELECT quantity FROM stock_manual WHERE product_id = ?
        """, (product_id,)).fetchone()
        print(f"    Остаток: {stock['quantity'] if stock else 0} шт.")