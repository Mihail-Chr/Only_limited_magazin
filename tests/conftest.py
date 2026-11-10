"""
Общие фикстуры для тестов (v3.1).

Примечание: web.app (FastAPI) НЕ импортируется.
Создание тестовой БД — в tests/unit/conftest.py (локально для unit-тестов).
"""
import pytest
import sqlite3
import os
from tests.unit.conftest import setup_test_db

TEST_DB_PATH = "db/test_only_limited.sqlite3"


@pytest.fixture
def db_conn():
    """Соединение с тестовой базой (с PRAGMA foreign_keys = ON)."""
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    yield conn
    conn.close()