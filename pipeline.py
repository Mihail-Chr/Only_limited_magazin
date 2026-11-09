"""
pipeline.py — end-to-end сборка БД (v3.1).

Использование:
    python pipeline.py
    # или:
    .\run.bat python pipeline.py

Что делает:
1. init_db — создать БД из schema.sql.
2. seed_reference_data — заполнить справочники.
3. fetch_products (для каждого магазина) — загрузить товары.
4. fetch_postings (для каждого магазина) — загрузить продажи.
5. parse_names — разобрать названия (пишет ID).
6. Проверка — counts + 10 случайных примеров.

Конфиг: pipeline_config.json (временный, позже — из меню «Настройки»).
"""
import json
import sys
from pathlib import Path

# Корень проекта
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db import get_conn, init_db


CONFIG_PATH = PROJECT_ROOT / "pipeline_config.json"


# =====================================================================
# ШАГИ
# =====================================================================

def step_init_db() -> bool:
    """Шаг 1: создать БД из schema.sql."""
    print("[1/6] Инициализация БД...")
    try:
        init_db()
        with get_conn() as conn:
            tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
        print(f"  ✅ БД создана ({tables} таблиц)")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def step_seed_reference_data() -> bool:
    """Шаг 2: заполнить справочники."""
    print("[2/6] Заполнение справочников...")
    try:
        from src.scripts.seed_reference_data import main as seed_main
        seed_main()
        print("  ✅ Справочники заполнены")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def step_fetch_products(stores: list[dict]) -> bool:
    """Шаг 3: загрузить товары (для каждого магазина)."""
    print("[3/6] Загрузка товаров...")
    from src.scripts.fetch_products import fetch_products

    success = 0
    errors = []

    for store in stores:
        platform = store["platform"]
        store_code = store["store_code"]
        print(f"  → {platform}/{store_code}...")
        try:
            result = fetch_products(platform, store_code)
            if result["ok"]:
                print(f"    ✅ Создано: {result['inserted']}, обновлено: {result['updated']}")
                success += 1
            else:
                print(f"    ⚠️  Ошибка: {result['error']}")
                errors.append(f"{store_code}: {result['error']}")
        except Exception as e:
            print(f"    ⚠️  Исключение: {e}")
            errors.append(f"{store_code}: {e}")

    if success == 0:
        print(f"  ❌ Все магазины упали ({len(errors)} ошибок)")
        return False

    print(f"  ✅ Успешно: {success}/{len(stores)}")
    if errors:
        print(f"  ⚠️  Ошибок: {len(errors)}")
    return True


def step_fetch_postings(stores: list[dict]) -> bool:
    """Шаг 4: загрузить продажи (для каждого магазина). Мягко."""
    print("[4/6] Загрузка движения (продаж)...")

    # --- ПРОВЕРКА СХЕМЫ API (если есть сохраненные данные) ---
    from pathlib import Path
    import json
    from jsonschema import validate, ValidationError
    
    api_raw = Path("data/api_raw")
    files = list(api_raw.glob("*postings*.json"))
    if files:
        latest = max(files, key=lambda f: f.stat().st_mtime)
        try:
            with open(latest, encoding="utf-8") as f:
                data = json.load(f)
            # Простейшая проверка, что это список (или dict с postings)
            if isinstance(data, list):
                print("  ✅ Структура JSON (список) — ОК")
            else:
                print("  ⚠️ Структура JSON изменилась (не список) — проверьте!")
        except Exception as e:
            print(f"  ⚠️ Ошибка чтения JSON: {e}")
    # ---------------------------------------------------------

    from src.scripts.fetch_postings import fetch_postings

    success = 0
    errors = []

    for store in stores:
        platform = store["platform"]
        store_code = store["store_code"]
        date_from = store.get("date_from", "2022-01-01")
        date_to = store.get("date_to", "2026-12-31")
        print(f"  → {platform}/{store_code} ({date_from}—{date_to})...")
        try:
            result = fetch_postings(platform, store_code, date_from, date_to)
            if result["ok"]:
                print(f"    ✅ Создано: {result['inserted']}, ошибок: {len(result['errors'])}")
                success += 1
            else:
                print(f"    ⚠️  Ошибка: {result['error']}")
                errors.append(f"{store_code}: {result['error']}")
        except Exception as e:
            print(f"    ⚠️  Исключение: {e}")
            errors.append(f"{store_code}: {e}")

    if success == 0:
        print(f"  ⚠️  Все магазины упали ({len(errors)} ошибок). Продолжаем.")
        return True  # мягко — продолжаем

    print(f"  ✅ Успешно: {success}/{len(stores)}")
    if errors:
        print(f"  ⚠️  Ошибок: {len(errors)}")
    return True


