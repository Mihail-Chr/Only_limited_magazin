from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from web.routers import keeper, api, seller

app = FastAPI(title="Only_limited_magazin")
BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Подключаем роутеры
app.include_router(keeper.router)
app.include_router(api.router)
app.include_router(seller.router)


# Главная страница (GET + HEAD)
@app.get("/", response_class=HTMLResponse)
@app.head("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


# Healthcheck для Timeweb (GET + HEAD)
@app.get("/health")
@app.head("/health")
def health():
    return {"status": "ok"}