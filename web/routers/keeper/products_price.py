"""
products_price.py — POST /keeper/update_price_inline.

Меняет входную цену (products.cost) и/или цену OZON (listings.price)
для одного товара.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from src.db import get_conn
from .._shared.common import error, ok

router = APIRouter()


class PriceInlineUpdate(BaseModel):
    product_id: int
    cost: float | None = None
    ozon_price: float | None = None


@router.post("/update_price_inline")
def update_price_inline(data: PriceInlineUpdate):
    if data.cost is not None and data.cost < 0:
        return error("Входная цена не может быть отрицательной")
    if data.ozon_price is not None and data.ozon_price < 0:
        return error("Цена OZON не может быть отрицательной")

    with get_conn() as conn:
        prod = conn.execute(
            "SELECT productId FROM products WHERE productId = ? AND isActive = 1",
            (data.product_id,),
        ).fetchone()
        if not prod:
            return error(f"Товар {data.product_id} не найден")

        if data.cost is not None:
            conn.execute(
                "UPDATE products SET cost = ?, updatedAt = datetime('now') WHERE productId = ?",
                (data.cost, data.product_id),
            )

        if data.ozon_price is not None:
            existing = conn.execute(
                "SELECT listingId FROM listings WHERE storeId = 1 AND productId = ?",
                (data.product_id,),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE listings SET price = ? WHERE listingId = ?",
                    (data.ozon_price, existing["listingId"]),
                )
            else:
                conn.execute(
                    "INSERT INTO listings (storeId, productId, price, status) VALUES (1, ?, ?, 'draft')",
                    (data.product_id, data.ozon_price),
                )

        conn.commit()

    return ok()