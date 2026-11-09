"""
Тесты для src/scripts/fetch_postings.py (v3.1).

Запуск: pytest tests/unit/test_fetch_postings.py -v

TDD: тесты описывают ЖЕЛАЕМОЕ поведение.
На старом коде (v2) — тесты ПАДАЮТ. Это нормально.

Моки: OzonClient (не реальный API).
"""
import sqlite3
import os
import json
from unittest.mock import MagicMock
import pytest


TEST_DB_PATH = "db/test_only_limited.sqlite3"


def get_test_conn():
    """Соединение с тестовой БД."""
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def make_mock_client(postings=None, error=None):
    """Создаёт мок-клиент (OzonClient)."""
    client = MagicMock()
    if error:
        client.get_postings.side_effect = error
    else:
        client.get_postings.return_value = postings or []
    return client


@pytest.fixture(autouse=True)
def cleanup_api_raw():
    """Удаляет JSON из data/api_raw после каждого теста."""
    from pathlib import Path
    api_raw = Path("data/api_raw")

    yield

    if api_raw.exists():
        for f in api_raw.glob("*_postings_*.json"):
            try:
                f.unlink()
            except Exception:
                pass


# =====================================================================
# ПОЗИТИВНЫЕ (10)
# =====================================================================

def test_fetch_postings_creates_sales_orders(monkeypatch, tmp_path):
    """fetch_postings создаёт salesOrders."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [{"offer_id": "TEST-001", "quantity": 1, "price": "5000"}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is True
    assert result["inserted"] == 1

    conn = get_test_conn()
    rows = conn.execute("SELECT marketplaceOrderId FROM salesOrders").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0]["marketplaceOrderId"] == "TEST-001"


def test_fetch_postings_creates_items(monkeypatch, tmp_path):
    """fetch_postings создаёт salesOrderItems."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [
            {"offer_id": "TEST-001", "quantity": 2, "price": "5000"},
            {"offer_id": "TEST-002", "quantity": 1, "price": "3000"},
        ],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is True

    conn = get_test_conn()
    items = conn.execute("SELECT quantity, salePrice FROM salesOrderItems").fetchall()
    conn.close()
    assert len(items) == 2


def test_fetch_postings_creates_status_history(monkeypatch, tmp_path):
    """fetch_postings создаёт salesOrderStatusHistory (статус из API)."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [{"offer_id": "TEST-001", "quantity": 1, "price": "5000"}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is True

    conn = get_test_conn()
    history = conn.execute("SELECT * FROM salesOrderStatusHistory").fetchall()
    status_row = conn.execute(
        "SELECT statusId FROM statuses WHERE statusName = 'delivered' AND statusType = 'sale'"
    ).fetchone()
    conn.close()
    assert len(history) == 1
    assert status_row is not None


def test_fetch_postings_saves_raw_json(monkeypatch, tmp_path):
    """fetch_postings сохраняет сырой JSON."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{"posting_number": "TEST-001", "status": "delivered",
                 "created_at": "2026-11-01T10:00:00Z",
                 "products": [{"offer_id": "TEST-001", "quantity": 1, "price": "5000"}]}]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is True
    files = list((tmp_path / "api_raw").glob("*.json"))
    assert len(files) == 1


def test_fetch_postings_returns_counts(monkeypatch, tmp_path):
    """fetch_postings возвращает inserted."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [
        {"posting_number": "TEST-001", "status": "delivered",
         "created_at": "2026-11-01T10:00:00Z",
         "products": [{"offer_id": "TEST-001", "quantity": 1, "price": "5000"}]},
        {"posting_number": "TEST-002", "status": "delivering",
         "created_at": "2026-11-02T10:00:00Z",
         "products": [{"offer_id": "TEST-002", "quantity": 1, "price": "3000"}]},
    ]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is True
    assert result["inserted"] == 2


def test_fetch_postings_multiple_orders(monkeypatch, tmp_path):
    """fetch_postings создаёт несколько заказов."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [
        {"posting_number": "TEST-001", "status": "delivered",
         "created_at": "2026-11-01T10:00:00Z",
         "products": [{"offer_id": "TEST-001", "quantity": 1, "price": "5000"}]},
        {"posting_number": "TEST-002", "status": "delivering",
         "created_at": "2026-11-02T10:00:00Z",
         "products": [{"offer_id": "TEST-002", "quantity": 1, "price": "3000"}]},
    ]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    conn = get_test_conn()
    orders = conn.execute("SELECT COUNT(*) FROM salesOrders").fetchone()[0]
    conn.close()
    assert orders == 2


