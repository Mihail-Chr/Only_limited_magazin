"""
db.py — подключение к БД (v3.1).

get_conn() — контекстный менеджер (закрывает соединение всегда).
init_db() — создаёт таблицы из schema.sql.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import settings


@contextmanager
def get_conn():
    """
    Контекстный менеджер для соединения с БД.

    Автоматически закрывает соединение (даже при ошибке).
    Включает PRAGMA foreign_keys = ON и journal_mode = WAL.

    Использование:
        with get_conn() as conn:
            conn.execute("SELECT ...")
    """
    db_path_str = os.getenv("TEST_DB_PATH")
    db_path = Path(db_path_str) if db_path_str else settings.db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Создаёт БД из schema.sql (удаляет старую, если есть)."""
    db_path = Path(settings.db_path)
    if db_path.exists():
        db_path.unlink()
    schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(schema)