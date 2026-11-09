"""
fetch_postings.py — универсальная загрузка отправлений (продаж) с площадки (v3.1).

Использование:
    from src.scripts.fetch_postings import fetch_postings
    result = fetch_postings("ozon", "limited_games", "2026-01-01", "2026-11-08")

    # Или CLI:
    python -m src.scripts.fetch_postings ozon limited_games 2026-01-01 2026-11-08

Что делает:
- Читает stores (магазин), .env (ключи).
- Создаёт клиент площадки (OzonClient, YmClient, ...).
- Загружает отправления (get_postings).
- Сохраняет сырой JSON в data/api_raw/.
- Создаёт salesOrders, salesOrderItems, salesOrderStatusHistory.
- Возвращает dict: {ok, inserted, errors}.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Корень проекта (для запуска из src/scripts/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db import get_conn


# Каталог для сырых JSON (можно переопределить в тестах)
DATA_API_RAW = Path("data/api_raw")


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ
# =====================================================================

def _read_env(platform: str, store_code: str) -> tuple[str | None, str | None]:
    """Читает ключи API из .env (префикс площадки). Обрезает пробелы/кавычки."""
    prefix = platform.upper()
    store_upper = store_code.upper()

    client_id = os.getenv(f"{prefix}_{store_upper}_CLIENT_ID")
    api_key = os.getenv(f"{prefix}_{store_upper}_API_KEY")

    if client_id:
        client_id = client_id.strip().strip('"').strip("'")
    if api_key:
        api_key = api_key.strip().strip('"').strip("'")

    return client_id or None, api_key or None


def _create_client(platform: str, client_id: str, api_key: str):
    """Создаёт клиент площадки (OzonClient, YmClient, ...)."""
    if platform == "ozon":
        from src.clients.ozon import OzonClient
        return OzonClient(client_id, api_key)
    raise ValueError(f"Неизвестная площадка: {platform}")


def _parse_quantity(value) -> tuple[int, str | None]:
    """
    Парсит quantity.

    Возвращает (quantity, error):
    - >0: как есть, error=None.
    - 0: 0, error="quantity = 0 → ошибка (не создаём)".
    - <0: abs, error="quantity < 0 (abs): X → Y".
    - "": 0, error="quantity пустой → 0".
    - None: 0, error="quantity None → 0".
    - "abc": 0, error="quantity 'abc' → 0".
    """
    if value is None:
        return 0, "quantity None → 0"
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return 0, "quantity пустой → 0"
        try:
            num = int(s)
        except ValueError:
            return 0, f"quantity '{value}' → 0"
    else:
        try:
            num = int(value)
        except (ValueError, TypeError):
            return 0, f"quantity '{value}' → 0"

    if num < 0:
        return abs(num), f"quantity < 0 (abs): {num} → {abs(num)}"
    if num == 0:
        return 0, "quantity = 0 → ошибка (не создаём)"
    return num, None


def _parse_price(value) -> tuple[float, str | None]:
    """
    Парсит price.

    Возвращает (price, error):
    - >0: как есть, error=None.
    - 0: 0.0, error=None.
    - <0: abs, error="price < 0 (abs): X → Y".
    - "": 0.0, error="price пустой → 0".
    - None: 0.0, error="price None → 0".
    - "abc": 0.0, error="price 'abc' → 0".
    """
    if value is None:
        return 0.0, "price None → 0"
    if isinstance(value, dict):
        value = value.get("amount")
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return 0.0, "price пустой → 0"
        try:
            num = float(s)
        except ValueError:
            return 0.0, f"price '{value}' → 0"
    else:
        try:
            num = float(value)
        except (ValueError, TypeError):
            return 0.0, f"price '{value}' → 0"

    if num < 0:
        return abs(num), f"price < 0 (abs): {num} → {abs(num)}"
    return num, None


def _find_or_create_status(conn, status_name: str) -> int | None:
    """
    Находит или создаёт status в справочнике statuses.

    Площадка вольна (как с offerId): неизвестный статус — создаём.
    statusType = 'sale', sortOrder = 999, isActive = 1.
    """
    if not status_name:
        return None

    row = conn.execute(
        "SELECT statusId FROM statuses WHERE statusName = ? AND statusType = 'sale'",
        (status_name,)
    ).fetchone()
    if row:
        return row["statusId"]

    cur = conn.execute(
        """INSERT INTO statuses (statusName, statusType, sortOrder, isActive)
           VALUES (?, 'sale', 999, 1)""",
        (status_name,)
    )
    return cur.lastrowid


def _find_or_create_buyer(conn, buyer_nickname: str | None) -> int:
    """Находит или создаёт buyer. Если нет — возвращает 1 (Физлицо)."""
    nickname = (buyer_nickname or "").strip()
    if not nickname:
        return 1

    row = conn.execute(
        "SELECT buyerId FROM buyers WHERE buyerNickname = ?",
        (nickname,)
    ).fetchone()
    if row:
        return row["buyerId"]

    cur = conn.execute(
        "INSERT INTO buyers (buyerNickname, ageGroupId) VALUES (?, 2)",
        (nickname,)
    )
    return cur.lastrowid


def _find_or_create_product(conn, offer_id: str) -> int:
    """Находит или создаёт product по offerId."""
    row = conn.execute(
        "SELECT productId FROM products WHERE offerId = ?",
        (offer_id,)
    ).fetchone()
    if row:
        return row["productId"]

    cur = conn.execute(
        "INSERT INTO products (offerId, name, isActive) VALUES (?, ?, 1)",
        (offer_id, f"Товар {offer_id}")
    )
    return cur.lastrowid


# =====================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# =====================================================================

def fetch_postings(
    platform: str,
    store_code: str,
    date_from: str,
    date_to: str,
    client=None,
) -> dict:
    """
    Универсальная загрузка отправлений с площадки.

    Returns:
        dict: {"ok": bool, "inserted": int, "errors": list[str]}
    """
    errors = []
    inserted = 0

    # 1. Проверить магазин в БД
    with get_conn() as conn:
        store = conn.execute(
            "SELECT storeId, marketplaceId, hasApi FROM stores WHERE code = ?",
            (store_code,)
        ).fetchone()

        if not store:
            return {"ok": False, "error": f"Магазин '{store_code}' не найден",
                    "inserted": 0, "errors": []}

        # 2. Проверить площадку
        if platform not in ("ozon", "ym", "wb"):
            return {"ok": False, "error": f"Площадка '{platform}' не найдена",
                    "inserted": 0, "errors": []}

        # 3. Прочитать .env
        client_id, api_key = _read_env(platform, store_code)

        has_api = store["hasApi"]
        has_env = bool(client_id and api_key)

        if has_api and not has_env:
            return {"ok": False, "error": f"hasApi=1, но нет ключей в .env для '{store_code}'",
                    "inserted": 0, "errors": []}

        if not has_api and not has_env:
            return {"ok": False, "error": f"hasApi=0 и нет ключей в .env для '{store_code}'",
                    "inserted": 0, "errors": []}

        if not has_api and has_env:
            errors.append(f"hasApi=0, но ключи в .env есть. Обновите stores.hasApi для '{store_code}'")

        # 4. Создать клиент (если не передан)
        if client is None:
            try:
                client = _create_client(platform, client_id, api_key)
            except Exception as e:
                return {"ok": False, "error": str(e),
                        "inserted": 0, "errors": []}

        # 5. Загрузить отправления
        print(f"[1/4] Загрузка отправлений ({platform}/{store_code}, {date_from}—{date_to})...")
        try:
            postings = client.get_postings(date_from, date_to)
        except Exception as e:
            return {"ok": False, "error": str(e),
                    "inserted": 0, "errors": []}

        print(f"  → Получено: {len(postings)}")

        if not postings:
            print("  → Пустой ответ (нет отправлений)")
            return {"ok": True, "inserted": 0, "errors": errors}

        # 6. Сохранить сырой JSON
        DATA_API_RAW.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_path = DATA_API_RAW / f"{platform}_{store_code}_postings_{date_from}_{stamp}.json"
        raw_path.write_text(json.dumps(postings, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  → Сырой JSON: {raw_path}")

        # 7. Обработать отправления
        print(f"[2/4] Сохранение в БД...")
        marketplace_id = store["marketplaceId"]

        for i, p in enumerate(postings):
            
            if not p:
                errors.append("Пропущен None в postings")
                continue

            posting_number = p.get("posting_number")
            if not posting_number:
                errors.append("Пропущен posting_number=None")
                continue

            # Найти или создать salesOrder
            existing = conn.execute(
                "SELECT salesOrderId FROM salesOrders WHERE marketplaceOrderId = ?",
                (posting_number,)
            ).fetchone()

            if existing:
                sales_order_id = existing["salesOrderId"]
            else:
                buyer_id = _find_or_create_buyer(conn, p.get("buyer_nickname"))
                created_at = p.get("created_at") or datetime.now().isoformat()
                
                cur = conn.execute(
                    """INSERT INTO salesOrders 
                       (buyerId, marketplaceId, marketplaceOrderId, currencyId, createdAt)
                       VALUES (?, ?, ?, 1, ?)""",
                    (buyer_id, marketplace_id, posting_number, created_at)
                )
                sales_order_id = cur.lastrowid
                inserted += 1

            # Создать salesOrderStatusHistory
            status_name = p.get("status")
            status_id = _find_or_create_status(conn, status_name)
            if status_id:
                existing_history = conn.execute(
                    "SELECT historyId FROM salesOrderStatusHistory WHERE salesOrderId = ? AND statusId = ?",
                    (sales_order_id, status_id)
                ).fetchone()
                if not existing_history:
                    conn.execute(
                        """INSERT INTO salesOrderStatusHistory 
                           (salesOrderId, statusId, statusDate)
                           VALUES (?, ?, ?)""",
                        (sales_order_id, status_id, p.get("created_at") or datetime.now().isoformat())
                    )

            # Обработать products
            for prod in p.get("products", []) or []:
                if not prod:
                    continue

                offer_id = prod.get("offer_id")
                if not offer_id:
                    errors.append(f"Пропущен offer_id=None в {posting_number}")
                    continue

                quantity, q_err = _parse_quantity(prod.get("quantity"))
                if q_err:
                    errors.append(f"{posting_number}: {q_err}")

                # quantity <= 0 — не создаём salesOrderItem (ошибка)
                if quantity <= 0:
                    continue

                price, p_err = _parse_price(prod.get("price"))
                if p_err:
                    errors.append(f"{posting_number}: {p_err}")

                product_id = _find_or_create_product(conn, offer_id)

                conn.execute(
                    """INSERT INTO salesOrderItems 
                       (salesOrderId, productId, quantity, salePrice, warehouseId)
                       VALUES (?, ?, ?, ?, 1)""",
                    (sales_order_id, product_id, quantity, price)
                )

            if (i + 1) % 100 == 0:
                print(f"  → Обработано: {i + 1}/{len(postings)}")

        conn.commit()
        print(f"[3/4] Готово: создано {inserted}")
        print(f"[4/4] Ошибок: {len(errors)}")

    return {
        "ok": True,
        "inserted": inserted,
        "errors": errors,
    }


# =====================================================================
# CLI
# =====================================================================

def main():
    if len(sys.argv) < 5:
        print("Использование: python -m src.scripts.fetch_postings <platform> <store_code> <date_from> <date_to>")
        print("Пример: python -m src.scripts.fetch_postings ozon limited_games 2026-01-01 2026-11-08")
        sys.exit(1)

    platform = sys.argv[1]
    store_code = sys.argv[2]
    date_from = sys.argv[3]
    date_to = sys.argv[4]

    result = fetch_postings(platform, store_code, date_from, date_to)

    if result["ok"]:
        print(f"\n✅ OK: создано {result['inserted']}")
        if result["errors"]:
            print(f"⚠️  Ошибки ({len(result['errors'])}):")
            for e in result["errors"][:10]:
                print(f"  - {e}")
            if len(result["errors"]) > 10:
                print(f"  ... и ещё {len(result['errors']) - 10}")
        sys.exit(0)
    else:
        print(f"\n❌ ОШИБКА: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()