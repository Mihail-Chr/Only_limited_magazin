"""
Загрузка цен и остатков для магазина.
Запуск: python -m src.scripts.fetch_product_details <platform> <store_code>
Пример: python -m src.scripts.fetch_product_details ozon limited_games
"""
import json
import sys
from datetime import datetime
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient


def fetch_prices(client: OzonClient, offer_ids: list[str]) -> list[dict]:
    items = []
    valid_offer_ids = [oid for oid in offer_ids if len(str(oid)) <= 100]
    
    for i in range(0, len(valid_offer_ids), 1000):
        batch = valid_offer_ids[i:i+1000]
        payload = {"filter": {"offer_id": batch}, "limit": 1000, "cursor": ""}
        data = client.post("/v5/product/info/prices", payload)
        items.extend(data.get("items", []))
    
    return items


def main():
    if len(sys.argv) < 3:
        print("Использование: python -m src.scripts.fetch_product_details <platform> <store_code>")
        print("Пример: python -m src.scripts.fetch_product_details ozon limited_games")
        sys.exit(1)
    
    platform = sys.argv[1]
    store_code = sys.argv[2]
    
    store = get_store(platform, store_code)
    client = OzonClient(store)

    with get_conn() as conn:
        store_row = conn.execute(
            "SELECT id FROM store WHERE code = ?", (store_code,)
        ).fetchone()
        if not store_row:
            print(f"Магазин {store_code} не найден в БД")
            return
        store_id = store_row["id"]
        
        # Берем все offer_id этого магазина
        rows = conn.execute("""
            SELECT p.offer_id 
            FROM listing l
            JOIN product p ON p.id = l.product_id
            WHERE l.store_id = ?
        """, (store_id,)).fetchall()
        offer_ids = [r["offer_id"] for r in rows]

    print(f"Обновление цен для {len(offer_ids)} товаров магазина {store.name}...")
    prices = fetch_prices(client, offer_ids)
    print(f"Получено цен: {len(prices)}")

    # Обновляем базу
    with get_conn() as conn:
        updated = 0
        for p in prices:
            offer_id = p.get("offer_id")
            if not offer_id:
                continue
            
            price_info = p.get("price", {})
            new_price = float(price_info.get("price", 0) or 0)
            new_old = float(price_info.get("old_price", 0) or 0)
            
            conn.execute("""
                UPDATE listing 
                SET price = ?, old_price = ?, status = 'active'
                WHERE store_id = ? AND product_id = (
                    SELECT id FROM product WHERE offer_id = ?
                )
            """, (new_price, new_old, store_id, offer_id))
            updated += 1
        conn.commit()
        print(f"Обновлено листингов: {updated}")


if __name__ == "__main__":
    main()