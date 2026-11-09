"""
Инициализация БД: создаёт все таблицы из schema.sql.

Запуск: python -m src.scripts.init_db

ВНИМАНИЕ: если БД уже существует — таблицы НЕ удаляются (CREATE TABLE IF NOT EXISTS).
Для полной пересоздание — удалить файл БД вручную.
"""
import sys
from pathlib import Path
from src.db import init_db, get_conn
from src.config import settings


def main():
    db_path = Path(settings.db_path)
    print(f"БД: {db_path}")

    if db_path.exists():
        print(f"⚠️  БД уже существует: {db_path}")
        print("   Таблицы будут созданы только если их нет (CREATE TABLE IF NOT EXISTS).")
        print("   Для полного пересоздания — удалите файл и запустите снова.")
    else:
        print(f"✅ БД не существует — будет создана.")

    init_db()
    print("✅ БД инициализирована.")

    # Проверка PRAGMA foreign_keys
    with get_conn() as conn:
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        print(f"PRAGMA foreign_keys = {fk} ({'ON' if fk else 'OFF'})")
        if not fk:
            print("❌ ОШИБКА: PRAGMA foreign_keys = OFF!")
            sys.exit(1)

        # Проверка: сколько таблиц создано
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        print(f"Создано таблиц: {len(tables)}")
        for t in tables:
            print(f"  - {t['name']}")


if __name__ == "__main__":
    main()