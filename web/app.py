"""
Веб-интерфейс для Only_limited_magazin.
Запуск: uvicorn web.app:app --reload
Открыть: http://localhost:8000
"""
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from pydantic import BaseModel
import time

from src.db import get_conn

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Only_limited_magazin")

# Подключаем статику (CSS, картинки) и шаблоны (HTML)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Модель для массового сохранения инвентаризации
class StockItem(BaseModel):
    offer_id: str
    quantity: int


# ==========================================
# ГЛАВНАЯ И МЕНЮ
# ==========================================
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/keeper", response_class=HTMLResponse)
def keeper_menu(request: Request):
    return templates.TemplateResponse(request, "keeper_menu.html")

@app.get("/health")
def health():
    return {"status": "ok"}


# ==========================================
# ИНВЕНТАРИЗАЦИЯ (ОСТАТКИ)
# ==========================================
@app.get("/keeper/inventory", response_class=HTMLResponse)
def keeper_inventory(request: Request):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT 
                p.id,
                p.offer_id,
                p.name,
                COALESCE(sm.quantity, 0) AS physical_qty
            FROM product p
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            ORDER BY p.name ASC
            LIMIT 200
            """
        ).fetchall()
    return templates.TemplateResponse(request, "keeper_inventory.html", {"rows": rows})

@app.post("/keeper/inventory/bulk_save")
def bulk_save_stock(items: List[StockItem]):
    changes = []
    with get_conn() as conn:
        for item in items:
            prod = conn.execute(
                "SELECT id, name FROM product WHERE offer_id = ?", (item.offer_id,)
            ).fetchone()
            if not prod:
                continue
            
            old = conn.execute(
                "SELECT quantity FROM stock_manual WHERE product_id = ?", (prod["id"],)
            ).fetchone()
            old_qty = old["quantity"] if old else 0

            conn.execute(
                """INSERT INTO stock_manual (product_id, quantity)
                   VALUES (?, ?)
                   ON CONFLICT(product_id) DO UPDATE SET
                       quantity = excluded.quantity,
                       updated_at = datetime('now')""",
                (prod["id"], item.quantity),
            )
            
            if old_qty != item.quantity:
                changes.append({
                    "offer_id": item.offer_id,
                    "name": prod["name"],
                    "old": old_qty,
                    "new": item.quantity,
                })
        conn.commit()
    return {"ok": True, "changes": changes}


# ==========================================
# ДОБАВЛЕНИЕ ТОВАРА (WIZARD)
# ==========================================
# 1. Сначала GET-роут (открывает страницу)
@app.get("/keeper/add_product", response_class=HTMLResponse)
def add_product_page(request: Request):
    with get_conn() as conn:
        typeGoods = conn.execute("SELECT \"typeGoodId\", \"typeGoodName\" FROM \"typeGoods\" ORDER BY \"sortOrder\"").fetchall()
        platforms = conn.execute("SELECT \"platformId\", \"platformName\", \"platformVersion\" FROM platforms ORDER BY \"sortOrder\"").fetchall()
        editions = conn.execute("SELECT \"editionId\", \"editionName\" FROM \"editionTypes\" ORDER BY \"sortOrder\"").fetchall()
        regions = conn.execute("SELECT \"regionId\", \"regionCode\" FROM regions ORDER BY \"sortOrder\"").fetchall()
        publishers = conn.execute("SELECT \"publisherId\", \"publisherName\" FROM publishers ORDER BY \"publisherName\"").fetchall()
        games = conn.execute("SELECT DISTINCT \"baseGameName\" FROM product WHERE \"baseGameName\" IS NOT NULL").fetchall()
        
    return templates.TemplateResponse(request, "add_product.html", {
        "typeGoods": typeGoods,
        "platforms": platforms,
        "editions": editions,
        "regions": regions,
        "publishers": publishers,
        "games": games
    })

# 2. Потом POST-роут (обрабатывает форму)
@app.post("/keeper/add_product")
def add_product_submit(
    typeGoodId: str = Form(...),
    platformId: str = Form(...),
    gameName: str = Form(...),
    editionId: str = Form(...),
    regionId: str = Form(...),
    publisherId: str = Form(...),
    firstReleaseYear: str = Form(None),
    firstYearEdition: str = Form(None),
    audience: str = Form(None),
    priceRub: str = Form("0"),
    priceUsd: str = Form("0"),
    priceEur: str = Form("0"),
    priceGbp: str = Form("0"),
    quantity: str = Form("0"),
):
    # Безопасные преобразователи
    def to_int(val):
        return int(val) if val and str(val).strip() else None
    def to_float(val):
        return float(val) if val and str(val).strip() else 0.0

    with get_conn() as conn:
        # Получаем текстовые значения
        edition_row = conn.execute("SELECT editionName FROM editionTypes WHERE editionId = ?", (editionId,)).fetchone()
        platform_row = conn.execute("SELECT platformName, platformVersion FROM platforms WHERE platformId = ?", (platformId,)).fetchone()
        publisher_row = conn.execute("SELECT publisherName FROM publishers WHERE publisherId = ?", (publisherId,)).fetchone()

        edition_name = edition_row["editionName"] if edition_row else ""
        platform_name = f"{platform_row['platformName']} {platform_row['platformVersion']}" if platform_row else ""
        publisher_name = publisher_row["publisherName"] if publisher_row else ""

        full_name = f"{gameName} {edition_name} ({platform_name})".strip()
        offer_id = f"new_{int(time.time())}"

        cur = conn.execute(
            """INSERT INTO product (
                offer_id, name, baseGameName, product_type, platform, edition,
                age_rating, publisher, release_year, cost_price_synthetic, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                offer_id, full_name, gameName, typeGoodId, platform_name,
                edition_name, to_int(audience), publisher_name,
                to_int(firstReleaseYear), to_float(priceRub)
            )
        )
        product_id = cur.lastrowid

        # Листинг (цена)
        conn.execute(
            """INSERT INTO listing (store_id, product_id, price, status)
               VALUES (1, ?, ?, 'draft')""",
            (product_id, to_float(priceRub))
        )

        # Остаток
        conn.execute(
            """INSERT INTO stock_manual (product_id, quantity) VALUES (?, ?)""",
            (product_id, to_int(quantity) or 0)
        )
        conn.commit()

    return RedirectResponse("/keeper/inventory?ok=Товар успешно добавлен", status_code=303)


