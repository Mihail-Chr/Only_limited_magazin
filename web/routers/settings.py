from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.db import get_conn
import os
import subprocess
import sys

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
    
    return templates.TemplateResponse(request, "settings_menu.html", {
        "warehouses": warehouses,
        "platforms": platforms,
        "editions": editions,
        "publishers": publishers,
        "regions": regions,
    })

@router.get("/load_status")
def load_status():
    """Проверяет, завершилась ли загрузка (по наличию свежего файла в data/api_raw)."""
    api_raw_dir = Path("data/api_raw")
    if not api_raw_dir.exists():
        return {"ok": False, "error": "Папка data/api_raw не найдена"}
    
    # Ищем самый свежий файл product_list
    files = sorted(api_raw_dir.glob("*_product_list_*.json"), key=os.path.getmtime, reverse=True)
    if not files:
        return {"ok": False, "error": "Файлы загрузки не найдены"}
    
    latest = files[0]
    mtime = os.path.getmtime(latest)
    now = time.time()
    
    # Если файл создан менее 60 секунд назад — считаем, что загрузка завершена
    if now - mtime < 60:
        return {"ok": True, "status": "completed", "file": latest.name, "mtime": mtime}
    else:
        return {"ok": True, "status": "in_progress", "file": latest.name, "mtime": mtime}

@router.post("/load_products")
def load_products(store_code: str = "limited_games"):
    try:
        # Указываем рабочую директорию (корень проекта)
        project_root = BASE_DIR.parent.parent  # web/routers -> web -> корень
        log_path = project_root / "data" / "load_products.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        log_file = open(log_path, "w", encoding="utf-8")
        
        process = subprocess.Popen(
            [sys.executable, "-m", "src.scripts.fetch_products", "ozon", store_code],
            stdout=log_file,
            stderr=log_file,
            text=True,
            cwd=str(project_root)  # <-- ВАЖНО: рабочая директория = корень проекта
        )
        return {"ok": True, "message": f"Загрузка карточек для {store_code} запущена. Смотрите лог: data/load_products.log"}
    except Exception as e:
        return {"ok": False, "error": str(e)}