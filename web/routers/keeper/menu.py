"""
menu.py — GET /keeper/ (меню Кладовщика).
"""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", response_class=HTMLResponse)
def keeper_menu(request: Request):
    return templates.TemplateResponse(request, "keeper_menu.html")