"""
inventory_list.py — GET /keeper/inventory (инвентаризация).
"""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.db import get_conn
from ._dicts import get_warehouses

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/inventory", response_class=HTMLResponse)
def keeper_inventory(request: Request):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.productId AS id, p.offerId AS offer_id, p.baseGameName AS name,
                   pl.platformName || ' ' || pl.platformVersion AS platform,
                   COALESCE(s.quantity, 0) AS quantity,
                   COALESCE(s.warehouseId, 1) AS warehouse_id
            FROM products p
            LEFT JOIN stocks s ON s.productId = p.productId
            LEFT JOIN platforms pl ON pl.platformId = p.platformId
            WHERE p.isActive = 1
            ORDER BY p.baseGameName ASC
            
        """).fetchall()

        platforms = sorted(list({r["platform"] for r in rows if r["platform"]}))
        warehouses = get_warehouses(conn)

    return templates.TemplateResponse(request, "keeper_inventory.html", {
        "rows": rows, "platforms": platforms, "warehouses": warehouses,
    })