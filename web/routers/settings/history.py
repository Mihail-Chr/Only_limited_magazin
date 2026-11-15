"""
settings/history.py — GET /settings/history.

Возвращает историю загрузок из syncLog (JSON).
"""
from fastapi import APIRouter
from src.db import get_conn

router = APIRouter()


@router.get("/history")
def get_history(limit: int = 50):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, syncType, dateFrom, dateTo, recordsCount, syncedAt, notes
            FROM syncLog
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return {"history": [dict(r) for r in rows]}