import json
import sys
from datetime import datetime
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient

BATCH_SIZE = 1000

def fetch_prices(client, offer_ids):
    items = []
    for i in range(0, len(offer_ids), BATCH_SIZE):
        batch = offer_ids[i:i+BATCH_SIZE]
        payload = {"filter": {"offer_id": batch}, "limit": BATCH_SIZE, "cursor": ""}
        try:
            data = client.post("/v5/product/info/prices", payload)
            items.extend(data.get("items", []))
        except Exception as e:
            print(f"Ошибка при загрузке цен: {e}")
    return items

def main():
    if len(sys.argv) < 2:
        print("Использование: python -m src.scripts.fetch_product_details <store_code>")
        sys.exit(1)
    
    store_code = sys.argv[1]
    store = get_store(store_code)
    client = OzonClient(store)

    with get_conn() as conn:
        store_row = conn.execute("SELECT id FROM store WHERE code = ?", (store_code,)).fetchone()
        if not store_row:
            print(f"Магазин {store_code} не найден")
            return
        store_id = store_row["id"]
        
        # Берем offer_id всех товаров этого магазина
        rows = conn.execute("""
            SELECT p.offer_id 
            FROM listing l
            JOIN product p ON p.id = l.product_id
            WHERE l.store_id = ?
        """, (store_id,)).fetchall()
        offer_ids = [r["offer_id"] for r in rows]

    print(f"Обновление цен и остатков для {len(offer_ids)} товаров магазина {store.name}...")
    
    prices = fetch_prices(client, offer_ids)
    print(f"Получено цен: {len(prices)}")

    # Обновляем базу
    with get_conn() as conn:
        updated = 0
        for p in prices:
            offer_id = p.get("offer_id")
            if not offer_id: continue
            
            price_val = p.get("price", {}).get("price", 0) if isinstance(p.get("price"), dict) else p.get("price", 0)
            
            conn.execute("""
                UPDATE listing 
                SET price = ?, status = 'active'
                WHERE store_id = ? AND product_id = (SELECT id FROM product WHERE offer_id = ?)
            """, (float(price_val), store_id, offer_id))
            updated += 1
        conn.commit()
        print(f"Обновлено листингов: {updated}")

if __name__ == "__main__":
    main()