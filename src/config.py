import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


@dataclass
class Store:
    code: str
    name: str
    client_id: str | None
    api_key: str | None
    has_api: bool
    is_active: bool
    api_role: str | None


@dataclass
class Warehouse:
    code: str
    name: str
    default_currency: str
    supported_currencies: list[str]
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

    stores: list[Store] = field(default_factory=list)
    warehouses: list[Warehouse] = field(default_factory=list)

    data_dir: Path = BASE_DIR / "data"
    data_raw_xlsx: Path = BASE_DIR / "scratch" / "ozon_reports"
    data_api_raw: Path = BASE_DIR / "data" / "api_raw"
    data_exports: Path = BASE_DIR / "data" / "exports"
    log_dir: Path = BASE_DIR / "logs"

    log_level: str = "INFO"
    log_format: str = "json"
    app_secret_key: str = ""


def _load_stores() -> list[Store]:
    stores: list[Store] = []
    for i in (1, 2, 3):
        code = os.getenv(f"OZON_STORE_{i}_CODE")
        if not code:
            continue
        stores.append(
            Store(
                code=code,
                name=os.getenv(f"OZON_STORE_{i}_NAME", code),
                client_id=os.getenv(f"OZON_STORE_{i}_CLIENT_ID") or None,
                api_key=os.getenv(f"OZON_STORE_{i}_API_KEY") or None,
                has_api=_bool(os.getenv(f"OZON_STORE_{i}_HAS_API")),
                is_active=_bool(os.getenv(f"OZON_STORE_{i}_IS_ACTIVE"), True),
                api_role=os.getenv(f"OZON_STORE_{i}_API_ROLE") or None,
            )
        )
    return stores


def _load_warehouses() -> list[Warehouse]:
    warehouses: list[Warehouse] = []
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
                    for c in os.getenv(
                        f"WAREHOUSE_{i}_SUPPORTED_CURRENCIES", "RUB"
                    ).split(";")
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
        ozon_retry_max=int(os.getenv("OZON_API_RETRY_MAX", "3")),
        ozon_retry_backoff=int(os.getenv("OZON_API_RETRY_BACKOFF", "2")),
        ozon_rate_limit_per_sec=int(os.getenv("OZON_RATE_LIMIT_PER_SEC", "5")),
        stores=_load_stores(),
        warehouses=_load_warehouses(),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "json"),
        app_secret_key=os.getenv("APP_SECRET_KEY", ""),
    )


settings = load_settings()


def get_store(code: str) -> Store:
    for s in settings.stores:
        if s.code == code:
            return s
    raise KeyError(f"Магазин с кодом '{code}' не найден в .env")


def get_warehouse(code: str) -> Warehouse:
    for w in settings.warehouses:
        if w.code == code:
            return w
    raise KeyError(f"Склад с кодом '{code}' не найден в .env")