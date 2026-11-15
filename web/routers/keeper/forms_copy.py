from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.db import get_conn
from ._dicts import get_dictionaries
from ._ozon_price import get_ozon_price


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/copy_product/{product_id}", response_class=HTMLResponse)
def copy_product_page(request: Request, product_id: int):
    
    with get_conn() as conn:
        prod = conn.execute(
            "SELECT * FROM products WHERE productId = ? AND isActive = 1",
            (product_id,),
        ).fetchone()
        if not prod:
            return RedirectResponse("/keeper/manage_products")

        ctx = get_dictionaries(conn)
        stock = conn.execute(
            "SELECT quantity, warehouseId FROM stocks WHERE productId = ?", (product_id,)
        ).fetchone()
        listing = conn.execute(
            "SELECT price FROM listings WHERE storeId = 1 AND productId = ?", (product_id,)
        ).fetchone()
        ozon_price = get_ozon_price(conn, product_id, fallback_listing_price=listing["price"] if listing else None)

    ctx.update({
        "product": prod,
        "quantity": stock["quantity"] if stock else 0,
        "warehouse_id": stock["warehouseId"] if stock else 1,
        "ozon_price": ozon_price,
        "mode": "copy",
        "parse_note": prod["parseNote"],
    })
    return templates.TemplateResponse(request, "add_product.html", ctx)