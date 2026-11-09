"""
Локальные фикстуры для unit-тестов.

Создаёт тестовую БД из schema.sql и наполняет справочниками
(через seed_reference_data.py).
"""
import pytest
import sqlite3
import os
from src.db import init_db


TEST_DB_PATH = "db/test_only_limited.sqlite3"


@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Создаёт тестовую БД перед КАЖДЫМ тестом (изоляция).
    Удаляет после.
    """
    os.environ["TEST_DB_PATH"] = TEST_DB_PATH

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # Создаём БД из schema.sql
    init_db()

    # Наполняем справочниками
    from src.scripts.seed_reference_data import (
        seed_modules, seed_currencies, seed_regions, seed_platforms,
        seed_typeGoods, seed_editionTypes, seed_publishers, seed_statuses,
        seed_mediaTypes, seed_ageGroups, seed_adjustmentTypes,
        seed_warehouses, seed_marketplaces, seed_purchasePlatforms,
        seed_stores, seed_buyers,
    )
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    seed_modules(conn)
    seed_currencies(conn)
    seed_regions(conn)
    seed_platforms(conn)
    seed_typeGoods(conn)
    seed_editionTypes(conn)
    seed_publishers(conn)
    seed_statuses(conn)
    seed_mediaTypes(conn)
    seed_ageGroups(conn)
    seed_adjustmentTypes(conn)
    seed_warehouses(conn)
    seed_marketplaces(conn)
    seed_purchasePlatforms(conn)
    seed_stores(conn)
    seed_buyers(conn)
    conn.commit()
    conn.close()

    yield

    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass