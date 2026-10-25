"""
Детализация товаров: цены + остатки (FBS + FBO).
Запуск: python -m src.scripts.fetch_product_details
"""
import json
from datetime import datetime
from src.config import settings, get_store
from src.db import get_conn
from src.ozon_client import OzonClient


STORE_CODE = "limited_games"
WAREHOUSE_CODE = "main_warehouse"
BATCH_SIZE = 1000


def _save_raw(name: str, data: dict | list) -> None:
    settings.data_api_raw.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = settings.data_api_raw / f"{STORE_CODE}_{name}_{stamp}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  сохранено: {path.name}")


def fetch_prices(client: OzonClient, offer_ids: list[str]) -> list[dict]:
    items: list[dict] = []
    
    # Фильтруем: Ozon не принимает offer_id длиннее 100 символов
    valid_offer_ids = []
    too_long = []
    for oid in offer_ids:
        if len(str(oid)) <= 100:
            valid_offer_ids.append(oid)
        else:
            too_long.append(oid)
    
    if too_long:
        print(f"  ⚠️ Пропущено {len(too_long)} артикулов длиннее 100 символов:")
        for oid in too_long[:5]:  # покажем первые 5 для примера
            print(f"     - {oid[:80]}... (длина {len(oid)})")
    
    for i in range(0, len(valid_offer_ids), BATCH_SIZE):
        batch = valid_offer_ids[i : i + BATCH_SIZE]
        payload = {
            "filter": {"offer_id": batch},
            "limit": BATCH_SIZE,
            "cursor": ""
        }
        data = client.post("/v5/product/info/prices", payload)
        items.extend(data.get("items", []))
        
        cursor = data.get("cursor", "")
        while cursor:
            payload["cursor"] = cursor
            data = client.post("/v5/product/info/prices", payload)
            items.extend(data.get("items", []))
            cursor = data.get("cursor", "")
    
    return items

def fetch_stocks_fbs(client: OzonClient, offer_ids: list[str]) -> list[dict]:
    """
    FBS: /v4/product/info/stocks — возвращает плоский список: {offer_id, type, present, reserved}
    """
    valid_offer_ids = [oid for oid in offer_ids if len(str(oid)) <= 100]
    too_long = [oid for oid in offer_ids if len(str(oid)) > 100]
    if too_long:
        print(f"  ⚠️ Пропущено {len(too_long)} артикулов длиннее 100 символов (FBS)")

    flat_items: list[dict] = []
    for i in range(0, len(valid_offer_ids), BATCH_SIZE):
        batch = valid_offer_ids[i : i + BATCH_SIZE]
        payload = {
            "filter": {"offer_id": batch, "visibility": "ALL"},
            "limit": BATCH_SIZE,
            "last_id": ""
        }
        data = client.post("/v4/product/info/stocks", payload)
        result = data.get("result", {})

        for item in result.get("items", []):
            oid = item.get("offer_id")
            if not oid:
                continue
            for stock in item.get("stocks", []):
                flat_items.append({
                    "offer_id": oid,
                    "type": stock.get("type"),      # "fbs" или "fbo"
                    "present": stock.get("present", 0),
                    "reserved": stock.get("reserved", 0),
                })

        last_id = result.get("last_id", "")
        while last_id:
            payload["last_id"] = last_id
            data = client.post("/v4/product/info/stocks", payload)
            result = data.get("result", {})
            for item in result.get("items", []):
                oid = item.get("offer_id")
                if not oid:
                    continue
                for stock in item.get("stocks", []):
                    flat_items.append({
                        "offer_id": oid,
                        "type": stock.get("type"),
                        "present": stock.get("present", 0),
                        "reserved": stock.get("reserved", 0),
                    })
            last_id = result.get("last_id", "")

    return flat_items



def fetch_stocks_fbo(client: OzonClient, offer_ids: list[str]) -> list[dict]:
    """FBO: /v2/analytics/stock_on_warehouses (аналитический отчёт по складам Ozon)"""
    # Этот метод работает по всему кабинету, фильтр по offer_id — на нашей стороне.
    payload = {"limit": 1000, "offset": 0}
    rows: list[dict] = []
    while True:
        data = client.post("/v2/analytics/stock_on_warehouses", payload)
        batch = data.get("rows", []) or data.get("result", {}).get("rows", [])
        rows.extend(batch)
        if len(batch) < payload["limit"]:
            break
        payload["offset"] += payload["limit"]
    wanted = set(offer_ids)
    return [r for r in rows if str(r.get("offer_id", "")) in wanted]


