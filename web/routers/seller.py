from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.db import get_conn
from datetime import date

router = APIRouter(prefix="/seller", tags=["seller"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# --- ЭКРАН ПРОДАВЦА ---
@router.get("/", response_class=HTMLResponse)
def seller_dashboard(request: Request):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.id, p.offer_id, p.baseGameName AS name, p.platform, p.edition,
                   COALESCE(NULLIF(l.price, 0), (SELECT pi.price FROM posting_item pi JOIN posting po ON po.id = pi.posting_id WHERE pi.product_id = p.id AND pi.price > 0 ORDER BY po.created_at DESC, po.id DESC LIMIT 1)) AS final_price,
                   COALESCE(sm.quantity, 0) AS quantity
            FROM product p
            LEFT JOIN listing l ON l.product_id = p.id AND l.store_id = 1
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            ORDER BY p.baseGameName ASC LIMIT 500
        """).fetchall()
        platforms = sorted(list({r["platform"] for r in rows if r["platform"]}))
    return templates.TemplateResponse(request, "seller.html", {"rows": rows, "platforms": platforms})

# --- РУЧНАЯ ПРОДАЖА ---
MANUAL_STORE_CODE = "manual"
DEFAULT_BUYER_ID = 1
DEFAULT_BUYER_NICKNAME = "Физлицо"

@router.get("/manual_sale", response_class=HTMLResponse)
def manual_sale_form(request: Request):
    with get_conn() as conn:
        products = conn.execute("""
            SELECT p.id, p.offer_id, p.baseGameName AS name, p.platform,
                   COALESCE(sm.quantity, 0) AS stock,
                   COALESCE(p.cost_price_synthetic, 0) AS cost_price
            FROM product p
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            ORDER BY p.baseGameName ASC
        """).fetchall()
    return templates.TemplateResponse(request, "manual_sale.html", {
        "products": products, "today": date.today().isoformat()
    })

@router.post("/manual_sale")
def manual_sale_save(
    product_id: int = Form(...), quantity: int = Form(...), sale_price: float = Form(...),
    order_date: str = Form(...), buyer_nickname: str = Form("Физлицо"), notes: str = Form("")
):
    with get_conn() as conn:
        # Проверка остатка
        stock_row = conn.execute("SELECT quantity FROM stock_manual WHERE product_id = ?", (product_id,)).fetchone()
        if not stock_row or stock_row["quantity"] < quantity:
            return JSONResponse({"ok": False, "error": "Недостаточно остатка", "redirect": "/keeper/inventory"}, status_code=400)

        store_row = conn.execute("SELECT id FROM store WHERE code = 'manual'").fetchone()
        store_id = store_row["id"] if store_row else 3

        # Проверяем, есть ли покупатель с таким ником
        buyer_row = conn.execute("SELECT buyerId FROM buyer WHERE buyerNickname = ?", (buyer_nickname,)).fetchone()
        if buyer_row:
            buyer_id = buyer_row["buyerId"]
        else:
            cur_b = conn.execute("INSERT INTO buyer (buyerNickname) VALUES (?)", (buyer_nickname,))
            buyer_id = cur_b.lastrowid

        today = order_date.replace("-", "")
        cnt = conn.execute("SELECT COUNT(*) FROM posting WHERE posting_number LIKE ?", (f"manual_{today}_%",)).fetchone()[0]
        posting_number = f"manual_{today}_{cnt + 1:04d}"

        cur = conn.execute("""
            INSERT INTO posting(posting_number, store_id, status, created_at, source, buyer_id, buyer_nickname, is_preorder)
            VALUES(?, ?, 'received', ?, 'manual', ?, ?, 0)
        """, (posting_number, store_id, order_date, buyer_id, buyer_nickname))
        posting_id = cur.lastrowid

        conn.execute("""
            INSERT INTO posting_item(posting_id, product_id, quantity, price, currency)
            VALUES(?, ?, ?, ?, 'RUB')
        """, (posting_id, product_id, quantity, sale_price))

        conn.execute("UPDATE stock_manual SET quantity = quantity - ? WHERE product_id = ?", (quantity, product_id))
        conn.commit()
    return JSONResponse({"ok": True, "posting_number": posting_number})

@router.get("/manual_sales", response_class=HTMLResponse)
def manual_sales_list(request: Request):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT po.posting_number, po.created_at, po.buyer_nickname, pi.quantity, pi.price, p.baseGameName AS product_name
            FROM posting po
            JOIN posting_item pi ON pi.posting_id = po.id
            JOIN product p ON p.id = pi.product_id
            WHERE po.source = 'manual'
            ORDER BY po.created_at DESC, po.id DESC LIMIT 200
        """).fetchall()
    return templates.TemplateResponse(request, "manual_sales_list.html", {"rows": rows})

# --- СИНХРОНИЗАЦИЯ ПРОДАЖ С OZON (ЗАГЛУШКА ДЛЯ ШАГА 5) ---
@router.get("/sync_ozon", response_class=HTMLResponse)
def sync_ozon_page(request: Request):
    with get_conn() as conn:
        last_sync = conn.execute("SELECT * FROM sync_log WHERE sync_type = 'ozon_sales' ORDER BY synced_at DESC LIMIT 1").fetchone()
    return templates.TemplateResponse(request, "sync_ozon.html", {
        "last_sync": last_sync,
        "today": date.today().isoformat()
    })

@router.post("/sync_ozon")
def sync_ozon_start(date_from: str = Form(...), date_to: str = Form(...)):
    # TODO: Реализация в Шаге 5
    return JSONResponse({"ok": True, "message": "Синхронизация будет реализована на Шаге 5"})