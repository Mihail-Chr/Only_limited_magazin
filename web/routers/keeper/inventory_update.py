"""
inventory_update.py — POST /keeper/update_stock_inline.

Меняет склад + количество одной строки (UPSERT в stocks).
"""
from fastapi import APIRouter
from pydantic import BaseModel

from src.db import get_conn
from .._shared.common import error, ok

router = APIRouter()


class StockInlineUpdate(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int


@router.post("/update_stock_inline")
def update_stock_inline(data: StockInlineUpdate):
    if data.quantity < 0:
        return error("Количество не может быть отрицательным")

    with get_conn() as conn:
        wh = conn.execute(
            "SELECT warehouseId FROM warehouses WHERE warehouseId = ? AND isActive = 1",
            (data.warehouse_id,),
        ).fetchone()
        if not wh:
            return error(f"Склад {data.warehouse_id} не найден")

        prod = conn.execute(
            "SELECT productId FROM products WHERE productId = ? AND isActive = 1",
            (data.product_id,),
        ).fetchone()
        if not prod:
            return error(f"Товар {data.product_id} не найден")

        conn.execute("""
            INSERT INTO stocks (warehouseId, productId, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(warehouseId, productId)
            DO UPDATE SET quantity = excluded.quantity, updatedAt = datetime('now')
        """, (data.warehouse_id, data.product_id, data.quantity))
        conn.commit()

    return ok()