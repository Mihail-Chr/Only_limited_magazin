from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime
from src.db import get_conn

router = APIRouter()

class OrderItem(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int
    sale_price: float

class ManualSaleRequest(BaseModel):
    buyer_nickname: str = "Физлицо"
    items: List[OrderItem]

@router.post("/manual_sale")
def create_manual_sale(data: ManualSaleRequest):
    if not data.items:
        return JSONResponse({"ok": False, "error": "Корзина пуста"}, status_code=400)

    with get_conn() as conn:
        buyer = conn.execute("SELECT buyerId FROM buyers WHERE buyerNickname = ?", (data.buyer_nickname,)).fetchone()
        buyer_id = buyer["buyerId"] if buyer else conn.execute("INSERT INTO buyers (buyerNickname, ageGroupId) VALUES (?, 2)", (data.buyer_nickname,)).lastrowid

        marketplace_id = conn.execute("SELECT marketplaceId FROM marketplaces WHERE code = 'manual'").fetchone()[0]
        order_num = f"MAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cur = conn.execute("""
            INSERT INTO salesOrders (buyerId, marketplaceId, marketplaceOrderId, currencyId, createdAt)
            VALUES (?, ?, ?, 1, datetime('now'))
        """, (buyer_id, marketplace_id, order_num))
        sales_order_id = cur.lastrowid

        for item in data.items:
            # Проверяем остаток на КОНКРЕТНОМ складе
            stock = conn.execute("SELECT quantity FROM stocks WHERE productId = ? AND warehouseId = ?", (item.product_id, item.warehouse_id)).fetchone()
            if not stock or stock["quantity"] < item.quantity:
                return JSONResponse({"ok": False, "error": f"Недостаточно остатка на складе для товара ID {item.product_id}"}, status_code=400)
            if item.quantity <= 0:
                return JSONResponse({"ok": False, "error": "Количество должно быть больше нуля"}, status_code=400)
            if item.sale_price <= 0:
                return JSONResponse({"ok": False, "error": "Цена должна быть больше нуля"}, status_code=400)

            # Запись в salesOrderItems
            conn.execute("""
                INSERT INTO salesOrderItems (salesOrderId, productId, quantity, salePrice, warehouseId)
                VALUES (?, ?, ?, ?, ?)
            """, (sales_order_id, item.product_id, item.quantity, item.sale_price, item.warehouse_id))

            # Списание с конкретного склада
            conn.execute("UPDATE stocks SET quantity = quantity - ? WHERE productId = ? AND warehouseId = ?", (item.quantity, item.product_id, item.warehouse_id))

        conn.commit()

    return JSONResponse({"ok": True, "order_id": order_num})