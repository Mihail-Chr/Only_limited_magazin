from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
from pydantic import BaseModel
import time
from pathlib import Path
from src.db import get_conn
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
import shutil

router = APIRouter(prefix="/keeper", tags=["keeper"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

class StockItem(BaseModel):
    offer_id: str
    quantity: int

# --- Меню кладовщика ---
@router.get("/", response_class=HTMLResponse)
def keeper_menu(request: Request):
    return templates.TemplateResponse(request, "keeper_menu.html")

# --- Инвентаризация ---
@router.get("/inventory", response_class=HTMLResponse)
def keeper_inventory(request: Request):
    with get_conn() as conn:
        try:
            rows = conn.execute(
                """
                SELECT p.id, p.offer_id, p.name, COALESCE(sm.quantity, 0) AS physical_qty
                FROM product p
                LEFT JOIN stock_manual sm ON sm.product_id = p.id
                ORDER BY p.name ASC
                LIMIT 200
                """
            ).fetchall()
        except Exception:
            # Если таблицы нет — возвращаем пустой список
            rows = []
    
    return templates.TemplateResponse(request, "keeper_inventory.html", {"rows": rows})

@router.get("/backup")
def download_backup():
    db_path = Path("db/only_limited.sqlite3")
    if not db_path.exists():
        return {"error": "База не найдена"}
    return FileResponse(db_path, media_type="application/octet-stream", filename="only_limited.sqlite3")

@router.get("/backup_menu", response_class=HTMLResponse)
def backup_menu(request: Request):
    return templates.TemplateResponse(request, "backup_menu.html")

@router.post("/inventory/bulk_save")
def bulk_save_stock(items: List[StockItem]):
    changes = []
    with get_conn() as conn:
        for item in items:
            prod = conn.execute("SELECT id, name FROM product WHERE offer_id = ?", (item.offer_id,)).fetchone()
            if not prod: continue
            
            old = conn.execute("SELECT quantity FROM stock_manual WHERE product_id = ?", (prod["id"],)).fetchone()
            old_qty = old["quantity"] if old else 0

            conn.execute(
                """INSERT INTO stock_manual (product_id, quantity) VALUES (?, ?)
                   ON CONFLICT(product_id) DO UPDATE SET quantity = excluded.quantity, updated_at = datetime('now')""",
                (prod["id"], item.quantity),
            )
            
            if old_qty != item.quantity:
                changes.append({"offer_id": item.offer_id, "name": prod["name"], "old": old_qty, "new": item.quantity})
        conn.commit()
    return {"ok": True, "changes": changes}

# --- Добавление товара ---

@router.get("/add_product", response_class=HTMLResponse)
def add_product_page(request: Request):
    with get_conn() as conn:
        # Проверяем, есть ли хотя бы один тип товара
        typeGoods = conn.execute('SELECT "typeGoodId", "typeGoodName" FROM "typeGoods" ORDER BY "sortOrder"').fetchall()
        if not typeGoods:
            return templates.TemplateResponse(request, "error.html", {
                "error_message": "Справочники пусты. Сначала добавьте типы товаров в базу."
            }, status_code=200)

    with get_conn() as conn:
        typeGoods = conn.execute('SELECT "typeGoodId", "typeGoodName" FROM "typeGoods" ORDER BY "sortOrder"').fetchall()
        # Передаем платформы как есть, чтобы в шаблоне можно было разбить на название и версию
        platforms = conn.execute('SELECT "platformId", "platformName", "platformVersion" FROM platforms ORDER BY "sortOrder"').fetchall()
        editions = conn.execute('SELECT "editionId", "editionName" FROM "editionTypes" ORDER BY "sortOrder"').fetchall()
        regions = conn.execute('SELECT "regionId", "regionCode" FROM regions ORDER BY "sortOrder"').fetchall()
        publishers = conn.execute('SELECT "publisherId", "publisherName" FROM publishers ORDER BY "publisherName"').fetchall()
        games = conn.execute('SELECT DISTINCT "baseGameName" FROM product WHERE "baseGameName" IS NOT NULL').fetchall()
        
    return templates.TemplateResponse(request, "add_product.html", {
        "typeGoods": typeGoods, "platforms": platforms, "editions": editions,
        "regions": regions, "publishers": publishers, "games": games
    })

@router.post("/restore")
async def restore_backup(file: UploadFile = File(...)):
    # Сохраняем загруженный файл поверх текущей базы
    with open("db/only_limited.sqlite3", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return RedirectResponse("/keeper?ok=База восстановлена", status_code=303)

@router.post("/add_product")
def add_product_submit(
    typeGoodId: str = Form(...),
    platformName: str = Form(...),      # <-- НОВОЕ
    platformVersion: str = Form(...),   # <-- НОВОЕ
    gameName: str = Form(...),
    editionId: str = Form(...),
    regionId: str = Form(...),
    publisherId: str = Form(...),
    firstReleaseYear: str = Form(None),
    firstYearEdition: str = Form(None),
    audience: str = Form(None),
    priceRub: str = Form("0"),
    quantity: str = Form("0"),
):
    def to_int(val): return int(val) if val and str(val).strip() else None
    def to_float(val): return float(val) if val and str(val).strip() else 0.0

    with get_conn() as conn:
        edition_row = conn.execute('SELECT "editionName" FROM "editionTypes" WHERE "editionId" = ?', (editionId,)).fetchone()
        publisher_row = conn.execute('SELECT "publisherName" FROM publishers WHERE "publisherId" = ?', (publisherId,)).fetchone()

        edition_name = edition_row["editionName"] if edition_row else ""
        publisher_name = publisher_row["publisherName"] if publisher_row else ""
        
        # Склеиваем платформу и версию для сохранения в товар
        full_platform = f"{platformName} {platformVersion}".strip()

        full_name = f"{gameName} {edition_name} ({full_platform})".strip()
        offer_id = f"new_{int(time.time())}"

        cur = conn.execute(
            """INSERT INTO product (offer_id, name, baseGameName, product_type, platform, edition, age_rating, publisher, release_year, cost_price_synthetic, is_active) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (offer_id, full_name, gameName, typeGoodId, full_platform, edition_name, to_int(audience), publisher_name, to_int(firstReleaseYear), to_float(priceRub))
        )
        product_id = cur.lastrowid
        
        conn.execute('INSERT INTO listing (store_id, product_id, price, status) VALUES (1, ?, ?, "draft")', (product_id, to_float(priceRub)))
        conn.execute('INSERT INTO stock_manual (product_id, quantity) VALUES (?, ?)', (product_id, to_int(quantity) or 0))
        conn.commit()
    return RedirectResponse("/keeper/inventory?ok=Товар успешно добавлен", status_code=303)