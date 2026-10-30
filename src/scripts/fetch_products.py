"""
Загрузка списка товаров (offer_id) для магазина.
Запуск: python -m src.scripts.fetch_products <platform> <store_code>
Пример: python -m src.scripts.fetch_products ozon limited_games
"""
import json
import sys
from datetime import datetime
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient


def fetch_all_products(client: OzonClient) -> list[dict]:
    items = []
    last_id = ""
    while True:
        payload = {"filter": {"visibility": "ALL"}, "last_id": last_id, "limit": 1000}
        data = client.post("/v3/product/list", payload)
        result = data.get("result", {})
        batch = result.get("items", [])
        items.extend(batch)
        last_id = result.get("last_id", "")
        if not batch or not last_id:
            break
    return items


def main():
    if len(sys.argv) < 3:
        print("Использование: python -m src.scripts.fetch_products <platform> <store_code>")
        print("Пример: python -m src.scripts.fetch_products ozon limited_games")
        sys.exit(1)
    
    platform = sys.argv[1]
    store_code = sys.argv[2]
    
    store = get_store(platform, store_code)
    client = OzonClient(store)

    print(f"Загрузка товаров: {store.name} (Площадка: {platform}, Client-Id: {store.store_id})")
    items = fetch_all_products(client)
    print(f"Получено товаров: {len(items)}")

    # Сохраняем в файл
    settings.data_api_raw.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = settings.data_api_raw / f"{platform}_{store_code}_product_list_{stamp}.json"
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранено: {out}")

    # Обновляем базу
    with get_conn() as conn:
        store_row = conn.execute(
            "SELECT id FROM store WHERE code = ?", (store_code,)
        ).fetchone()
        if not store_row:
            print(f"Магазин {store_code} не найден в БД")
            return
        store_id = store_row["id"]
        
        inserted = 0
        for item in items:
            offer_id = item.get("offer_id")
            if not offer_id:
                continue
            
            # Проверяем, есть ли уже такой товар
            prod = conn.execute("SELECT id FROM product WHERE offer_id = ?", (offer_id,)).fetchone()
            if not prod:
                # Создаём черновик с offer_id (название обновим позже)
                cur = conn.execute(
                    """INSERT INTO product (offer_id, name, baseGameName, is_active) 
                       VALUES (?, ?, ?, 1)""",
                    (offer_id, f"Товар {offer_id}", f"Товар {offer_id}")
                )
                product_id = cur.lastrowid
            else:
                product_id = prod["id"]
            
            # Привязываем к магазину в listing
            conn.execute(
                """INSERT OR IGNORE INTO listing (store_id, product_id, warehouse_id, status) 
                   VALUES (?, ?, 1, 'draft')""",
                (store_id, product_id)
            )
            inserted += 1
        conn.commit()
        print(f"Записано листингов в БД: {inserted}")
        
        # --- ЗАПРАШИВАЕМ НАЗВАНИЯ ИЗ OZON ---
        print("Запрос названий товаров...")
        offer_ids = [item["offer_id"] for item in items if item.get("offer_id")]
        
        # OZON разрешает до 1000 offer_id за раз
        for i in range(0, len(offer_ids), 1000):
            batch = offer_ids[i:i+1000]
            payload = {"offer_id": batch, "product_id": [], "sku": []}
            try:
                data = client.post("/v3/product/info/list", payload)
                details = data.get("items", [])
                
                for d in details:
                    oid = d.get("offer_id")
                    real_name = d.get("name")
                    if oid and real_name:
                        conn.execute(
                            "UPDATE product SET name = ?, baseGameName = ? WHERE offer_id = ?",
                            (real_name, real_name, oid)
                        )
                conn.commit()
            except Exception as e:
                print(f"Ошибка при запросе названий: {e}")
        
        print("Названия обновлены.")


if __name__ == "__main__":
    main()