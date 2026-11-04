from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from src.db import get_conn
from web.routers import keeper, api, seller

app = FastAPI(title="Only_limited_magazin")
BASE_DIR = Path(__file__).resolve().parent

# Инициализация шаблонов
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Загружаем склады один раз при старте
with get_conn() as conn:
    warehouses = conn.execute("SELECT code, name FROM warehouse WHERE is_active = 1").fetchall()
    # Преобразуем в список словарей, чтобы Jinja2 могла с ними работать
    warehouses_list = [{"code": row["code"], "name": row["name"]} for row in warehouses]

# Передаём склады во все шаблоны глобально
templates.env.globals["warehouses"] = warehouses_list

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Подключаем роутеры
app.include_router(keeper.router)
app.include_router(api.router)
app.include_router(seller.router)


# Главная страница (GET + HEAD)
@app.get("/", response_class=HTMLResponse)
@app.head("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

# Healthcheck
@app.get("/health")
@app.head("/health")
def health():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Ошибка: {exc}")
    return templates.TemplateResponse(
        request, 
        "error.html", 
        {"error_message": "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже."},
        status_code=500
    )