def main() -> None:
    store = get_store(STORE_CODE)
    client = OzonClient(store)

    with get_conn() as conn:
        store_row = conn.execute(
            "SELECT id FROM store WHERE code=?", (store.code,)
        ).fetchone()
        if not store_row:
            raise SystemExit("Магазин не найден в БД. Сначала seed.py")
        store_id = store_row["id"]

        wh_row = conn.execute(
            "SELECT id FROM warehouse WHERE code=?", (WAREHOUSE_CODE,)
        ).fetchone()
        if not wh_row:
            raise SystemExit("Склад не найден в БД. Сначала seed.py")
        wh_id = wh_row["id"]

        offer_ids = [
            r["offer_id"]
            for r in conn.execute(
                "SELECT offer_id FROM product ORDER BY offer_id"
            ).fetchall()
        ]

    if not offer_ids:
        raise SystemExit("Нет товаров в product. Сначала import_xlsx.py")

    print(f"Товаров для обновления: {len(offer_ids)}")

    # ---------- Цены ----------
    print("\n[1/3] Цены (/v5/product/info/prices)")
    prices = fetch_prices(client, offer_ids)
    _save_raw("prices", prices)
    print(f"  получено: {len(prices)}")

    # ---------- Остатки FBS ----------
    print("\n[2/3] Остатки FBS (/v4/product/info/stocks)")
    stocks_fbs = fetch_stocks_fbs(client, offer_ids)
    _save_raw("stocks_fbs", stocks_fbs)
    print(f"  получено: {len(stocks_fbs)}")

    # ---------- Остатки FBO ----------
    print("\n[3/3] Остатки FBO (/v2/analytics/stock_on_warehouses)")
    stocks_fbo = fetch_stocks_fbo(client, offer_ids)
    _save_raw("stocks_fbo", stocks_fbo)
    print(f"  получено: {len(stocks_fbo)}")

    # ---------- Запись в БД ----------
    print("\nЗапись в БД...")
    price_map = {p["offer_id"]: p for p in prices if p.get("offer_id")}

    # FBS: суммируем present по всем складам внутри каждого товара
    fbs_qty: dict[str, int] = {}
    for s in stocks_fbs:
        oid = s.get("offer_id")
        if not oid:
            continue
        
        fbs_qty[oid] = fbs_qty.get(oid, 0) + int(s.get("present", 0))

    # FBO: аналогично, если есть
    fbo_qty: dict[str, int] = {}
    for s in stocks_fbo:
        oid = s.get("offer_id")
        if not oid:
            continue
        qty = s.get("free_to_sell_amount") or s.get("present") or 0
        fbo_qty[oid] = fbo_qty.get(oid, 0) + int(qty)

    updated_listings = 0
    updated_stocks = 0

    with get_conn() as conn:
        for oid in offer_ids:
            # listing: цена
            p = price_map.get(oid)
            if p:
                price_info = p.get("price", {})
                new_price = float(price_info.get("price", 0) or 0)
                new_old = float(price_info.get("old_price", 0) or 0)
                vat = str(price_info.get("vat", "") or "")
                conn.execute(
                    """UPDATE listing
                       SET price=?, old_price=?, vat=?, status='active'
                       WHERE store_id=? AND product_id=(
                           SELECT id FROM product WHERE offer_id=?
                       )""",
                    (new_price, new_old, vat, store_id, oid),
                )
                if conn.total_changes:
                    updated_listings += 1

            # stock: сумма FBS + FBO
            total_qty = fbs_qty.get(oid, 0) + fbo_qty.get(oid, 0)
            conn.execute(
                """INSERT INTO stock(warehouse_id, product_id, quantity)
                   VALUES(?, (SELECT id FROM product WHERE offer_id=?), ?)
                   ON CONFLICT(warehouse_id, product_id) DO UPDATE SET
                       quantity=excluded.quantity,
                       updated_at=datetime('now')""",
                (wh_id, oid, total_qty),
            )
            updated_stocks += 1

        conn.commit()

    print(f"\nОбновлено листингов (цены): {updated_listings}")
    print(f"Обновлено остатков (FBS+FBO): {updated_stocks}")

    # ---------- Сводка ----------
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM product").fetchone()["c"]
        with_price = conn.execute(
            "SELECT COUNT(*) c FROM listing WHERE price IS NOT NULL AND price > 0"
        ).fetchone()["c"]
        with_stock = conn.execute(
            "SELECT COUNT(*) c FROM stock WHERE quantity > 0"
        ).fetchone()["c"]
        sum_fbs = sum(fbs_qty.values())
        sum_fbo = sum(fbo_qty.values())

    print(f"\nВсего товаров: {total}")
    print(f"С ценой > 0: {with_price}")
    print(f"С остатком > 0: {with_stock}")
    print(f"Суммарный остаток FBS: {sum_fbs}")
    print(f"Суммарный остаток FBO: {sum_fbo}")


if __name__ == "__main__":
    main()