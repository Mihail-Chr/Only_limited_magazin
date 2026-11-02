from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from pydantic import BaseModel
import time
import shutil
import difflib
from pathlib import Path
from src.db import get_conn

router = APIRouter(prefix="/keeper", tags=["keeper"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

class StockItem(BaseModel):
    offer_id: str
    quantity: int

class StockInlineUpdate(BaseModel):
    product_id: int
    quantity: int

class CheckDuplicatesReq(BaseModel):
    gameName: str
    platformName: str
    platformVersion: Optional[str] = None
    editionId: Optional[str] = None
    regionId: Optional[str] = None
    publisherId: Optional[str] = None
    exclude_id: Optional[int] = None # Для редактирования

@router.get("/", response_class=HTMLResponse)
def keeper_menu(request: Request):
    return templates.TemplateResponse(request, "keeper_menu.html")

@router.get("/inventory", response_class=HTMLResponse)
def keeper_inventory(request: Request):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.id, p.offer_id, p.baseGameName AS name, p.platform,
                   COALESCE(sm.quantity, 0) AS physical_qty
            FROM product p
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            ORDER BY p.baseGameName ASC LIMIT 500
        """).fetchall()
        platforms = sorted(list({r["platform"] for r in rows if r["platform"]}))
    return templates.TemplateResponse(request, "keeper_inventory.html", {"rows": rows, "platforms": platforms})

@router.post("/inventory/bulk_save")
def bulk_save_stock(items: List[StockItem]):
    with get_conn() as conn:
        for item in items:
            prod = conn.execute("SELECT id FROM product WHERE offer_id = ?", (item.offer_id,)).fetchone()
            if prod:
                conn.execute("""
                    INSERT INTO stock_manual (product_id, quantity) VALUES (?, ?)
                    ON CONFLICT(product_id) DO UPDATE SET quantity = excluded.quantity, updated_at = datetime('now')
                """, (prod["id"], item.quantity))
        conn.commit()
    return {"ok": True}

@router.post("/update_stock_inline")
def update_stock_inline(data: StockInlineUpdate):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO stock_manual (product_id, quantity) VALUES (?, ?)
            ON CONFLICT(product_id) DO UPDATE SET quantity = excluded.quantity
        """, (data.product_id, data.quantity))
        conn.commit()
    return {"ok": True}

# --- УПРАВЛЕНИЕ ТОВАРАМИ ---
@router.get("/manage_products", response_class=HTMLResponse)
def manage_products(request: Request):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT p.id, p.offer_id, p.baseGameName AS name, p.platform,
                   p.edition, p.publisher, p.regionId,
                   r.regionCode AS region,
                   p.cost_price_synthetic AS cost_price,
                   l.price AS ozon_price,
                   COALESCE(sm.quantity, 0) AS quantity
            FROM product p
            LEFT JOIN regions r ON r.regionId = p.regionId
            LEFT JOIN listing l ON l.product_id = p.id AND l.store_id = 1
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            ORDER BY p.baseGameName ASC LIMIT 500
        """).fetchall()
        platforms = sorted(list({r["platform"] for r in rows if r["platform"]}))
        editions = sorted(list({r["edition"] for r in rows if r["edition"]}))
        regions = sorted(list({r["region"] for r in rows if r["region"]}))
        publishers = sorted(list({r["publisher"] for r in rows if r["publisher"]}))
    return templates.TemplateResponse(request, "manage_products.html", {
        "rows": rows, "platforms": platforms, "editions": editions, "regions": regions, "publishers": publishers
    })

# --- ДОБАВЛЕНИЕ / КОПИРОВАНИЕ / РЕДАКТИРОВАНИЕ ---

def _get_dictionaries(conn):
    # Добавляем все платформы из товаров (включая составные PS4/PS5)
    all_db_platforms = conn.execute('SELECT DISTINCT platform FROM product WHERE platform IS NOT NULL').fetchall()
    
    return {
        "typeGoods": conn.execute('SELECT "typeGoodId", "typeGoodName" FROM "typeGoods" ORDER BY "sortOrder"').fetchall(),
        "platforms": conn.execute('SELECT "platformId", "platformName", "platformVersion" FROM platforms ORDER BY "sortOrder"').fetchall(),
        "editions": conn.execute('SELECT "editionId", "editionName" FROM "editionTypes" ORDER BY "sortOrder"').fetchall(),
        "regions": conn.execute('SELECT "regionId", "regionCode" FROM regions ORDER BY "sortOrder"').fetchall(),
        "publishers": conn.execute('SELECT "publisherId", "publisherName" FROM publishers ORDER BY "publisherName"').fetchall(),
        "games": conn.execute('SELECT DISTINCT "baseGameName" FROM product WHERE "baseGameName" IS NOT NULL').fetchall(),
        "all_db_platforms": [r["platform"] for r in all_db_platforms]
    }

@router.get("/add_product", response_class=HTMLResponse)
def add_product_page(request: Request):
    with get_conn() as conn:
        ctx = _get_dictionaries(conn)
    ctx.update({"product": None, "quantity": 0, "mode": "add"})
    return templates.TemplateResponse(request, "add_product.html", ctx)

@router.get("/copy_product/{product_id}", response_class=HTMLResponse)
def copy_product_page(request: Request, product_id: int):
    with get_conn() as conn:
        prod = conn.execute("SELECT * FROM product WHERE id = ?", (product_id,)).fetchone()
        if not prod: return RedirectResponse("/keeper/manage_products")
        ctx = _get_dictionaries(conn)
        stock = conn.execute("SELECT quantity FROM stock_manual WHERE product_id = ?", (product_id,)).fetchone()
    ctx.update({"product": prod, "quantity": stock["quantity"] if stock else 0, "mode": "copy"})
    return templates.TemplateResponse(request, "add_product.html", ctx)

@router.get("/edit_product/{product_id}", response_class=HTMLResponse)
def edit_product_page(request: Request, product_id: int):
    with get_conn() as conn:
        prod = conn.execute("SELECT * FROM product WHERE id = ?", (product_id,)).fetchone()
        if not prod: return RedirectResponse("/keeper/manage_products")
        ctx = _get_dictionaries(conn)
        stock = conn.execute("SELECT quantity FROM stock_manual WHERE product_id = ?", (product_id,)).fetchone()
    ctx.update({"product": prod, "quantity": stock["quantity"] if stock else 0, "mode": "edit"})
    return templates.TemplateResponse(request, "add_product.html", ctx)

# --- ПРОВЕРКА ДУБЛЕЙ ---
@router.post("/check_duplicates")
def check_duplicates(data: CheckDuplicatesReq):
    with get_conn() as conn:
        full_platform = f"{data.platformName} {data.platformVersion or ''}".strip()
        
        ed_name = conn.execute('SELECT "editionName" FROM "editionTypes" WHERE "editionId" = ?', (data.editionId,)).fetchone()["editionName"] if data.editionId and data.editionId != "None" else None
        pub_name = conn.execute('SELECT "publisherName" FROM publishers WHERE "publisherId" = ?', (data.publisherId,)).fetchone()["publisherName"] if data.publisherId and data.publisherId != "None" else None

        # Ищем по платформе, исключая текущий ID (если редактируем)
        query = """
            SELECT p.id, p.baseGameName, p.platform, p.edition, p.publisher, 
                   r.regionCode AS region, COALESCE(sm.quantity, 0) AS quantity
            FROM product p
            LEFT JOIN regions r ON r.regionId = p.regionId
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            WHERE p.platform = ?
        """
        params = [full_platform]
        
        if data.exclude_id:
            query += " AND p.id != ?"
            params.append(data.exclude_id)

        candidates = conn.execute(query, tuple(params)).fetchall()

        matches = []
        for row in candidates:
            ratio = difflib.SequenceMatcher(None, data.gameName.lower(), row["baseGameName"].lower()).ratio()
            
            ed_match = (row["edition"] == ed_name) if ed_name else True
            pub_match = (row["publisher"] == pub_name) if pub_name else True
            
            if ratio >= 0.8 and ed_match and pub_match:
                matches.append({
                    "id": row["id"], "name": row["baseGameName"], "platform": row["platform"],
                    "edition": row["edition"], "publisher": row["publisher"], "region": row["region"],
                    "quantity": row["quantity"], "score": round(ratio * 100)
                })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return {"ok": True, "matches": matches}

# --- СОХРАНЕНИЕ ТОВАРА ---
@router.post("/save_product")
def save_product(
    mode: str = Form(...), product_id: str = Form(None),
    typeGoodId: str = Form(...), platformName: str = Form(...), platformVersion: str = Form(None),
    gameName: str = Form(...), editionId: str = Form(None), regionId: str = Form(None),
    publisherId: str = Form(None), firstReleaseYear: str = Form(None), audience: str = Form(None),
    priceRub: str = Form("0"), quantity: str = Form("0")
):
    def to_int(val): 
        if not val or str(val).strip() in ("", "None"): return None
        try: return int(val)
        except: return None
        
    def to_float(val): 
        if not val or str(val).strip() in ("", "None"): return 0.0
        try: return float(str(val).replace(',', '.'))
        except: return 0.0

    pid = None
    if product_id and str(product_id).strip() not in ("", "None"):
        try: pid = int(product_id)
        except ValueError: pass

    with get_conn() as conn:
        wh_row = conn.execute("SELECT id FROM warehouse LIMIT 1").fetchone()
        warehouse_id = wh_row["id"] if wh_row else 1

        ed_row = conn.execute('SELECT "editionName" FROM "editionTypes" WHERE "editionId" = ?', (editionId,)).fetchone() if editionId and str(editionId) != "None" else None
        pub_row = conn.execute('SELECT "publisherName" FROM publishers WHERE "publisherId" = ?', (publisherId,)).fetchone() if publisherId and str(publisherId) != "None" else None
        
        ed_name = ed_row["editionName"] if ed_row else None
        pub_name = pub_row["publisherName"] if pub_row else None
        
        full_platform = f"{platformName} {platformVersion or ''}".strip()
        full_name = f"{gameName} {ed_name or ''} ({full_platform})".strip()
        
        if mode == "edit" and pid:
            conn.execute("""
                UPDATE product SET name=?, baseGameName=?, product_type=?, platform=?, edition=?, publisher=?, regionId=?, release_year=?, age_rating=?, cost_price_synthetic=? WHERE id=?
            """, (full_name, gameName, typeGoodId, full_platform, ed_name, pub_name, to_int(regionId), to_int(firstReleaseYear), audience or None, to_float(priceRub), pid))
            conn.execute("UPDATE listing SET price = ? WHERE product_id = ?", (to_float(priceRub), pid))
            conn.execute("INSERT INTO stock_manual (product_id, quantity) VALUES (?, ?) ON CONFLICT(product_id) DO UPDATE SET quantity = excluded.quantity", (pid, to_int(quantity) or 0))
        else:
            offer_id = f"new_{int(time.time())}"
            cur = conn.execute("""
                INSERT INTO product (offer_id, name, baseGameName, product_type, platform, edition, age_rating, publisher, release_year, cost_price_synthetic, is_active) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (offer_id, full_name, gameName, typeGoodId, full_platform, ed_name, to_int(audience), pub_name, to_int(firstReleaseYear), to_float(priceRub)))
            pid = cur.lastrowid
            
            conn.execute("""
                INSERT INTO listing (store_id, product_id, warehouse_id, price, status) 
                VALUES (1, ?, ?, ?, 'draft')
            """, (pid, warehouse_id, to_float(priceRub)))
            
            conn.execute('INSERT INTO stock_manual (product_id, quantity) VALUES (?, ?)', (pid, to_int(quantity) or 0))
        conn.commit()
    return RedirectResponse("/keeper/manage_products?ok=Сохранено", status_code=303)

# --- БЭКАП ---
@router.get("/backup")
def download_backup():
    db_path = Path("db/only_limited.sqlite3")
    if not db_path.exists(): return {"error": "База не найдена"}
    return FileResponse(db_path, media_type="application/octet-stream", filename="only_limited.sqlite3")

@router.get("/backup_menu", response_class=HTMLResponse)
def backup_menu(request: Request):
    return templates.TemplateResponse(request, "backup_menu.html")

@router.post("/restore")
async def restore_backup(file: UploadFile = File(...)):
    with open("db/only_limited.sqlite3", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return RedirectResponse("/keeper?ok=База восстановлена", status_code=303)