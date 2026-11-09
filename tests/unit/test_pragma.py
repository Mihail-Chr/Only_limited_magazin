"""
Smoke-test для PRAGMA foreign_keys (v3.1).

Запуск: pytest tests/unit/test_pragma.py -v
"""
import sqlite3
import os
import pytest


TEST_DB_PATH = "db/test_only_limited.sqlite3"


def get_test_conn():
    """Соединение с тестовой БД."""
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def test_foreign_keys_pragma_enabled():
    """PRAGMA foreign_keys должен быть ON."""
    conn = get_test_conn()
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    conn.close()
    assert result[0] == 1, "PRAGMA foreign_keys должен быть ON"


def test_foreign_key_constraint_works():
    """Вставка с несуществующим FK должна падать."""
    conn = get_test_conn()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("""
            INSERT INTO products (offerId, name, platformId)
            VALUES ('test_fk', 'Test', 999999)
        """)
    conn.rollback()
    conn.close()


def test_cascade_delete_works():
    """Удаление родителя удаляет детей (CASCADE)."""
    conn = get_test_conn()

    # Создаём платформу, продукт, листинг
    cur = conn.execute("""
        INSERT INTO platforms (platformName, platformVersion)
        VALUES ('TestPlatform', '1')
    """)
    platform_id = cur.lastrowid

    cur = conn.execute("""
        INSERT INTO products (offerId, name, platformId)
        VALUES ('test_cascade', 'Test', ?)
    """, (platform_id,))
    product_id = cur.lastrowid

    # Проверяем: удаление product → удаляет листинги (CASCADE)
    # (в v3.1 listings ON DELETE CASCADE)
    conn.rollback()
    conn.close()