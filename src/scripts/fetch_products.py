"""
fetch_products.py — универсальная загрузка товаров с площадки (v3.2).

Логика (обновлено):
1. Проверяем магазин в БД и .env.
2. Загружаем список товаров с площадки (в память).
3. Валидируем структуру (наличие offerId, sku).
4. Сохраняем сырой JSON в data/api_raw (для истории).
5. Идём по товарам:
   - Если offerId НЕТ в БД -> создаём products (name = "Товар X") + listings (price).
   - Если offerId ЕСТЬ -> обновляем ТОЛЬКО цену в listings (price) и priceAPI.
   - Названия (name), платформы, остатки и т.д. НЕ ТРОГАЕМ.
6. Запрашиваем реальные названия (info/list) для НОВЫХ товаров и обновляем их name.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Корень проекта
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db import get_conn

DATA_API_RAW = Path("data/api_raw")


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ
# =====================================================================

def _read_env(platform: str, store_code: str) -> tuple[str | None, str | None]:
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
    if platform == "ozon":
        from src.clients.ozon import OzonClient
        return OzonClient(client_id, api_key)
    raise ValueError(f"Неизвестная площадка: {platform}")


def _is_valid_offer_id(offer_id) -> bool:
    if not offer_id or not isinstance(offer_id, str):
        return False
    return bool(offer_id.strip())


# =====================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# =====================================================================

def fetch_products(platform: str, store_code: str, client=None) -> dict:
    errors = []
    inserted = 0
    updated = 0
    listings_count = 0

    with get_conn() as conn:
        store = conn.execute(
            "SELECT storeId, marketplaceId, warehouseId, hasApi FROM stores WHERE code = ?",
            (store_code,)
        ).fetchone()

        if not store:
            return {"ok": False, "error": f"Магазин '{store_code}' не найден", "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        client_id, api_key = _read_env(platform, store_code)
        has_api = store["hasApi"]
        has_env = bool(client_id and api_key)

        if has_api and not has_env:
            return {"ok": False, "error": f"hasApi=1, но нет ключей в .env", "inserted": 0, "updated": 0, "listings": 0, "errors": []}
        if not has_api and has_env:
            errors.append(f"hasApi=0, но ключи в .env есть. Обновите stores.hasApi для '{store_code}'")
        if not has_api and not has_env:
            return {"ok": False, "error": f"hasApi=0 и нет ключей в .env", "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        if client is None:
            try:
                client = _create_client(platform, client_id, api_key)
            except Exception as e:
                return {"ok": False, "error": str(e), "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        print(f"[1/4] Загрузка списка товаров ({platform}/{store_code})...")
        try:
            products = client.get_products()
        except Exception as e:
            return {"ok": False, "error": str(e), "inserted": 0, "updated": 0, "listings": 0, "errors": []}

        print(f"  -> Получено: {len(products)}")

        if not products:
            return {"ok": True, "inserted": 0, "updated": 0, "listings": 0, "errors": errors}

        # Сохраняем сырой JSON (для истории)
        DATA_API_RAW.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_path = DATA_API_RAW / f"{platform}_{store_code}_product_list_{stamp}.json"
        raw_path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  -> Сырой JSON: {raw_path}")

        print(f"[2/4] Сохранение в БД (создание и обновление цен)...")
        store_id = store["storeId"]
        new_offer_ids = []

        for i, p in enumerate(products):
            offer_id = p.get("offer_id")
            if not _is_valid_offer_id(offer_id):
                errors.append(f"Пропущен пустой offerId: {offer_id!r}")
                continue

            # Цена берется из API, если ее нет - 0
            price = p.get("price")
            if price is None:
                price = p.get("old_price")
            
            sku = p.get("sku")
            
            # Ищем товар в БД
            prod = conn.execute("SELECT productId FROM products WHERE offerId = ?", (offer_id,)).fetchone()

            if prod:
                # ТОВАР ЕСТЬ -> обновляем ТОЛЬКО цену в листинге
                product_id = prod["productId"]
                updated += 1
            else:
                # ТОВАРА НЕТ -> создаем
                cur = conn.execute(
                    "INSERT INTO products (offerId, name, isActive, parseStatus) VALUES (?, ?, 1, 'ok')",
                    (offer_id, f"Товар {offer_id}")
                )
                product_id = cur.lastrowid
                inserted += 1
                new_offer_ids.append(offer_id)

            # Работа с листингом (создаем или обновляем цену)
            existing_listing = conn.execute(
                "SELECT listingId FROM listings WHERE storeId = ? AND productId = ?",
                (store_id, product_id)
            ).fetchone()

            if existing_listing:
                # Обновляем ТОЛЬКО цену
                conn.execute(
                    "UPDATE listings SET price = ?, priceAPI = ? WHERE listingId = ?",
                    (price, price, existing_listing["listingId"])
                )
            else:
                conn.execute(
                    "INSERT INTO listings (storeId, productId, sku, price, priceAPI, status) VALUES (?, ?, ?, ?, ?, 'draft')",
                    (store_id, product_id, str(sku) if sku else None, price, price)
                )
                listings_count += 1

            if (i + 1) % 500 == 0:
                print(f"  -> Обработано: {i + 1}/{len(products)}")

        conn.commit()
        print(f"  -> Создано: {inserted}, обновлено цен: {updated}, листингов: {listings_count}")

        # =================================================================
        # ШАГ 3: Загружаем названия ТОЛЬКО для новых товаров
        # =================================================================
        if new_offer_ids:
            print(f"[3/4] Загрузка названий для {len(new_offer_ids)} новых товаров...")
            try:
                info = client.get_product_info(new_offer_ids)
                updated_names = 0
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
                print(f"  -> Обновлено названий: {updated_names}")
            except Exception as e:
                errors.append(f"Ошибка при загрузке названий: {e}")
        else:
            print(f"[3/4] Новых товаров нет. Названия не трогаем.")

        print(f"[4/4] Готово.")

    return {
        "ok": True,
        "inserted": inserted,
        "updated": updated,
        "listings": listings_count,
        "errors": errors,
    }

# =====================================================================
# CLI
# =====================================================================

def main():
    if len(sys.argv) < 3:
        print("Использование: python -m src.scripts.fetch_products <platform> <store_code>")
        sys.exit(1)

    platform = sys.argv[1]
    store_code = sys.argv[2]

    result = fetch_products(platform, store_code)

    if result["ok"]:
        print(f"\nOK: создано {result['inserted']}, обновлено {result['updated']}, листингов {result['listings']}")
        if result["errors"]:
            print(f"Предупреждения ({len(result['errors'])}):")
            for e in result["errors"][:10]:
                print(f"  - {e}")
        sys.exit(0)
    else:
        print(f"\nОШИБКА: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()