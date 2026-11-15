from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path


from web.routers import keeper, api, seller, settings

app = FastAPI(title="Only_limited_magazin")
BASE_DIR = Path(__file__).resolve().parent

# Инициализация шаблонов
templates = Jinja2Templates(directory=BASE_DIR / "templates")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Подключаем роутеры
app.include_router(keeper.router)
app.include_router(api.router)
app.include_router(seller.router)
app.include_router(settings.router)

# =====================================================================
# БАЗОВЫЕ РОУТЫ
# =====================================================================
@app.get("/", response_class=HTMLResponse)
@app.head("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

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
        {"error_message": "Произошла ошибка при обработке запроса."},
        status_code=500
    )