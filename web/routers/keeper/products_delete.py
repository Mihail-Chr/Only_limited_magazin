"""
products_delete.py — POST /keeper/delete_product/{product_id}.

Физическое удаление (если нет salesOrderItems), иначе — isActive=0.
"""
from fastapi import APIRouter

from src.db import get_conn
from .._shared.common import error, ok

router = APIRouter()


@router.post("/delete_product/{product_id}")
def delete_product(product_id: int):
    with get_conn() as conn:
        prod = conn.execute(
            "SELECT productId FROM products WHERE productId = ?",
            (product_id,),
        ).fetchone()
        if not prod:
            return error(f"Товар {product_id} не найден", status_code=404)

        sales = conn.execute(
            "SELECT COUNT(*) FROM salesOrderItems WHERE productId = ?",
            (product_id,),
        ).fetchone()[0]

        if sales > 0:
            return error("Нельзя удалить: есть на складе")

        conn.execute("DELETE FROM listings WHERE productId = ?", (product_id,))
        conn.execute("DELETE FROM stocks WHERE productId = ?", (product_id,))
        conn.execute("DELETE FROM products WHERE productId = ?", (product_id,))
        conn.commit()

    return ok(mode="physical")