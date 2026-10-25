"""
Загрузка истории заказов FBS по годам (с 2022 по текущий).
Запуск: python -m src.scripts.fetch_history
"""
import json
from datetime import datetime
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient

STORE_CODE = "limited_games"
START_YEAR = 2022


def fetch_postings_for_year(client: OzonClient, since: str, to: str) -> list[dict]:
    """Курсорная пагинация v4: has_next + cursor."""
    all_postings: list[dict] = []
    cursor = ""
    while True:
        payload = {
            "dir": "ASC",
            "filter": {"since": since, "to": to, "status": ""},
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


def save_postings_to_db(store_id: int, postings: list[dict]) -> int:
    """Сохраняет список отправлений в БД. Возвращает количество обработанных."""
    inserted = 0
    with get_conn() as conn:
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
                offer_id = prod.get("offer_id")
                product_row = conn.execute(
                    "SELECT id FROM product WHERE offer_id=?", (offer_id,)
                ).fetchone() if offer_id else None

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

                conn.execute(
                    """INSERT INTO posting_item(
                        posting_id, product_id, offer_id, sku, name, quantity, price, currency
                    ) VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        posting_id,
                        product_row["id"] if product_row else None,
                        offer_id,
                        str(prod.get("sku", "") or ""),
                        prod.get("name"),
                        int(prod.get("quantity", 0) or 0),
                        price_val,
                        currency_val,
                    ),
                )
            inserted += 1
        conn.commit()
    return inserted


def main() -> None:
    store = get_store(STORE_CODE)
    client = OzonClient(store)

    with get_conn() as conn:
        store_row = conn.execute(
            "SELECT id FROM store WHERE code=?", (store.code,)
        ).fetchone()
        store_id = store_row["id"]

    current_year = datetime.now().year
    total_all_years = 0

    for year in range(START_YEAR, current_year + 1):
        since = f"{year}-01-01T00:00:00Z"
        if year == current_year:
            to = datetime.now().strftime("%Y-%m-%dT23:59:59Z")
        else:
            to = f"{year}-12-31T23:59:59Z"

        print(f"\n=== Загрузка за {year} год ===")
        try:
            postings = fetch_postings_for_year(client, since, to)
            print(f"  Найдено отправлений: {len(postings)}")
            
            # Сохраняем сырой JSON (для аудита)
            if postings:
                settings.data_api_raw.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                raw_path = settings.data_api_raw / f"{STORE_CODE}_postings_{year}_{stamp}.json"
                raw_path.write_text(json.dumps(postings, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  Сырые данные: {raw_path.name}")
            
            # Сохраняем в БД
            saved = save_postings_to_db(store_id, postings)
            print(f"  Записано в БД: {saved}")
            total_all_years += saved
            
        except Exception as e:
            print(f"  Ошибка при загрузке за {year} год: {e}")
            print("  Пропускаем этот год...")

    print(f"\n=== ИТОГО ===")
    print(f"Всего загружено и обновлено отправлений: {total_all_years}")


if __name__ == "__main__":
    main()