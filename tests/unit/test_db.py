"""
Тесты для src/db.py (v3.1).

Запуск: pytest tests/unit/test_db.py -v
"""
import sqlite3
import os
import pytest
from src.db import get_conn, init_db


TEST_DB_PATH = "db/test_only_limited.sqlite3"


def test_get_conn_returns_connection():
    """get_conn() возвращает соединение с БД (через with)."""
    with get_conn() as conn:
        assert isinstance(conn, sqlite3.Connection)


def test_get_conn_enables_foreign_keys():
    """get_conn() включает PRAGMA foreign_keys = ON."""
    with get_conn() as conn:
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1, "PRAGMA foreign_keys должен быть ON"


def test_get_conn_row_factory():
    """get_conn() использует row_factory = sqlite3.Row."""
    with get_conn() as conn:
        row = conn.execute("SELECT 1 AS test_value").fetchone()
        assert row["test_value"] == 1


def test_init_db_creates_tables():
    """init_db() создаёт все таблицы из schema.sql."""
    with get_conn() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = {t["name"] for t in tables}

    required = {
        "modules", "currencies", "regions", "platforms", "typeGoods",
        "editionTypes", "publishers", "statuses", "mediaTypes", "ageGroups",
        "adjustmentTypes", "exchangeRates",
        "purchasePlatforms", "marketplaces", "warehouses", "stores",
        "products", "listings", "productGenres", "productLanguages", "bundleItems",
        "stocks", "stockHistory", "returnReasons", "stockWriteOffs",
        "salesReturns", "purchaseReturns",
        "buyers", "salesOrders", "salesOrderItems", "salesOrderStatusHistory",
        "payouts", "payoutAdjustments", "syncLog",
    }
    missing = required - table_names
    assert not missing, f"Не хватает таблиц: {missing}"