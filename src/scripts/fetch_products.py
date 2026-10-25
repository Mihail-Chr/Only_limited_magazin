import json
from datetime import datetime
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient


STORE_CODE = "limited_games"


def fetch_all_products(client: OzonClient) -> list[dict]:
    items: list[dict] = []
    last_id = ""
    while True:
        payload = {
            "filter": {"visibility": "ALL"},
            "last_id": last_id,
            "limit": 1000,
        }
        data = client.post("/v3/product/list", payload)
        result = data.get("result", {})
        batch = result.get("items", [])
        items.extend(batch)
        last_id = result.get("last_id", "")
        if not batch or not last_id:
            break
    return items


def main() -> None:
    store = get_store(STORE_CODE)
    client = OzonClient(store)

    print(f"Магазин: {store.name} (Client-Id {store.client_id})")
    items = fetch_all_products(client)
    print(f"Получено товаров: {len(items)}")

    settings.data_api_raw.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = settings.data_api_raw / f"{STORE_CODE}_product_list_{stamp}.json"
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранено: {out}")

    # Сверяем с БД: сколько из них уже есть в product по offer_id
    with get_conn() as conn:
        rows = conn.execute("SELECT offer_id FROM product").fetchall()
        known = {r["offer_id"] for r in rows}
    api_offer_ids = {i.get("offer_id") for i in items if i.get("offer_id")}
    missing_in_db = api_offer_ids - known
    only_in_db = known - api_offer_ids
    print(f"Есть в API, нет в БД: {len(missing_in_db)}")
    print(f"Есть в БД, нет в API: {len(only_in_db)}")
    print("Пример из API:", json.dumps(items[0], ensure_ascii=False) if items else "—")


if __name__ == "__main__":
    main()