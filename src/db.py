import os
import sqlite3
from pathlib import Path
from .config import settings

def get_conn() -> sqlite3.Connection:
    # Если задана переменная TEST_DB_PATH (для тестов) - используем её
    db_path_str = os.getenv("TEST_DB_PATH")
    db_path = Path(db_path_str) if db_path_str else settings.db_path
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db() -> None:
    schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    with get_conn() as conn:
        conn.executescript(schema)