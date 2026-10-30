import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

def _bool(v: Optional[str], default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")

@dataclass
class Store:
    platform: str
    code: str
    store_id: str
    store_key: str
    name: str

@dataclass
class Warehouse:
    code: str
    name: str
    default_currency: str
    supported_currencies: List[str]
    is_active: bool

@dataclass
class Settings:
    app_name: str
    app_env: str
    app_debug: bool
    timezone: str

    db_driver: str
    db_path: Path

    ozon_base_url: str
    ozon_timeout: int
    ozon_retry_max: int
    ozon_retry_backoff: int
    ozon_rate_limit_per_sec: int

    stores: Dict[str, Dict[str, Store]] = field(default_factory=dict)
    warehouses: List[Warehouse] = field(default_factory=list)

    data_dir: Path = BASE_DIR / "data"
    data_api_raw: Path = BASE_DIR / "data" / "api_raw"
    data_exports: Path = BASE_DIR / "data" / "exports"
    log_dir: Path = BASE_DIR / "logs"

    log_level: str = "INFO"
    log_format: str = "json"

def _load_stores() -> Dict[str, Dict[str, Store]]:
    """Собирает магазины из плоских переменных .env в словарь."""
    stores = {}
    platforms = ["ozon", "wb", "ym", "avito", "vk"]
    
    for platform in platforms:
        prefix = platform.upper()
        store_codes_str = os.getenv(f"{prefix}_STORES", "")
        if not store_codes_str:
            continue
        
        stores[platform] = {}
        store_codes = [c.strip() for c in store_codes_str.split(",") if c.strip()]
        
        for code in store_codes:
            store_id = os.getenv(f"{prefix}_{code.upper()}_ID")
            store_key = os.getenv(f"{prefix}_{code.upper()}_KEY")
            store_name = os.getenv(f"{prefix}_{code.upper()}_NAME", code)
            
            # Проверка на пустые значения
            if not store_id or not store_key:
                print(f"⚠️ Магазин '{code}' на площадке '{platform}' пропущен: не заданы ID или KEY")
                continue
            
            stores[platform][code] = Store(
                platform=platform,
                code=code,
                store_id=store_id,
                store_key=store_key,
                name=store_name,
            )
    
    return stores

def _load_warehouses() -> List[Warehouse]:
    warehouses = []
    for i in (1,):
        code = os.getenv(f"WAREHOUSE_{i}_CODE")
        if not code:
            continue
        warehouses.append(
            Warehouse(
                code=code,
                name=os.getenv(f"WAREHOUSE_{i}_NAME", code),
                default_currency=os.getenv(f"WAREHOUSE_{i}_DEFAULT_CURRENCY", "RUB"),
                supported_currencies=[
                    c.strip()
                    for c in os.getenv(f"WAREHOUSE_{i}_SUPPORTED_CURRENCIES", "RUB").split(";")
                    if c.strip()
                ],
                is_active=_bool(os.getenv(f"WAREHOUSE_{i}_IS_ACTIVE"), True),
            )
        )
    return warehouses

def load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Only_limited_magazin"),
        app_env=os.getenv("APP_ENV", "development"),
        app_debug=_bool(os.getenv("APP_DEBUG")),
        timezone=os.getenv("APP_TIMEZONE", "Europe/Moscow"),
        db_driver=os.getenv("DB_DRIVER", "sqlite"),
        db_path=(BASE_DIR / os.getenv("DB_PATH", "./db/only_limited.sqlite3")).resolve(),
        ozon_base_url=os.getenv("OZON_API_BASE_URL", "https://api-seller.ozon.ru"),
        ozon_timeout=int(os.getenv("OZON_API_TIMEOUT", "30").split("#")[0].strip()),
        ozon_retry_max=int(os.getenv("OZON_API_RETRY_MAX", "3").split("#")[0].strip()),
        ozon_retry_backoff=int(os.getenv("OZON_API_RETRY_BACKOFF", "2").split("#")[0].strip()),
        ozon_rate_limit_per_sec=int(os.getenv("OZON_RATE_LIMIT_PER_SEC", "5").split("#")[0].strip()),
        stores=_load_stores(),
        warehouses=_load_warehouses(),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "json"),
    )

settings = load_settings()

def get_store(platform: str, code: str) -> Store:
    """Возвращает магазин по площадке и коду."""
    if platform not in settings.stores:
        raise KeyError(f"Площадка '{platform}' не найдена в .env")
    if code not in settings.stores[platform]:
        raise KeyError(f"Магазин '{code}' на площадке '{platform}' не найден")
    return settings.stores[platform][code]

def get_warehouse(code: str) -> Warehouse:
    for w in settings.warehouses:
        if w.code == code:
            return w
    raise KeyError(f"Склад '{code}' не найден в .env")