def test_fetch_postings_buyer_from_api(monkeypatch, tmp_path):
    """fetch_postings использует buyer_nickname из API."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "buyer_nickname": "PlayerOne",
        "products": [{"offer_id": "TEST-001", "quantity": 1, "price": "5000"}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    conn = get_test_conn()
    buyers = conn.execute("SELECT buyerNickname FROM buyers").fetchall()
    conn.close()
    names = [b["buyerNickname"] for b in buyers]
    assert "PlayerOne" in names


def test_fetch_postings_fallback_buyer(monkeypatch, tmp_path):
    """fetch_postings: fallback buyerId=1 (если нет в API)."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [{"offer_id": "TEST-001", "quantity": 1, "price": "5000"}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    conn = get_test_conn()
    order = conn.execute("SELECT buyerId FROM salesOrders").fetchone()
    conn.close()
    assert order["buyerId"] == 1


def test_fetch_postings_product_if_missing(monkeypatch, tmp_path):
    """fetch_postings создаёт product (заглушку), если нет."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [{"offer_id": "NEW-001", "quantity": 1, "price": "5000"}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    conn = get_test_conn()
    prod = conn.execute("SELECT offerId FROM products WHERE offerId = 'NEW-001'").fetchone()
    conn.close()
    assert prod is not None


def test_fetch_postings_multiple_products(monkeypatch, tmp_path):
    """fetch_postings создаёт несколько товаров в заказе."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [
            {"offer_id": "TEST-001", "quantity": 2, "price": "5000"},
            {"offer_id": "TEST-002", "quantity": 1, "price": "3000"},
        ],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    conn = get_test_conn()
    items = conn.execute("SELECT quantity, salePrice FROM salesOrderItems").fetchall()
    conn.close()
    assert len(items) == 2


# =====================================================================
# НЕГАТИВНЫЕ (13)
# =====================================================================

def test_fetch_postings_handles_unknown_store(monkeypatch):
    """Магазин не найден → ok=False."""
    from src.scripts.fetch_postings import fetch_postings

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)

    client = make_mock_client()
    result = fetch_postings("ozon", "unknown_store", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is False
    assert "не найден" in result["error"].lower()


def test_fetch_postings_handles_unknown_platform(monkeypatch):
    """Площадка не найдена → ok=False."""
    from src.scripts.fetch_postings import fetch_postings

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("UNKNOWN_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("UNKNOWN_LIMITED_GAMES_API_KEY", "test_key")

    client = make_mock_client()
    result = fetch_postings("unknown", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is False
    assert "площадк" in result["error"].lower() or "unknown" in result["error"].lower()


def test_fetch_postings_handles_no_api(monkeypatch):
    """hasApi=0 → ok=False."""
    from src.scripts.fetch_postings import fetch_postings
    from src.db import get_conn

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)

    with get_conn() as conn:
        conn.execute("UPDATE stores SET hasApi = 0 WHERE code = 'manual'")

    client = make_mock_client()
    result = fetch_postings("ozon", "manual", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is False
    assert "api" in result["error"].lower()


def test_fetch_postings_handles_missing_env(monkeypatch):
    """Нет ключей в .env → ok=False."""
    from src.scripts.fetch_postings import fetch_postings

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.delenv("OZON_LIMITED_GAMES_CLIENT_ID", raising=False)
    monkeypatch.delenv("OZON_LIMITED_GAMES_API_KEY", raising=False)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=None)

    assert result["ok"] is False
    assert "env" in result["error"].lower() or "ключ" in result["error"].lower()


def test_fetch_postings_handles_garbage_env(monkeypatch):
    """«Мусор» в .env (401) → ok=False."""
    from src.scripts.fetch_postings import fetch_postings

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "№№##")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "абракадабра")

    client = MagicMock()
    client.get_postings.side_effect = ValueError("Невалидный API-ключ (401)")

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is False
    assert "401" in result["error"] or "ключ" in result["error"].lower()


