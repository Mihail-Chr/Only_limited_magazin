"""
settings/restore.py — POST /settings/restore.

Загрузить БД из файла:
1. Проверить расширение (.sqlite3).
2. Проверить схему (есть ли products, salesOrders).
3. Сохранить текущую как .bak.
4. Заменить.
"""
import shutil
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

from src.config import settings as app_settings

router = APIRouter()


def _check_schema(path: str) -> bool:
    """Проверяет, что это наша БД (есть таблицы products, salesOrders)."""
    import sqlite3
    try:
        conn = sqlite3.connect(path)
        try:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            return "products" in tables and "salesOrders" in tables
        finally:
            conn.close()
    except Exception:
        return False


@router.post("/restore")
async def restore_db(file: UploadFile = File(...)):
    if not file.filename.endswith(".sqlite3"):
        return JSONResponse(
            {"ok": False, "error": "Нужен файл .sqlite3"},
            status_code=400,
        )

    tmp_dir = Path(tempfile.gettempdir())
    tmp_path = tmp_dir / f"restore_{int(time.time())}.sqlite3"

    try:
        content = await file.read()
        tmp_path.write_bytes(content)

        if not _check_schema(str(tmp_path)):
            tmp_path.unlink(missing_ok=True)
            return JSONResponse(
                {"ok": False, "error": "Неверный файл БД: нет таблиц products/salesOrders"},
                status_code=400,
            )

        db_path = Path(app_settings.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        backup_path = db_path.with_suffix(".sqlite3.bak")
        if db_path.exists():
            shutil.copy2(db_path, backup_path)

        shutil.copy2(tmp_path, db_path)
        tmp_path.unlink(missing_ok=True)

        return JSONResponse({
            "ok": True,
            "message": "БД восстановлена. Предыдущая сохранена как .bak",
        })
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)