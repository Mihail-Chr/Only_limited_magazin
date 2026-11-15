from pathlib import Path
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.db import get_conn

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/orders", response_class=HTMLResponse)
def orders_list(
    request: Request,
    date_from: str = Query(None),
    date_to: str = Query(None)
):
    with get_conn() as conn:
        query = """
            SELECT so.salesOrderId AS id, so.marketplaceOrderId AS order_num, so.createdAt AS created_at,
                   b.buyerNickname AS buyer, m.name AS marketplace,
                   p.baseGameName AS product_name, soi.quantity, soi.salePrice AS price
            FROM salesOrders so
            JOIN marketplaces m ON m.marketplaceId = so.marketplaceId
            JOIN buyers b ON b.buyerId = so.buyerId
            JOIN salesOrderItems soi ON soi.salesOrderId = so.salesOrderId
            JOIN products p ON p.productId = soi.productId
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND so.createdAt >= ?"
            params.append(date_from + " 00:00:00")
        if date_to:
            query += " AND so.createdAt <= ?"
            params.append(date_to + " 23:59:59")
        
        query += " ORDER BY so.salesOrderId DESC"
        rows = conn.execute(query, params).fetchall()

    # Обязательно передаем даты обратно, чтобы они не сбрасывались в полях
    return templates.TemplateResponse(request, "seller_orders.html", {
        "rows": rows, 
        "date_from": date_from or "",
        "date_to": date_to or ""
    })