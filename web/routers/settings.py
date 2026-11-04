from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.db import get_conn
import os
import subprocess
import sys
import time

router = APIRouter(prefix="/settings", tags=["settings"])
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/", response_class=HTMLResponse)
def settings_menu(request: Request):
    with get_conn() as conn:
        warehouses = conn.execute("SELECT id, name FROM warehouse WHERE is_active = 1").fetchall()
        platforms = conn.execute('SELECT "platformId", "platformName", "platformVersion" FROM platforms ORDER BY "sortOrder"').fetchall()
        editions = conn.execute('SELECT "editionId", "editionName" FROM "editionTypes" ORDER BY "sortOrder"').fetchall()
        publishers = conn.execute('SELECT "publisherId", "publisherName" FROM publishers ORDER BY "publisherName"').fetchall()
        regions = conn.execute('SELECT "regionId", "regionCode" FROM regions ORDER BY "sortOrder"').fetchall()
        
        # Площадки (уникальные platform из store)
        store_platforms = conn.execute("SELECT DISTINCT platform FROM store WHERE platform IS NOT NULL").fetchall()
        platforms_list = [r["platform"] for r in store_platforms]
        
        # Магазины (все)
        stores = conn.execute("SELECT code, name, platform FROM store").fetchall()
    
    return templates.TemplateResponse(request, "settings_menu.html", {
        "warehouses": warehouses,
        "platforms": platforms,
        "editions": editions,
        "publishers": publishers,
        "regions": regions,
        "platforms_list": platforms_list,
        "stores": stores,
    })

@router.get("/stores_by_platform")
def stores_by_platform(platform: str):
    """Возвращает список магазинов для выбранной площадки."""
    with get_conn() as conn:
        stores = conn.execute("SELECT code, name FROM store WHERE platform = ?", (platform,)).fetchall()
    return {"stores": [{"code": r["code"], "name": r["name"]} for r in stores]}

@router.post("/run_action")
def run_action(
    platform: str = Form(...),
    store_code: str = Form(...),
    action: str = Form(...)
):
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        python_exe = sys.executable
        
        # Явно указываем путь к скрипту и добавляем корень в PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        
        if action == "load_products":
            script_path = project_root / "src" / "scripts" / "fetch_products.py"
            cmd = [python_exe, str(script_path), platform, store_code]
        elif action == "load_postings":
            today = time.strftime("%Y-%m-%d")
            year_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 365*24*3600))
            script_path = project_root / "src" / "scripts" / "fetch_postings.py"
            cmd = [python_exe, str(script_path), platform, store_code, year_ago, today]
        else:
            return {"ok": False, "error": f"Неизвестное действие: {action}"}
        
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, cwd=str(project_root),
            env=env, timeout=300
        )
        
        return {
            "ok": True,
            "message": f"Действие '{action}' выполнено. Код возврата: {result.returncode}",
            "stdout": result.stdout[-3000:] if result.stdout else "",
            "stderr": result.stderr[-3000:] if result.stderr else ""
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Таймаут выполнения (более 5 минут)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/update_warehouse")
def update_warehouse(warehouse_id: int = Form(...), new_name: str = Form(...)):
    with get_conn() as conn:
        conn.execute("UPDATE warehouse SET name = ? WHERE id = ?", (new_name, warehouse_id))
        conn.commit()
    return JSONResponse({"ok": True, "message": f"Склад переименован в '{new_name}'"})

@router.post("/update_item")
def update_item(
    item_type: str = Form(...),
    item_id: int = Form(...),
    new_value: str = Form(...),
    new_version: str = Form(None)
):
    table_map = {
        "warehouse": ("warehouse", "id", "name"),
        "platform": ("platforms", "platformId", "platformName"),
        "edition": ("editionTypes", "editionId", "editionName"),
        "publisher": ("publishers", "publisherId", "publisherName"),
        "region": ("regions", "regionId", "regionCode"),
    }
    
    if item_type not in table_map:
        return JSONResponse({"ok": False, "error": f"Неизвестный тип: {item_type}"})
    
    table, id_field, value_field = table_map[item_type]
    
    with get_conn() as conn:
        conn.execute(f'UPDATE "{table}" SET "{value_field}" = ? WHERE "{id_field}" = ?', (new_value, item_id))
        if item_type == "platform" and new_version is not None:
            conn.execute(f'UPDATE "{table}" SET "platformVersion" = ? WHERE "{id_field}" = ?', (new_version, item_id))
        conn.commit()
    
    return JSONResponse({"ok": True, "message": f"Обновлено: {new_value}"})