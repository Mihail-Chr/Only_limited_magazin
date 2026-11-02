def test_main_page(client):
    """Проверка, что главная страница открывается."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Выберите роль" in response.text

def test_inventory_page(client):
    """Проверка, что инвентаризация открывается."""
    response = client.get("/keeper/inventory")
    assert response.status_code == 200
    assert "Инвентаризация склада" in response.text

def test_manual_sale(client, db_conn):
    """Проверка ручной продажи (списание остатка)."""
    # Продаем 2 штуки товара с ID=1 (у него остаток 10)
    response = client.post("/seller/manual_sale", data={
        "product_id": 1,
        "quantity": 2,
        "sale_price": 1000,
        "order_date": "2026-11-02",
        "buyer_nickname": "Тестовый Покупатель"
    })
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["ok"] is True
    
    # Проверяем, что остаток уменьшился с 10 до 8
    row = db_conn.execute("SELECT quantity FROM stock_manual WHERE product_id = 1").fetchone()
    assert row["quantity"] == 8
    
    # Проверяем, что продажа записалась в posting
    posting = db_conn.execute("SELECT * FROM posting WHERE source = 'manual' ORDER BY id DESC LIMIT 1").fetchone()
    assert posting is not None
    assert posting["buyer_nickname"] == "Тестовый Покупатель"

def test_manual_sale_fail_no_stock(client):
    """Проверка, что нельзя продать больше, чем есть."""
    response = client.post("/seller/manual_sale", data={
        "product_id": 2, # У этого товара остаток 0
        "quantity": 1,
        "sale_price": 1000,
        "order_date": "2026-11-02",
        "buyer_nickname": "Физлицо"
    })
    assert response.status_code == 400
    assert response.json()["ok"] is False

def test_parser_logic():
    """Проверка, что парсер работает (изолированно)."""
    from src.scripts.parse_names import parse_name
    result = parse_name("Видеоигра Test Game (PS5)")
    assert result["base_name"] == "Test Game"
    assert result["platform"] == "PlayStation 5"