def step_parse_names() -> bool:
    """Шаг 5: разобрать названия (пишет ID). Критично, если есть товары."""
    print("[5/6] Разбор названий...")

    # Проверка: есть ли товары
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    if count == 0:
        print("  ⚠️  Нет товаров для разбора. Пропуск.")
        return True  # мягко (но товаров нет — это уже проблема)

    try:
        from src.scripts.parse_names import main as parse_main
        parse_main()
        print("  ✅ Названия разобраны")
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def step_check() -> None:
    """Шаг 6: проверка (counts + 10 примеров)."""
    print("[6/6] Проверка...")
    with get_conn() as conn:
        print(f"  products: {conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]}")
        print(f"  listings: {conn.execute('SELECT COUNT(*) FROM listings').fetchone()[0]}")
        print(f"  salesOrders: {conn.execute('SELECT COUNT(*) FROM salesOrders').fetchone()[0]}")
        print(f"  salesOrderItems: {conn.execute('SELECT COUNT(*) FROM salesOrderItems').fetchone()[0]}")
        print(f"  salesOrderStatusHistory: {conn.execute('SELECT COUNT(*) FROM salesOrderStatusHistory').fetchone()[0]}")
        print(f"  statuses: {conn.execute('SELECT COUNT(*) FROM statuses').fetchone()[0]}")

        print("\n  Случайные 10 товаров:")
        samples = conn.execute("""
            SELECT productId, offerId, name, baseGameName,
                   platformId, editionId, publisherId, typeGoodId,
                   mediaTypeId, regionId, restore
            FROM products
            ORDER BY RANDOM()
            LIMIT 10
        """).fetchall()

        for s in samples:
            print(f"    productId: {s['productId']}, offerId: {s['offerId']}")
            print(f"      name: {s['name']}")
            print(f"      baseGameName: {s['baseGameName']}")
            print(f"      platformId: {s['platformId']}, editionId: {s['editionId']}, publisherId: {s['publisherId']}")
            print(f"      typeGoodId: {s['typeGoodId']}, mediaTypeId: {s['mediaTypeId']}, regionId: {s['regionId']}, restore: {s['restore']}")
            print()

def step_clean_stubs() -> bool:
    """Шаг 5.5: Удаление заглушек (Товар N)."""
    print("[5.5/6] Очистка заглушек...")
    try:
        from src.scripts.clean_stubs import main as clean_main
        clean_main()
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("=" * 60)
    print("PIPELINE v3.1")
    print("=" * 60)

    # 0. Загрузить конфиг
    if not CONFIG_PATH.exists():
        print(f"❌ Конфиг не найден: {CONFIG_PATH}")
        print("Создайте pipeline_config.json (пример в HISTORY.md)")
        sys.exit(1)

    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в конфиге: {e}")
        sys.exit(1)

    stores = config.get("stores", [])
    if not stores:
        print("❌ В конфиге нет stores")
        sys.exit(1)

    print(f"Магазинов: {len(stores)}")
    for s in stores:
        print(f"  - {s['platform']}/{s['store_code']} ({s.get('date_from')}—{s.get('date_to')})")
    print()

    # 1. init_db (критично)
    if not step_init_db():
        print("\n❌ Pipeline остановлен (init_db)")
        sys.exit(1)

    # 2. seed_reference_data (критично)
    if not step_seed_reference_data():
        print("\n❌ Pipeline остановлен (seed_reference_data)")
        sys.exit(1)

    # 3. fetch_products (критично, если все упали)
    if not step_fetch_products(stores):
        print("\n❌ Pipeline остановлен (fetch_products)")
        sys.exit(1)

    # 4. fetch_postings (мягко)
    step_fetch_postings(stores)

    # 5. parse_names (критично, если есть товары)
    if not step_parse_names():
        print("\n❌ Pipeline остановлен (parse_names)")
        sys.exit(1)

    # 5.5 clean_stubs (очистка заглушек)
    step_clean_stubs()

    # 6. Проверка (всегда)
    print()
    step_check()
    
    print("=" * 60)
    print("✅ Pipeline завершён")
    print("=" * 60)


if __name__ == "__main__":
    main()