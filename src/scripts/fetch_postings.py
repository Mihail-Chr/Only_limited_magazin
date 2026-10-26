"""
Загрузка отправлений FBS через /v4/posting/fbs/list.
Запуск: python -m src.scripts.fetch_postings <store_code> <since> <to>
Пример: python -m src.scripts.fetch_postings limited_games 2022-01-01 2022-12-31
"""
import json
import sys
from datetime import datetime
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient

BATCH_SIZE = 100

def fetch_postings(client: OzonClient, since: str, to: str) -> list[dict]:
    """Курсорная пагинация v4: has_next + cursor."""
    all_postings: list[dict] = []
    cursor = ""
    while True:
        payload = {
            "dir": "ASC",
            "filter": {
                "since": since,
                "to": to,
                "status": "",
            },
            "limit": BATCH_SIZE,
            "cursor": cursor,
            "with": {
                "analytics_data": False,
                "barcodes": False,
                "financial_data": False,
                "product_exemplars": False,
                "translit": False,
            },
        }
        data = client.post("/v4/posting/fbs/list", payload)
        postings = data.get("postings", [])
        all_postings.extend(postings)
        
        has_next = data.get("has_next", False)
        cursor = data.get("cursor", "")
        
        if not has_next or not cursor:
            break
            
    return all_postings

def main() -> None:
    if len(sys.argv) < 4:
        print("Использование: python -m src.scripts.fetch_postings <store_code> <since> <to>")
        print("Пример: python -m src.scripts.fetch_postings limited_games 2022-01-01 2022-12-31")
        sys.exit(1)
    
    store_code = sys.argv[1]
    since_date = sys.argv[2]
    to_date = sys.argv[3]
    
    # Формат OZON
    since = f"{since_date}T00:00:00Z"
    to = f"{to_date}T23:59:59Z"
    
    store = get_store(store_code)
    client = OzonClient(store)

    print(f"Магазин: {store.name}")
    print(f"Период: {since} — {to}")

    postings = fetch_postings(client, since, to)
    print(f"Получено отправлений: {len(postings)}")

    # Сохраняем сырой JSON (для отладки)
    settings.data_api_raw.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = settings.data_api_raw / f"{store_code}_postings_{since_date}_{stamp}.json"
    raw_path.write_text(json.dumps(postings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранено: {raw_path.name}")

    # Запись в БД
    with get_conn() as conn:
        store_row = conn.execute(
            "SELECT id FROM store WHERE code=?", (store.code,)
        ).fetchone()
        if not store_row:
            raise SystemExit(f"Магазин {store_code} не найден в БД")
        store_id = store_row["id"]

        inserted = 0
        for p in postings:
            posting_number = p.get("posting_number")
            if not posting_number:
                continue

            # Вставляем или обновляем отправление
            conn.execute(
                """INSERT INTO posting(
                    posting_number, order_id, store_id, status, substatus,
                    created_at, in_process_at, shipment_date, delivering_date,
                    tracking_number, raw_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(posting_number) DO UPDATE SET
                    status=excluded.status,
                    substatus=excluded.substatus,
                    shipment_date=excluded.shipment_date,
                    delivering_date=excluded.delivering_date,
                    tracking_number=excluded.tracking_number,
                    raw_json=excluded.raw_json""",
                (
                    posting_number,
                    p.get("order_id"),
                    store_id,
                    p.get("status"),
                    p.get("substatus"),
                    p.get("created_at"),
                    p.get("in_process_at"),
                    p.get("shipment_date"),
                    p.get("delivering_date"),
                    p.get("tracking_number"),
                    json.dumps(p, ensure_ascii=False),
                ),
            )
            
            posting_id = conn.execute(
                "SELECT id FROM posting WHERE posting_number=?", (posting_number,)
            ).fetchone()["id"]

            # Удаляем старые позиции, чтобы не дублировать
            conn.execute("DELETE FROM posting_item WHERE posting_id=?", (posting_id,))

            # Вставляем новые позиции
            for prod in p.get("products", []):
                offer_id = prod.get("offer_id")
                
                # Ищем product_id по offer_id (если товар есть в нашей базе)
                product_row = conn.execute(
                    "SELECT id FROM product WHERE offer_id=?", (offer_id,)
                ).fetchone()
                product_id = product_row["id"] if product_row else None

                # Безопасный разбор цены (OZON может отдавать dict или число)
                raw_price = prod.get("price", 0)
                if isinstance(raw_price, dict):
                    price_val = float(raw_price.get("amount", 0) or 0)
                    currency_val = raw_price.get("currency", "RUB")
                else:
                    try:
                        price_val = float(raw_price or 0)
                    except (ValueError, TypeError):
                        price_val = 0.0
                    currency_val = prod.get("currency_code", "RUB")

                # Искусственная себестоимость (30% от цены)
                cost_at_sale = round(price_val * 0.3, 2)

                # --- ОБНОВЛЯЕМ НАЗВАНИЕ ТОВАРА В PRODUCT, ЕСЛИ ОНО ЗАГЛУШКА ---
                product_name = prod.get("name", "")
                if product_id and product_name:
                    current_prod = conn.execute("SELECT name FROM product WHERE id = ?", (product_id,)).fetchone()
                    if current_prod and current_prod["name"] == "Новый товар (ожидает заполнения)":
                        conn.execute("UPDATE product SET name = ?, baseGameName = ? WHERE id = ?", (product_name, product_name, product_id))
                # -----------------------------------------------------------------


                conn.execute(
                    """INSERT INTO posting_item(
                        posting_id, product_id, offer_id, sku, name, quantity, price, currency, cost_price_at_sale
                    ) VALUES(?,?,?,?,?,?,?,?,?)""",
                    (
                        posting_id,
                        product_id,
                        offer_id,
                        str(prod.get("sku", "") or ""),
                        prod.get("name"),
                        int(prod.get("quantity", 0) or 0),
                        price_val,
                        currency_val,
                        cost_at_sale,
                    ),
                )
            inserted += 1

        conn.commit()
        print(f"Записано отправлений в БД: {inserted}")

    # Сводка: сколько единиц товара «в пути»
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT pi.offer_id, SUM(pi.quantity) AS qty
               FROM posting_item pi
               JOIN posting p ON p.id = pi.posting_id
               WHERE p.status NOT IN ('delivered', 'cancelled')
               GROUP BY pi.offer_id
               ORDER BY qty DESC
               LIMIT 20"""
        ).fetchall()

    print("\nТоп-20 товаров «в пути» (не доставлены и не отменены):")
    for r in rows:
        print(f"  {r['offer_id']}: {r['qty']} шт.")

if __name__ == "__main__":
    main()