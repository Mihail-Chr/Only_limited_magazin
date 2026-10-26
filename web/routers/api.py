from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from src.db import get_conn

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/rates")
def get_rates():
    with get_conn() as conn:
        rows = conn.execute("SELECT currency, rate_to_rub FROM exchangeRates").fetchall()
        rates = {r["currency"]: r["rate_to_rub"] for r in rows}
    return rates

@router.post("/add_type")
def add_type(new_type_name: str = Form(...)):
    with get_conn() as conn:
        conn.execute('INSERT INTO "typeGoods" ("typeGoodName", "sortOrder") VALUES (?, 200)', (new_type_name,))
        conn.commit()
    return RedirectResponse("/keeper/add_product", status_code=303)

@router.post("/add_edition")
def add_edition(new_edition_name: str = Form(...)):
    with get_conn() as conn:
        conn.execute('INSERT INTO "editionTypes" ("editionName", "sortOrder") VALUES (?, 200)', (new_edition_name,))
        conn.commit()
    return RedirectResponse("/keeper/add_product", status_code=303)

@router.post("/add_publisher")
def add_publisher(new_publisher_name: str = Form(...)):
    with get_conn() as conn:
        conn.execute('INSERT INTO publishers ("publisherName") VALUES (?)', (new_publisher_name,))
        conn.commit()
    return RedirectResponse("/keeper/add_product", status_code=303)

@router.post("/add_platform")
def add_platform(platformName: str = Form(...), platformVersion: str = Form(...)):
    with get_conn() as conn:
        conn.execute(
            'INSERT INTO platforms ("platformName", "platformVersion", "sortOrder") VALUES (?, ?, 200)',
            (platformName, platformVersion)
        )
        conn.commit()
    return RedirectResponse("/keeper/add_product", status_code=303)