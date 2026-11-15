from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.db import get_conn
from ._dicts import get_warehouses

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/manage_products", response_class=HTMLResponse)
def manage_products(
    request: Request, 
    parse_status: str = "",
    sort_by: str = "name",
    sort_dir: str = "asc",
    f_platform: str = "",
    f_edition: str = ""
):
    with get_conn() as conn:
        where = "WHERE p.isActive = 1"
        params = []
        
        if parse_status in ("ok", "needs_review"):
            where += " AND p.parseStatus = ?"
            params.append(parse_status)
        if f_platform:
            where += " AND pl.platformName || ' ' || pl.platformVersion = ?"
            params.append(f_platform)
        if f_edition:
            where += " AND ed.editionName = ?"
            params.append(f_edition)

        sort_map = {
            "name": "p.baseGameName",
            "platform": "pl.platformName",
            "edition": "ed.editionName",
            "warehouse": "s.warehouseId"
        }
        order_col = sort_map.get(sort_by, "p.baseGameName")
        order_dir = "DESC" if sort_dir == "desc" else "ASC"

        query = f"""
            SELECT p.productId AS id, p.offerId AS offer_id, p.baseGameName AS name,
                   pl.platformName || ' ' || pl.platformVersion AS platform,
                   ed.editionName AS edition,
                   pub.publisherName AS publisher,
                   r.regionCode AS region,
                   l.price AS ozon_price,
                   p.cost AS cost,
                   COALESCE(s.quantity, 0) AS quantity,
                   COALESCE(s.warehouseId, 1) AS warehouse_id,
                   p.parseStatus AS parse_status,
                   p.parseNote AS parse_note
            FROM products p
            LEFT JOIN platforms pl ON pl.platformId = p.platformId
            LEFT JOIN editionTypes ed ON ed.editionId = p.editionId
            LEFT JOIN publishers pub ON pub.publisherId = p.publisherId
            LEFT JOIN regions r ON r.regionId = p.regionId
            LEFT JOIN listings l ON l.productId = p.productId AND l.storeId = 1
            LEFT JOIN stocks s ON s.productId = p.productId
            {where}
            ORDER BY {order_col} {order_dir}
        """
        
        rows = conn.execute(query, params).fetchall()

        platforms = [row[0] for row in conn.execute("SELECT DISTINCT platformName || ' ' || platformVersion FROM platforms").fetchall()]
        editions = [row[0] for row in conn.execute("SELECT DISTINCT editionName FROM editionTypes").fetchall()]
        regions = [row[0] for row in conn.execute("SELECT DISTINCT regionCode FROM regions").fetchall()]
        publishers = [row[0] for row in conn.execute("SELECT DISTINCT publisherName FROM publishers").fetchall()]
        warehouses = get_warehouses(conn)

    return templates.TemplateResponse(request, "manage_products.html", {
        "rows": rows, "platforms": platforms, "editions": editions,
        "regions": regions, "publishers": publishers, "warehouses": warehouses,
        "parse_status": parse_status, "sort_by": sort_by, "sort_dir": sort_dir,
        "f_platform": f_platform, "f_edition": f_edition
    })