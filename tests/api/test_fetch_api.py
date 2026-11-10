import pytest
import sqlite3
from pathlib import Path
from src.scripts.fetch_postings import fetch_postings

TEST_DB_PATH = "db/test_only_limited.sqlite3"

@pytest.fixture
def mock_ozon_client(mocker):
    """Мокаем OzonClient, чтобы он не ходил в реальный API."""
    mock = mocker.patch("src.scripts.fetch_postings._create_client")
    client_instance = mock.return_value
    
    # Фейковый ответ от OZON
    client_instance.get_postings.return_value = [
        {
            "posting_number": "TEST-API-001",
            "status": "delivered",
            "created_at": "2026-11-10T10:00:00Z",
            "products": [
                {"offer_id": "TEST-ITEM-1", "quantity": 2, "price": {"amount": "1500", "currency": "RUB"}}
            ]
        }
    ]
    return client_instance

def test_fetch_postings_api_integration(mock_ozon_client, monkeypatch, tmp_path, setup_test_db):
    """Проверяем, что fetch_postings корректно парсит мок-ответ API и пишет в БД."""
    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")
    
    # Перенаправляем сохранение JSON в tmp_path
    import src.scripts.fetch_postings as fp
    monkeypatch.setattr(fp, "DATA_API_RAW", tmp_path / "api_raw")

    # Вызываем функцию
    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-10")
    
    assert result["ok"] is True
    assert result["inserted"] == 1
    
    # Проверяем, что данные реально в базе
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    order = conn.execute("SELECT marketplaceOrderId FROM salesOrders WHERE marketplaceOrderId = 'TEST-API-001'").fetchone()
    assert order is not None
    
    item = conn.execute("SELECT quantity, salePrice FROM salesOrderItems WHERE salesOrderId = (SELECT salesOrderId FROM salesOrders WHERE marketplaceOrderId = 'TEST-API-001')").fetchone()
    assert item["quantity"] == 2
    assert item["salePrice"] == 1500.0
    
    conn.close()