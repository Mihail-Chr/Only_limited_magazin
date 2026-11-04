from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.db import get_conn
from src.config import get_store
from src.ozon_client import OzonClient
from datetime import date, datetime
import json

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
                   COALESCE(sm.quantity, 0) AS quantity,
                   w.name AS warehouse_name
            FROM product p
            LEFT JOIN listing l ON l.product_id = p.id AND l.store_id = 1
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            LEFT JOIN warehouse w ON w.id = l.warehouse_id
            ORDER BY p.baseGameName ASC LIMIT 500
        """).fetchall()
        platforms = sorted(list({r["platform"] for r in rows if r["platform"]}))
    return templates.TemplateResponse(request, "seller.html", {"rows": rows, "platforms": platforms})

# --- РУЧНАЯ ПРОДАЖА ---
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
        stock_row = conn.execute("SELECT quantity FROM stock_manual WHERE product_id = ?", (product_id,)).fetchone()
        if not stock_row or stock_row["quantity"] < quantity:
            return JSONResponse({"ok": False, "error": "Недостаточно остатка", "redirect": "/keeper/inventory"}, status_code=400)

        store_row = conn.execute("SELECT id FROM store WHERE code = 'manual'").fetchone()
        store_id = store_row["id"]

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

# --- СИНХРОНИЗАЦИЯ ПРОДАЖ С OZON ---
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
    stores = []
    with get_conn() as conn:
        stores = conn.execute("SELECT code, name, client_id, api_key FROM store WHERE has_api = 1").fetchall()
        
    if not stores:
        return JSONResponse({"ok": False, "error": "Нет магазинов с API"})

    total_items = 0
    
    for store in stores:
        try:
            store_config = get_store("ozon", store["code"])
            client = OzonClient(store_config)
            
            since = f"{date_from}T00:00:00Z"
            to = f"{date_to}T23:59:59Z"
            
            with get_conn() as conn:
                store_id_db = conn.execute("SELECT id FROM store WHERE code = ?", (store["code"],)).fetchone()["id"]
                
                cursor = ""
                while True:
                    payload = {
                        "dir": "ASC",
                        "filter": {"since": since, "to": to, "status": ""},
                        "limit": 100,
                        "cursor": cursor,
                        "with": {"analytics_data": False, "barcodes": False, "financial_data": False}
                    }
                    data = client.post("/v4/posting/fbs/list", payload)
                    postings = data.get("postings", [])
                    
                    if not postings:
                        break
                        
                    for p in postings:
                        posting_number = p.get("posting_number")
                        if not posting_number:
                            continue
                            
                        existing = conn.execute("SELECT id FROM posting WHERE posting_number = ?", (posting_number,)).fetchone()
                        if existing:
                            continue
                            
                        created_at = p.get("in_process_at", "")[:10]
                        if not created_at:
                            created_at = p.get("shipment_date", "")[:10]
                        if not created_at:
                            created_at = date.today().isoformat()
                        
                        buyer_nickname = "Физлицо"
                        buyer_row = conn.execute("SELECT buyerId FROM buyer WHERE buyerNickname = ?", (buyer_nickname,)).fetchone()
                        buyer_id = buyer_row["buyerId"] if buyer_row else 1
                        
                        cur = conn.execute("""
                            INSERT INTO posting(posting_number, store_id, status, created_at, source, buyer_id, buyer_nickname, is_preorder)
                            VALUES(?, ?, ?, ?, 'ozon', ?, ?, 0)
                        """, (posting_number, store_id_db, p.get("status"), created_at, buyer_id, buyer_nickname))
                        posting_id = cur.lastrowid
                        
                        for prod in p.get("products", []):
                            offer_id = prod.get("offer_id")
                            product_row = conn.execute("SELECT id FROM product WHERE offer_id = ?", (offer_id,)).fetchone()
                            product_id = product_row["id"] if product_row else None
                            
                            stock_row = conn.execute("SELECT quantity FROM stock_manual WHERE product_id = ?", (product_id,)).fetchone()
                            stock_qty = stock_row["quantity"] if stock_row else 0
                            is_preorder = 1 if stock_qty <= 0 else 0
                            
                            if is_preorder:
                                conn.execute("UPDATE posting SET is_preorder = 1 WHERE id = ?", (posting_id,))
                            
                            raw_price = prod.get("price", 0)
                            if isinstance(raw_price, dict):
                                price_val = float(raw_price.get("amount", 0) or 0)
                            else:
                                price_val = float(raw_price or 0)
                                
                            sku = str(prod.get("sku", "") or "")
                            conn.execute("""
                                INSERT INTO posting_item(posting_id, product_id, offer_id, sku, quantity, price, currency)
                                VALUES(?, ?, ?, ?, ?, ?, 'RUB')
                            """, (posting_id, product_id, offer_id, sku, int(prod.get("quantity", 1)), price_val))
                            
                            total_items += 1
                    
                    cursor = data.get("cursor", "")
                    if not data.get("has_next") or not cursor:
                        break
            
            conn.commit()
            
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Ошибка магазина {store['name']}: {str(e)}"})

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO sync_log(sync_type, date_from, date_to, records_count)
            VALUES('ozon_sales', ?, ?, ?)
        """, (date_from, date_to, total_items))
        conn.commit()

    return JSONResponse({"ok": True, "message": f"Загружено позиций: {total_items}"})

# --- ТОВАРЫ ПОД ЗАКАЗ ---
@router.get("/preorders", response_class=HTMLResponse)
def preorders_list(request: Request):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT 
                po.posting_number, 
                po.created_at, 
                po.status, 
                po.is_preorder,
                s.name AS store_name,
                pi.quantity, 
                pi.price, 
                pi.offer_id,
                pi.sku,
                p.baseGameName AS name, 
                p.platform
            FROM posting po
            JOIN posting_item pi ON pi.posting_id = po.id
            JOIN product p ON p.id = pi.product_id
            JOIN store s ON s.id = po.store_id
            WHERE po.is_preorder = 1 AND po.status != 'cancelled'
            ORDER BY s.name, po.created_at, po.posting_number, pi.sku
        """).fetchall()
    return templates.TemplateResponse(request, "preorders_list.html", {"rows": rows})