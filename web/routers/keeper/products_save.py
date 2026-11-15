"""
products_save.py — POST /keeper/save_product.

Режимы:
- add  — новый товар (offerId обязателен, проверка на занятость).
- edit — обновление (offerId не меняется).
- copy — копия (offerId копируется, проверка на занятость).

Проверки:
1. Обязательные поля: offerId, baseGameName, typeGoodId, platformId.
2. offerId занят (для add/copy) → 400.
3. Дубль по 8 полям → 400.

Пишет: products (INSERT/UPDATE), listings (UPSERT price), stocks (UPSERT quantity).
"""
from fastapi import APIRouter, Request

from src.db import get_conn
from .._shared.common import error, ok, to_int_or_none, to_float_or_none, to_int_default
from ._duplicates import find_duplicate

router = APIRouter()


@router.post("/save_product")
async def save_product(request: Request):
    form = await request.form()
    mode = form.get("mode", "add")

    # --- Сбор данных ---
    data = {
        "offerId": (form.get("offerId") or "").strip(),
        "baseGameName": (form.get("baseGameName") or "").strip(),
        "typeGoodId": to_int_or_none(form.get("typeGoodId")),
        "platformId": to_int_or_none(form.get("platformId")),
        "editionId": to_int_or_none(form.get("editionId")),
        "regionId": to_int_or_none(form.get("regionId")),
        "publisherId": to_int_or_none(form.get("publisherId")),
        "mediaTypeId": to_int_or_none(form.get("mediaTypeId")),
        "restore": 1 if form.get("restore") else 0,
        "releaseYear": to_int_or_none(form.get("releaseYear")),
        "cost": to_float_or_none(form.get("cost")),
        "ozonPrice": to_float_or_none(form.get("ozonPrice")),
        "quantity": max(0, to_int_default(form.get("quantity"), 0)),
        "warehouse_id": to_int_default(form.get("warehouse_id"), 1),
    }

    # --- Валидация ---
    if not data["offerId"]:
        return error("offerId обязателен")
    if not data["baseGameName"]:
        data["baseGameName"] = f"Товар {data['offerId']}"
    if not data["baseGameName"]:
        return error("Название игры обязательно")
    if not data["typeGoodId"]:
        return error("Тип товара обязателен")
    if not data["platformId"]:
        return error("Платформа обязательна")

    exclude_id = None
    if mode == "edit":
        exclude_id = to_int_or_none(form.get("product_id"))
        if not exclude_id:
            return error("product_id обязателен для edit")

    with get_conn() as conn:
        # --- Проверка offerId (для add/copy) ---
        if mode in ("add", "copy"):
            existing = conn.execute(
                "SELECT productId FROM products WHERE offerId = ? AND isActive = 1",
                (data["offerId"],),
            ).fetchone()
            if existing:
                return error(f"offerId '{data['offerId']}' уже занят")

        # --- Проверка дублей (8 полей) ---
        dup = find_duplicate(conn, data, exclude_product_id=exclude_id)
        if dup:
            return error(
                f"Такой товар уже есть: '{dup['baseGameName']}' "
                f"(offerId '{dup['offerId']}')"
            )

        # --- products ---
        if mode == "edit":
            conn.execute("""
                UPDATE products SET
                    baseGameName = ?, typeGoodId = ?, platformId = ?, editionId = ?,
                    regionId = ?, publisherId = ?, mediaTypeId = ?, restore = ?,
                    releaseYear = ?, cost = ?, updatedAt = datetime('now')
                WHERE productId = ?
            """, (
                data["baseGameName"], data["typeGoodId"], data["platformId"],
                data["editionId"], data["regionId"], data["publisherId"],
                data["mediaTypeId"], data["restore"], data["releaseYear"],
                data["cost"], exclude_id,
            ))
            product_id = exclude_id
        else:
            conn.execute("""
                INSERT INTO products (
                    offerId, name, baseGameName, typeGoodId, platformId, editionId,
                    regionId, publisherId, mediaTypeId, restore, releaseYear,
                    cost, isActive, parseStatus
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'ok')
            """, (
                data["offerId"], data["baseGameName"], data["baseGameName"], data["typeGoodId"],
                data["platformId"], data["editionId"], data["regionId"],
                data["publisherId"], data["mediaTypeId"], data["restore"],
                data["releaseYear"], data["cost"],
            ))
            product_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # --- listings (price OZON) ---
        existing_listing = conn.execute(
            "SELECT listingId FROM listings WHERE storeId = 1 AND productId = ?",
            (product_id,),
        ).fetchone()
        if existing_listing:
            conn.execute(
                "UPDATE listings SET price = ? WHERE listingId = ?",
                (data["ozonPrice"], existing_listing["listingId"]),
            )
        else:
            conn.execute(
                "INSERT INTO listings (storeId, productId, price, status) VALUES (1, ?, ?, 'draft')",
                (product_id, data["ozonPrice"]),
            )

        # --- stocks (quantity + warehouse) ---
        conn.execute("""
            INSERT INTO stocks (warehouseId, productId, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(warehouseId, productId)
            DO UPDATE SET quantity = excluded.quantity, updatedAt = datetime('now')
        """, (data["warehouse_id"], product_id, data["quantity"]))

        conn.commit()

    return ok(productId=product_id)