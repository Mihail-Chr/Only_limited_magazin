"""
settings/backup.py — GET /settings/backup.

Скачать текущую БД (.sqlite3).
"""
import time
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from src.config import settings as app_settings

router = APIRouter()


@router.get("/backup")
def backup_db():
    db_path = Path(app_settings.db_path)
    if not db_path.exists():
        return JSONResponse({"ok": False, "error": "БД не найдена"}, status_code=404)

    stamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"only_limited_{stamp}.sqlite3"

    return FileResponse(
        path=str(db_path),
        filename=filename,
        media_type="application/x-sqlite3",
    )