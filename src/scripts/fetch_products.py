"""
fetch_products.py — универсальная загрузка товаров с площадки (v3.1).

Использование:
    from src.scripts.fetch_products import fetch_products
    result = fetch_products("ozon", "limited_games")

    # Или CLI:
    python -m src.scripts.fetch_products ozon limited_games

Что делает:
- Читает stores (магазин), .env (ключи).
- Создаёт клиент площадки (OzonClient, YmClient, ...).
- Загружает список товаров (get_products).
- Сохраняет сырой JSON в data/api_raw/.
- Создаёт products + listings.
- Обновляет name из get_product_info.
- Возвращает dict: {ok, inserted, updated, listings, errors}.
"""
import json
import os
import re
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
    """
    Читает ключи API из .env (с префиксом площадки).

    Пример: OZON_LIMITED_GAMES_CLIENT_ID, OZON_LIMITED_GAMES_API_KEY.
    Обрезает пробелы и кавычки.
    """
    prefix = platform.upper()
    store_upper = store_code.upper()

    client_id = os.getenv(f"{prefix}_{store_upper}_CLIENT_ID")
    api_key = os.getenv(f"{prefix}_{store_upper}_API_KEY")

    # Обрезаем пробелы и кавычки
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
    # Позже: elif platform == "ym": from src.clients.ym import YmClient; ...
    raise ValueError(f"Неизвестная площадка: {platform}")


def _is_valid_offer_id(offer_id) -> bool:
    """
    Проверяет offerId (только на пустоту).

    Площадка вольна делать что хочет (странный offerId — валидный).
    Пропускаем только пустые: None, "", "   ".
    """
    if not offer_id:
        return False
    if not isinstance(offer_id, str):
        return False
    s = offer_id.strip()
    if not s:
        return False
    return True


# =====================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# =====================================================================

def fetch_products(platform: str, store_code: str, client=None) -> dict:
    """
    Универсальная загрузка товаров с площадки.

    Args:
        platform: площадка ("ozon", "ym", ...).
        store_code: магазин ("limited_games", ...).
        client: клиент API (опционально, для тестов).

    Returns:
        dict: {"ok": bool, "inserted": int, "updated": int,
               "listings": int, "errors": list[str]}
    """
    errors = []
    inserted = 0
    listings_count = 0

    # 1. Проверить магазин в БД
    with get_conn() as conn:
        store = conn.execute(
            "SELECT storeId, marketplaceId, warehouseId, hasApi FROM stores WHERE code = ?",
            (store_code,)
        ).fetchone()

        if not store:
            return {"ok": False, "error": f"Магазин '{store_code}' не найден",
                    "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        # 2. Прочитать .env
        client_id, api_key = _read_env(platform, store_code)

        # Проверка hasApi vs .env
        has_api = store["hasApi"]
        has_env = bool(client_id and api_key)

        if has_api and not has_env:
            return {"ok": False, "error": f"hasApi=1, но нет ключей в .env для '{store_code}'",
                    "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        if not has_api and not has_env:
            return {"ok": False, "error": f"hasApi=0 и нет ключей в .env для '{store_code}'",
                    "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        if not has_api and has_env:
            errors.append(f"hasApi=0, но ключи в .env есть. Обновите stores.hasApi для '{store_code}'")

        # 3. Создать клиент (если не передан)
        if client is None:
            try:
                client = _create_client(platform, client_id, api_key)
            except Exception as e:
                return {"ok": False, "error": str(e),
                        "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        # 4. Загрузить список товаров
        print(f"[1/4] Загрузка списка товаров ({platform}/{store_code})...")
        try:
            products = client.get_products()
        except Exception as e:
            return {"ok": False, "error": str(e),
                    "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        print(f"  → Получено: {len(products)}")

        if not products:
            print("  → Пустой ответ (нет товаров)")
            return {"ok": True, "inserted": 0, "updated": 0, "listings": 0, "errors": errors}

        # 5. Сохранить сырой JSON
        DATA_API_RAW.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_path = DATA_API_RAW / f"{platform}_{store_code}_product_list_{stamp}.json"
        raw_path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  → Сырой JSON: {raw_path}")

        # 6. Создать products + listings
        print(f"[2/4] Сохранение в БД...")
        store_id = store["storeId"]

        for i, p in enumerate(products):
            offer_id = p.get("offer_id")
            sku = p.get("sku")
            name = f"Товар {offer_id}" if offer_id else "Товар"

            # Пропустить пустой offerId
            if not _is_valid_offer_id(offer_id):
                errors.append(f"Пропущен пустой offerId: {offer_id!r}")
                continue

            # Найти или создать product
            prod = conn.execute(
                "SELECT productId FROM products WHERE offerId = ?", (offer_id,)
            ).fetchone()

            if prod:
                product_id = prod["productId"]
            else:
                cur = conn.execute(
                    """INSERT INTO products (offerId, name, isActive)
                       VALUES (?, ?, 1)""",
                    (offer_id, name)
                )
                product_id = cur.lastrowid
                inserted += 1

            # Создать listing (если нет)
            existing_listing = conn.execute(
                "SELECT listingId FROM listings WHERE storeId = ? AND productId = ?",
                (store_id, product_id)
            ).fetchone()

            if not existing_listing:
                conn.execute(
                    """INSERT INTO listings (storeId, productId, sku, status)
                       VALUES (?, ?, ?, 'draft')""",
                    (store_id, product_id, str(sku) if sku else None)
                )
                listings_count += 1

            # Прогресс
            if (i + 1) % 100 == 0:
                print(f"  → Обработано: {i + 1}/{len(products)}")

        conn.commit()
        print(f"  → Создано: {inserted}, листингов: {listings_count}")

        # 7. Загрузить названия
        print(f"[3/4] Загрузка названий...")
        valid_offer_ids = [p.get("offer_id") for p in products if _is_valid_offer_id(p.get("offer_id"))]

        updated_names = 0
        if valid_offer_ids:
            try:
                info = client.get_product_info(valid_offer_ids)
            except Exception as e:
                errors.append(f"Ошибка при загрузке названий: {e}")
                info = []

            for d in info:
                oid = d.get("offer_id")
                real_name = d.get("name")
                if oid and real_name:
                    conn.execute(
                        "UPDATE products SET name = ?, updatedAt = datetime('now') WHERE offerId = ?",
                        (real_name, oid)
                    )
                    updated_names += 1
            conn.commit()
            print(f"  → Обновлено названий: {updated_names}")

        print(f"[4/4] Готово: создано {inserted}, обновлено {updated_names}, листингов {listings_count}")

    return {
        "ok": True,
        "inserted": inserted,
        "updated": updated_names,
        "listings": listings_count,
        "errors": errors,
    }


# =====================================================================
# CLI
# =====================================================================

def main():
    if len(sys.argv) < 3:
        print("Использование: python -m src.scripts.fetch_products <platform> <store_code>")
        print("Пример: python -m src.scripts.fetch_products ozon limited_games")
        sys.exit(1)

    platform = sys.argv[1]
    store_code = sys.argv[2]

    result = fetch_products(platform, store_code)

    if result["ok"]:
        print(f"\n✅ OK: создано {result['inserted']}, обновлено {result['updated']}, листингов {result['listings']}")
        if result["errors"]:
            print(f"⚠️  Предупреждения ({len(result['errors'])}):")
            for e in result["errors"]:
                print(f"  - {e}")
        sys.exit(0)
    else:
        print(f"\n❌ ОШИБКА: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()