def test_fetch_postings_handles_api_error(monkeypatch):
    """Ошибка API (500) → ok=False."""
    from src.scripts.fetch_postings import fetch_postings

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    client = MagicMock()
    client.get_postings.side_effect = ValueError("Ошибка сервера OZON (500)")

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is False
    assert "500" in result["error"]


def test_fetch_postings_handles_empty_response(monkeypatch, tmp_path):
    """Пустой ответ ([]) → ok=True, inserted=0."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    client = make_mock_client(postings=[])

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is True
    assert result["inserted"] == 0


def test_fetch_postings_handles_none_response(monkeypatch, tmp_path):
    """None в ответе → пропуск."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [None]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is True
    assert len(result["errors"]) > 0


def test_fetch_postings_handles_invalid_json(monkeypatch):
    """«Сломанный» JSON → ok=False."""
    from src.scripts.fetch_postings import fetch_postings

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    client = MagicMock()
    client.get_postings.side_effect = ValueError("Невалидный JSON в ответе")

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is False
    assert "json" in result["error"].lower()


def test_fetch_postings_negative_quantity(monkeypatch, tmp_path):
    """Отрицательное quantity → abs, ошибка в errors."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [{"offer_id": "TEST-001", "quantity": -3, "price": "5000"}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    conn = get_test_conn()
    item = conn.execute("SELECT quantity FROM salesOrderItems").fetchone()
    conn.close()
    assert item["quantity"] == 3
    assert len(result["errors"]) > 0


def test_fetch_postings_empty_quantity(monkeypatch, tmp_path):
    """Пустое quantity → 0, ошибка, salesOrderItems НЕ создаётся."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [{"offer_id": "TEST-001", "quantity": "", "price": "5000"}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    assert result["ok"] is True
    assert len(result["errors"]) > 0
    conn = get_test_conn()
    items = conn.execute("SELECT * FROM salesOrderItems").fetchall()
    conn.close()
    assert len(items) == 0


def test_fetch_postings_negative_price(monkeypatch, tmp_path):
    """Отрицательное price → abs, ошибка."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [{"offer_id": "TEST-001", "quantity": 1, "price": -100}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    conn = get_test_conn()
    item = conn.execute("SELECT salePrice FROM salesOrderItems").fetchone()
    conn.close()
    assert item["salePrice"] == 100.0
    assert len(result["errors"]) > 0


def test_fetch_postings_empty_price(monkeypatch, tmp_path):
    """Пустое price → 0, ошибка."""
    from src.scripts.fetch_postings import fetch_postings
    import src.scripts.fetch_postings as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    fp.DATA_API_RAW = tmp_path / "api_raw"

    postings = [{
        "posting_number": "TEST-001",
        "status": "delivered",
        "created_at": "2026-11-01T10:00:00Z",
        "products": [{"offer_id": "TEST-001", "quantity": 1, "price": ""}],
    }]
    client = make_mock_client(postings=postings)

    result = fetch_postings("ozon", "limited_games", "2026-11-01", "2026-11-08", client=client)

    conn = get_test_conn()
    item = conn.execute("SELECT salePrice FROM salesOrderItems").fetchone()
    conn.close()
    assert item["salePrice"] == 0.0
    assert len(result["errors"]) > 0