# ==========================================
# ПРОДАВЕЦ И API
# ==========================================
@app.get("/seller", response_class=HTMLResponse)
def seller(request: Request):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT 
                p.offer_id, p.name, l.price, l.commission_rate, l.payout_amount,
                p.cost_price_synthetic,
                CASE WHEN p.cost_price_synthetic > 0 AND l.payout_amount > 0
                     THEN ROUND((l.payout_amount - p.cost_price_synthetic) / l.payout_amount * 100, 1)
                     ELSE NULL END AS margin_net_pct
            FROM product p
            JOIN listing l ON l.product_id = p.id
            WHERE l.price IS NOT NULL AND l.price > 0
            ORDER BY margin_net_pct ASC
            LIMIT 100
            """
        ).fetchall()
    return templates.TemplateResponse(request, "seller.html", {"rows": rows})

@app.get("/api/rates")
def get_rates():
    with get_conn() as conn:
        rows = conn.execute("SELECT currency, rate_to_rub FROM exchangeRates").fetchall()
        rates = {r["currency"]: r["rate_to_rub"] for r in rows}
    return rates

# --- API для добавления новых справочных значений ---

@app.post("/api/add_type")
def add_type(new_type_name: str = Form(...)):
    with get_conn() as conn:
        conn.execute("INSERT INTO typeGoods (typeGoodName, sortOrder) VALUES (?, 200)", (new_type_name,))
        conn.commit()
    return RedirectResponse("/keeper/add_product", status_code=303)

@app.post("/api/add_edition")
def add_edition(new_edition_name: str = Form(...)):
    with get_conn() as conn:
        conn.execute("INSERT INTO editionTypes (editionName, sortOrder) VALUES (?, 200)", (new_edition_name,))
        conn.commit()
    return RedirectResponse("/keeper/add_product", status_code=303)

@app.post("/api/add_publisher")
def add_publisher(new_publisher_name: str = Form(...)):
    with get_conn() as conn:
        conn.execute("INSERT INTO publishers (publisherName) VALUES (?)", (new_publisher_name,))
        conn.commit()
    return RedirectResponse("/keeper/add_product", status_code=303)