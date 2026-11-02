import pytest
import sqlite3
import os
from fastapi.testclient import TestClient

# Устанавливаем путь к тестовой базе ДО импорта приложения
TEST_DB_PATH = "db/test_only_limited.sqlite3"
os.environ["TEST_DB_PATH"] = TEST_DB_PATH

from web.app import app
from src.db import get_conn

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Создаем тестовую базу перед всеми тестами и удаляем после."""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    conn = sqlite3.connect(TEST_DB_PATH)
    with open("src/schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    
    # Наполняем тестовыми данными
    conn.execute("INSERT INTO warehouse (id, code, name, default_currency) VALUES (1, 'main', 'Основной', 'RUB')")
    conn.execute("INSERT INTO store (id, code, name, has_api) VALUES (1, 'limited_games', 'LimitedGames', 1)")
    conn.execute("INSERT INTO store (id, code, name, has_api) VALUES (2, 'manual', 'Ручная продажа', 0)")
    conn.execute("INSERT INTO buyer (buyerId, buyerNickname) VALUES (1, 'Физлицо')")
    
    conn.execute("""
        INSERT INTO product (id, offer_id, name, baseGameName, product_type, platform, is_active) 
        VALUES (1, 'TEST-001', 'Test Game (PS5)', 'Test Game', 'game', 'PlayStation 5', 1)
    """)
    conn.execute("INSERT INTO stock_manual (product_id, quantity) VALUES (1, 10)")
    
    conn.execute("""
        INSERT INTO product (id, offer_id, name, baseGameName, product_type, platform, is_active) 
        VALUES (2, 'TEST-002', 'Preorder Game (PS5)', 'Preorder Game', 'game', 'PlayStation 5', 1)
    """)
    conn.execute("INSERT INTO stock_manual (product_id, quantity) VALUES (2, 0)")
    
    conn.commit()
    conn.close()
    
    yield
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.fixture(scope="session")
def client():
    """Тестовый клиент FastAPI."""
    return TestClient(app)

@pytest.fixture
def db_conn():
    """Соединение с тестовой базой для проверок."""
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()