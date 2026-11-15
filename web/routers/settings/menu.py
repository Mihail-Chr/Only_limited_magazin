"""
settings/menu.py — GET /settings/ (меню Настроек).
"""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.db import get_conn
from ._dicts import get_settings_dicts

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", response_class=HTMLResponse)
def settings_menu(request: Request):
    with get_conn() as conn:
        ctx = get_settings_dicts(conn)

    return templates.TemplateResponse(request, "settings_menu.html", ctx)