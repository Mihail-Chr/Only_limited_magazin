"""
Загрузка истории отправлений (продаж) для магазина.
Запуск: python -m src.scripts.fetch_postings <platform> <store_code> <since> <to>
Пример: python -m src.scripts.fetch_postings ozon limited_games 2026-01-01 2026-12-31
"""
import json
import sys
from datetime import datetime
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient

BATCH_SIZE = 100


def fetch_postings(client: OzonClient, since: str, to: str) -> list[dict]:
    all_postings = []
    cursor = ""
    while True:
        payload = {
            "dir": "ASC",
            "filter": {"since": since, "to": to, "status": ""},
            "limit": BATCH_SIZE,
            "cursor": cursor,
            "with": {
                "analytics_data": False,
                "barcodes": False,
                "financial_data": False,
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


def main():
    if len(sys.argv) < 5:
        print("Использование: python -m src.scripts.fetch_postings <platform> <store_code> <since> <to>")
        print("Пример: python -m src.scripts.fetch_postings ozon limited_games 2026-01-01 2026-12-31")
        sys.exit(1)
    
    platform = sys.argv[1]
    store_code = sys.argv[2]
    since_date = sys.argv[3]
    to_date = sys.argv[4]
    
    since = f"{since_date}T00:00:00Z"
    to = f"{to_date}T23:59:59Z"
    
    store = get_store(platform, store_code)
    client = OzonClient(store)

    print(f"Магазин: {store.name}")
    print(f"Период: {since} — {to}")

    postings = fetch_postings(client, since, to)
    print(f"Получено отправлений: {len(postings)}")

    # Сохраняем сырой JSON
    settings.data_api_raw.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = settings.data_api_raw / f"{platform}_{store_code}_postings_{since_date}_{stamp}.json"
    raw_path.write_text(json.dumps(postings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранено: {raw_path.name}")

    # Запись в БД
    with get_conn() as conn:
        store_row = conn.execute(
            "SELECT id FROM store WHERE code = ?", (store_code,)
        ).fetchone()
        if not store_row:
            print(f"Магазин {store_code} не найден в БД")
            return
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

            # Удаляем старые позиции
            conn.execute("DELETE FROM posting_item WHERE posting_id=?", (posting_id,))

            # Вставляем новые позиции
            for prod in p.get("products", []):
                offer_id = prod.get("offer_id")
                product_row = conn.execute(
                    "SELECT id FROM product WHERE offer_id=?", (offer_id,)
                ).fetchone()
                product_id = product_row["id"] if product_row else None

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

                cost_at_sale = round(price_val * 0.3, 2)

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


if __name__ == "__main__":
    main()