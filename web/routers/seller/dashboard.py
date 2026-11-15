from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.db import get_conn

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/", response_class=HTMLResponse)
def seller_dashboard(request: Request):
    with get_conn() as conn:
        # Получаем список складов
        warehouses = conn.execute("SELECT warehouseId, name FROM warehouses WHERE isActive = 1 ORDER BY sortOrder").fetchall()
        
        # Формируем запрос для получения остатков по складам
        rows = conn.execute("""
            SELECT p.productId AS id, p.offerId AS offer_id, p.baseGameName AS name,
                   pl.platformName || ' ' || pl.platformVersion AS platform,
                   l.price AS ozon_price,
                   s.warehouseId AS warehouse_id,
                   w.name AS warehouse_name,
                   s.quantity
            FROM products p
            LEFT JOIN platforms pl ON pl.platformId = p.platformId
            LEFT JOIN listings l ON l.productId = p.productId AND l.storeId = 1
            JOIN stocks s ON s.productId = p.productId
            JOIN warehouses w ON w.warehouseId = s.warehouseId
            WHERE p.isActive = 1 AND s.quantity > 0
            ORDER BY p.baseGameName ASC, w.sortOrder ASC
        """).fetchall()

        platforms = [r["platform"] for r in conn.execute("SELECT DISTINCT platformName || ' ' || platformVersion AS platform FROM platforms").fetchall()]

    return templates.TemplateResponse(request, "seller_dashboard.html", {
        "rows": rows, "platforms": platforms, "warehouses": warehouses
    })