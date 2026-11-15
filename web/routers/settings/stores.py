"""
settings/stores.py — GET /settings/stores_by_platform.

Магазины для выбранной площадки (JOIN stores + marketplaces).
"""
from fastapi import APIRouter

from src.db import get_conn

router = APIRouter()


@router.get("/stores_by_platform")
def stores_by_platform(platform: str):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT s.code, s.name
            FROM stores s
            JOIN marketplaces m ON m.marketplaceId = s.marketplaceId
            WHERE m.code = ? AND s.isActive = 1
            ORDER BY s.sortOrder
        """, (platform,)).fetchall()

    return {"stores": [{"code": r["code"], "name": r["name"]} for r in rows]}