from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.db import get_conn

router = APIRouter(prefix="/seller", tags=["seller"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/", response_class=HTMLResponse)
def seller(request: Request):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.offer_id, p.name, l.price, l.commission_rate, l.payout_amount, p.cost_price_synthetic,
                   CASE WHEN p.cost_price_synthetic > 0 AND l.payout_amount > 0
                        THEN ROUND((l.payout_amount - p.cost_price_synthetic) / l.payout_amount * 100, 1)
                        ELSE NULL END AS margin_net_pct
            FROM product p JOIN listing l ON l.product_id = p.id
            WHERE l.price IS NOT NULL AND l.price > 0
            ORDER BY margin_net_pct ASC LIMIT 100
            """
        ).fetchall()
    return templates.TemplateResponse(request, "seller.html", {"rows": rows})