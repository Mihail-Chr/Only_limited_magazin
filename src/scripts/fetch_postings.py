"""
Загрузка отправлений FBS через /v4/posting/fbs/list.
Запуск: python -m src.scripts.fetch_postings
"""
import json
from datetime import datetime, timedelta
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient

STORE_CODE = "limited_games"
DAYS_BACK = 30


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
            "limit": 100,
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
    store = get_store(STORE_CODE)
    client = OzonClient(store)

    to_dt = datetime.now()
    since_dt = to_dt - timedelta(days=DAYS_BACK)
    since = since_dt.strftime("%Y-%m-%dT00:00:00Z")
    to = to_dt.strftime("%Y-%m-%dT23:59:59Z")

    print(f"Магазин: {store.name}")
    print(f"Период: {since} — {to}")

    postings = fetch_postings(client, since, to)
    print(f"Получено отправлений: {len(postings)}")

    settings.data_api_raw.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = settings.data_api_raw / f"{STORE_CODE}_postings_{stamp}.json"
    raw_path.write_text(json.dumps(postings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранено: {raw_path.name}")

    with get_conn() as conn:
        store_row = conn.execute(
            "SELECT id FROM store WHERE code=?", (store.code,)
        ).fetchone()
        store_id = store_row["id"]

        inserted = 0
        for p in postings:
            posting_number = p.get("posting_number")
            if not posting_number:
                continue

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
                    raw_json=excluded.raw_json,
                    fetched_at=datetime('now')""",
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

            conn.execute("DELETE FROM posting_item WHERE posting_id=?", (posting_id,))

            for prod in p.get("products", []):
                                # --- Безопасный разбор цены ---
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
                # -------------------------------

                # --- НОВОЕ: себестоимость на момент продажи ---
                cost_at_sale = round(price_val * 0.3, 2)  # дисконт 70% => себестоимость 30%
                # ---------------------------------------------

                conn.execute(
                    """INSERT INTO posting_item(
                        posting_id, product_id, offer_id, sku, name, quantity, price, currency, cost_price_at_sale
                    ) VALUES(?,?,?,?,?,?,?,?,?)""",
                    (
                        posting_id,
                        product_row["id"] if product_row else None,
                        offer_id,
                        str(prod.get("sku", "") or ""),
                        prod.get("name"),
                        int(prod.get("quantity", 0) or 0),
                        price_val,
                        currency_val,
                        cost_at_sale,   # <-- добавили сюда
                    ),
                )
            inserted += 1

        conn.commit()
        print(f"Записано отправлений в БД: {inserted}")

    # Сводка: сколько единиц товара «в пути» по каждому offer_id
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