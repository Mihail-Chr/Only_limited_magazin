"""
settings/refs.py — POST /settings/add_item, POST /settings/delete_item.

Добавление и удаление записей в справочниках.
Проверка на использование при удалении (внешние ключи).
"""
import sqlite3
import web
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse


from src.db import get_conn

router = APIRouter()

TABLE_MAP = {
    "warehouse": {
        "table": "warehouses",
        "id": "warehouseId",
        "fields": {"name": "name", "code": "code"},
        "check_ref": "stocks", "check_col": "warehouseId"
    },
    "platform": {
        "table": "platforms",
        "id": "platformId",
        "fields": {"name": "platformName", "version": "platformVersion"},
        "check_ref": "products", "check_col": "platformId"
    },
    "edition": {
        "table": "editionTypes",
        "id": "editionId",
        "fields": {"name": "editionName"},
        "check_ref": "products", "check_col": "editionId"
    },
    "publisher": {
        "table": "publishers",
        "id": "publisherId",
        "fields": {"name": "publisherName"},
        "check_ref": "products", "check_col": "publisherId"
    },
    "region": {
        "table": "regions",
        "id": "regionId",
        "fields": {"name": "regionCode", "full_name": "regionName"},
        "check_ref": "products", "check_col": "regionId"
    },
}


@router.post("/add_item")
def add_item(
    item_type: str = Form(...),
    name: str = Form(...),
    version: str = Form(None),
    code: str = Form(None),
    full_name: str = Form(None)
):
    if item_type not in TABLE_MAP:
        return JSONResponse({"ok": False, "error": f"Неизвестный тип: {item_type}"})

    try:
        with get_conn() as conn:
            if item_type == "warehouse":
                conn.execute("INSERT INTO warehouses (code, name) VALUES (?, ?)", (code or f"wh_{int(time.time())}", name))
            elif item_type == "platform":
                conn.execute("INSERT INTO platforms (platformName, platformVersion) VALUES (?, ?)", (name, version or "—"))
            elif item_type == "region":
                conn.execute("INSERT INTO regions (regionCode, regionName) VALUES (?, ?)", (name, full_name or name))
            elif item_type == "edition":
                conn.execute("INSERT INTO editionTypes (editionName, sortOrder, isActive, createdBy) VALUES (?, 999, 1, 'manual')", (name,))
            elif item_type == "publisher":
                conn.execute("INSERT INTO publishers (publisherName, sortOrder, isActive) VALUES (?, 999, 1)", (name,))
            
            conn.commit()
            
            return JSONResponse({"ok": True, "message": "Добавлено"})
    except sqlite3.IntegrityError:
        return JSONResponse({"ok": False, "error": "Такая запись уже существует"}, status_code=400)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.post("/delete_item")
def delete_item(
    item_type: str = Form(...),
    item_id: int = Form(...)
):
    if item_type not in TABLE_MAP:
        return JSONResponse({"ok": False, "error": f"Неизвестный тип: {item_type}"})

    cfg = TABLE_MAP[item_type]
    table = cfg["table"]
    id_field = cfg["id"]
    check_ref = cfg["check_ref"]
    check_col = cfg["check_col"]

    with get_conn() as conn:
        # 1. Проверяем, используется ли в других таблицах
        used = conn.execute(
            f'SELECT COUNT(*) FROM "{check_ref}" WHERE "{check_col}" = ?',
            (item_id,)
        ).fetchone()[0]

        if used > 0:
            return JSONResponse({
                "ok": False,
                "error": f"Нельзя удалить: используется в {used} записях товаров/остатков"
            }, status_code=400)

        # 2. Удаляем
        conn.execute(f'DELETE FROM "{table}" WHERE "{id_field}" = ?', (item_id,))
        conn.commit()
        
    return JSONResponse({"ok": True, "message": "Удалено"})