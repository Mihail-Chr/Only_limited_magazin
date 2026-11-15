"""
Тесты для роутеров Кладовщика (API).
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from web.routers.keeper import inventory_update, products_price, products_delete, products_save

app = FastAPI()
app.include_router(inventory_update.router, prefix="/keeper")
app.include_router(products_price.router, prefix="/keeper")
app.include_router(products_delete.router, prefix="/keeper")
app.include_router(products_save.router, prefix="/keeper")

client = TestClient(app)

# =====================================================================
# INVENTORY_UPDATE
# =====================================================================

def test_update_stock_inline_success(db_conn):
    """Успешное обновление остатка и склада."""
    # В seed есть товар? Нет, создадим
    db_conn.execute("INSERT INTO products (productId, offerId, name) VALUES (100, 'TEST-STOCK', 'Test')")
    db_conn.commit()
    
    response = client.post("/keeper/update_stock_inline", json={
        "product_id": 100, "warehouse_id": 1, "quantity": 5
    })
    assert response.status_code == 200
    assert response.json()["ok"] is True
    
    # Проверяем в БД
    row = db_conn.execute("SELECT quantity FROM stocks WHERE productId = 100 AND warehouseId = 1").fetchone()
    assert row is not None
    assert row["quantity"] == 5


def test_update_stock_inline_negative_fails(db_conn):
    """Отрицательное количество — ошибка 400."""
    response = client.post("/keeper/update_stock_inline", json={
        "product_id": 1, "warehouse_id": 1, "quantity": -5
    })
    assert response.status_code == 400
    assert "отрицательным" in response.json()["error"]


# =====================================================================
# PRODUCTS_PRICE
# =====================================================================

def test_update_price_inline_success(db_conn):
    """Успешное обновление входной цены и цены OZON."""
    db_conn.execute("INSERT INTO products (productId, offerId, name) VALUES (101, 'TEST-PRICE', 'Test')")
    db_conn.commit()
    
    response = client.post("/keeper/update_price_inline", json={
        "product_id": 101, "cost": 500.0, "ozon_price": 1000.0
    })
    assert response.status_code == 200
    assert response.json()["ok"] is True
    
    # Проверяем products.cost
    row = db_conn.execute("SELECT cost FROM products WHERE productId = 101").fetchone()
    assert row["cost"] == 500.0
    
    # Проверяем listings.price
    row = db_conn.execute("SELECT price FROM listings WHERE productId = 101").fetchone()
    assert row["price"] == 1000.0


# =====================================================================
# PRODUCTS_DELETE
# =====================================================================

def test_delete_product_physical(db_conn):
    """Физическое удаление, если нет продаж."""
    db_conn.execute("INSERT INTO products (productId, offerId, name) VALUES (102, 'TEST-DEL', 'Test')")
    db_conn.commit()
    
    response = client.post("/keeper/delete_product/102")
    assert response.status_code == 200
    assert response.json()["mode"] == "physical"
    
    row = db_conn.execute("SELECT productId FROM products WHERE productId = 102").fetchone()
    assert row is None


def test_delete_product_with_sales_fails(db_conn):
    """Нельзя удалить, если есть продажи (salesOrderItems)."""
    # Создаем товар, заказ и позицию
    db_conn.execute("INSERT INTO products (productId, offerId, name) VALUES (103, 'TEST-DEL-SALES', 'Test')")
    db_conn.execute("INSERT INTO buyers (buyerId, buyerNickname) VALUES (99, 'TestBuyer')")
    db_conn.execute("INSERT INTO salesOrders (salesOrderId, buyerId, marketplaceId, currencyId) VALUES (99, 99, 1, 1)")
    db_conn.execute("INSERT INTO salesOrderItems (salesOrderItemId, salesOrderId, productId, quantity, salePrice, warehouseId) VALUES (99, 99, 103, 1, 100, 1)")
    db_conn.commit()
    
    response = client.post("/keeper/delete_product/103")
    assert response.status_code == 400
    assert "Нельзя удалить" in response.json()["error"]


# =====================================================================
# PRODUCTS_SAVE
# =====================================================================

def test_save_product_add_success(db_conn):
    """Создание нового товара."""
    # Проверяем, что его нет
    row = db_conn.execute("SELECT productId FROM products WHERE offerId = 'NEW-TEST'").fetchone()
    assert row is None

    response = client.post("/keeper/save_product", data={
        "mode": "add",
        "offerId": "NEW-TEST",
        "baseGameName": "New Game",
        "typeGoodId": 1,      # game
        "platformId": 3,      # PlayStation 5
        "quantity": 2,
        "warehouse_id": 1
    })
    assert response.status_code == 200
    assert response.json()["ok"] is True

    # Проверяем, что создался
    row = db_conn.execute("SELECT productId, name FROM products WHERE offerId = 'NEW-TEST'").fetchone()
    assert row is not None
    assert row["name"] == "New Game"


def test_save_product_duplicate_fails(db_conn):
    """Проверка дубля по 8 полям."""
    # Создаем товар
    client.post("/keeper/save_product", data={
        "mode": "add", "offerId": "DUP-1", "baseGameName": "Dup Game",
        "typeGoodId": 1, "platformId": 3, "quantity": 1, "warehouse_id": 1
    })
    
    # Пытаемся создать второй с такими же полями, но другим offerId
    response = client.post("/keeper/save_product", data={
        "mode": "add", "offerId": "DUP-2", "baseGameName": "Dup Game",
        "typeGoodId": 1, "platformId": 3, "quantity": 1, "warehouse_id": 1
    })
    assert response.status_code == 400
    assert "уже есть" in response.json()["error"]