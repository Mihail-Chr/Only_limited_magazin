from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.db import get_conn
from ._dicts import get_dictionaries

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/add_product", response_class=HTMLResponse)
def add_product_page(request: Request):
    
    with get_conn() as conn:
        ctx = get_dictionaries(conn)

    ctx.update({
        "product": None,
        "quantity": 0,
        "warehouse_id": 1,
        "ozon_price": None,
        "mode": "add",
        "parse_note": None,
    })
    return templates.TemplateResponse(request, "add_product.html", ctx)