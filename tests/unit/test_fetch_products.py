"""
Тесты для src/scripts/fetch_products.py (v3.1).

Запуск: pytest tests/unit/test_fetch_products.py -v

TDD: тесты описывают ЖЕЛАЕМОЕ поведение.

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


def make_mock_client(products=None, info=None, error=None):
    """Создаёт мок-клиент (OzonClient)."""
    client = MagicMock()
    if error:
        client.get_products.side_effect = error
    else:
        client.get_products.return_value = products or []
    client.get_product_info.return_value = info or []
    return client


# =====================================================================
# ПОЗИТИВНЫЕ (5)
# =====================================================================

def test_fetch_products_creates_products(monkeypatch, tmp_path):
    """fetch_products создаёт products из мок-ответа."""
    from src.scripts.fetch_products import fetch_products
    from src.db import get_conn

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    products = [
        {"offer_id": "TEST-001", "product_id": 123, "sku": 456},
        {"offer_id": "TEST-002", "product_id": 124, "sku": 457},
    ]
    info = [
        {"offer_id": "TEST-001", "name": "God of War (PS4)"},
        {"offer_id": "TEST-002", "name": "God of War II (PS4)"},
    ]
    client = make_mock_client(products=products, info=info)

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is True
    assert result["inserted"] == 2

    conn = get_test_conn()
    rows = conn.execute("SELECT offerId, name FROM products ORDER BY offerId").fetchall()
    conn.close()
    assert len(rows) == 2
    assert rows[0]["offerId"] == "TEST-001"
    assert rows[0]["name"] == "God of War (PS4)"


def test_fetch_products_creates_listings(monkeypatch, tmp_path):
    """fetch_products создаёт listings (привязка к stores)."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    products = [{"offer_id": "TEST-001", "product_id": 123, "sku": 456}]
    info = [{"offer_id": "TEST-001", "name": "God of War (PS4)"}]
    client = make_mock_client(products=products, info=info)

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is True
    assert result["listings"] == 1

    conn = get_test_conn()
    rows = conn.execute("SELECT * FROM listings").fetchall()
    conn.close()
    assert len(rows) == 1


def test_fetch_products_updates_names(monkeypatch, tmp_path):
    """fetch_products обновляет name из info/list."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    products = [{"offer_id": "TEST-001", "product_id": 123, "sku": 456}]
    info = [{"offer_id": "TEST-001", "name": "God of War (PS4)"}]
    client = make_mock_client(products=products, info=info)

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is True
    assert result["updated"] == 1

    conn = get_test_conn()
    row = conn.execute("SELECT name FROM products WHERE offerId = 'TEST-001'").fetchone()
    conn.close()
    assert row["name"] == "God of War (PS4)"


def test_fetch_products_saves_raw_json(monkeypatch, tmp_path):
    """fetch_products сохраняет сырой JSON в data/api_raw/."""
    from src.scripts.fetch_products import fetch_products
    import src.scripts.fetch_products as fp

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    products = [{"offer_id": "TEST-001", "product_id": 123, "sku": 456}]
    info = [{"offer_id": "TEST-001", "name": "God of War (PS4)"}]
    client = make_mock_client(products=products, info=info)

    original_api_raw = fp.DATA_API_RAW
    fp.DATA_API_RAW = tmp_path / "api_raw"

    try:
        result = fetch_products("ozon", "limited_games", client=client)
        assert result["ok"] is True

        files = list((tmp_path / "api_raw").glob("*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert len(data) == 1
    finally:
        fp.DATA_API_RAW = original_api_raw


def test_fetch_products_returns_counts(monkeypatch, tmp_path):
    """fetch_products возвращает inserted, updated, listings."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    products = [
        {"offer_id": "TEST-001", "product_id": 123, "sku": 456},
        {"offer_id": "TEST-002", "product_id": 124, "sku": 457},
    ]
    info = [
        {"offer_id": "TEST-001", "name": "God of War (PS4)"},
        {"offer_id": "TEST-002", "name": "God of War II (PS4)"},
    ]
    client = make_mock_client(products=products, info=info)

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is True
    assert result["inserted"] == 2
    assert result["updated"] == 2
    assert result["listings"] == 2


# =====================================================================
# НЕГАТИВНЫЕ (10)
# =====================================================================

def test_fetch_products_handles_unknown_store(monkeypatch):
    """Магазин не найден → ok=False."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)

    client = make_mock_client()
    result = fetch_products("ozon", "unknown_store", client=client)

    assert result["ok"] is False
    assert "не найден" in result["error"].lower()


def test_fetch_products_handles_no_api(monkeypatch):
    """hasApi=0 → ok=False."""
    from src.scripts.fetch_products import fetch_products
    from src.db import get_conn

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)

    # Устанавливаем hasApi=0 для manual
    with get_conn() as conn:
        conn.execute("UPDATE stores SET hasApi = 0 WHERE code = 'manual'")

    client = make_mock_client()
    result = fetch_products("ozon", "manual", client=client)

    assert result["ok"] is False
    assert "api" in result["error"].lower()


def test_fetch_products_handles_missing_env(monkeypatch):
    """Нет ключей в .env → ok=False."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.delenv("OZON_LIMITED_GAMES_CLIENT_ID", raising=False)
    monkeypatch.delenv("OZON_LIMITED_GAMES_API_KEY", raising=False)

    result = fetch_products("ozon", "limited_games", client=None)

    assert result["ok"] is False
    assert "env" in result["error"].lower() or "ключ" in result["error"].lower()


def test_fetch_products_handles_garbage_env(monkeypatch):
    """«Мусор» в .env (401) → ok=False."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "№№##")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "абракадабра")

    client = MagicMock()
    client.get_products.side_effect = ValueError("Невалидный API-ключ (401)")

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is False
    assert "401" in result["error"] or "ключ" in result["error"].lower()


def test_fetch_products_handles_api_error(monkeypatch):
    """Ошибка API (500) → ok=False."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    client = MagicMock()
    client.get_products.side_effect = ValueError("Ошибка сервера OZON (500)")

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is False
    assert "500" in result["error"]


def test_fetch_products_handles_empty_response(monkeypatch):
    """Пустой ответ ([]) → ok=True, inserted=0."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    client = make_mock_client(products=[], info=[])

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is True
    assert result["inserted"] == 0


def test_fetch_products_handles_garbage_offer_id(monkeypatch):
    """Пустой offerId → пропуск, валидный (странный) создан."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    products = [
        {"offer_id": "", "product_id": 123, "sku": 456},           # пустой — пропуск
        {"offer_id": None, "product_id": 124, "sku": 457},         # None — пропуск
        {"offer_id": "   ", "product_id": 125, "sku": 458},        # пробелы — пропуск
        {"offer_id": "№№## 111FааРРП", "product_id": 126, "sku": 459},  # странный — ВАЛИДНЫЙ
        {"offer_id": "TEST-001", "product_id": 127, "sku": 460},   # валидный
    ]
    info = [
        {"offer_id": "№№## 111FааРРП", "name": "Garbage Game"},
        {"offer_id": "TEST-001", "name": "God of War (PS4)"},
    ]
    client = make_mock_client(products=products, info=info)

    result = fetch_products("ozon", "limited_games", client=client)

    # Пустые пропущены, странный + валидный созданы
    assert result["inserted"] == 2
    assert len(result["errors"]) == 3  # пустой, None, пробелы


def test_fetch_products_handles_invalid_json(monkeypatch):
    """«Сломанный» JSON → ok=False."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    client = MagicMock()
    client.get_products.side_effect = ValueError("Невалидный JSON в ответе")

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is False
    assert "json" in result["error"].lower()


def test_fetch_products_handles_hasapi_mismatch(monkeypatch):
    """hasApi=1, но .env пуст → ok=False."""
    from src.scripts.fetch_products import fetch_products

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.delenv("OZON_LIMITED_GAMES_CLIENT_ID", raising=False)
    monkeypatch.delenv("OZON_LIMITED_GAMES_API_KEY", raising=False)

    result = fetch_products("ozon", "limited_games", client=None)

    assert result["ok"] is False
    assert "env" in result["error"].lower() or "ключ" in result["error"].lower()


def test_fetch_products_handles_hasapi_zero_but_env_present(monkeypatch):
    """hasApi=0, но .env есть → ok=True, errors (предупреждение)."""
    from src.scripts.fetch_products import fetch_products
    from src.db import get_conn

    monkeypatch.setenv("TEST_DB_PATH", TEST_DB_PATH)
    monkeypatch.setenv("OZON_LIMITED_GAMES_CLIENT_ID", "test_id")
    monkeypatch.setenv("OZON_LIMITED_GAMES_API_KEY", "test_key")

    with get_conn() as conn:
        conn.execute("UPDATE stores SET hasApi = 0 WHERE code = 'limited_games'")

    products = [{"offer_id": "TEST-001", "product_id": 123, "sku": 456}]
    info = [{"offer_id": "TEST-001", "name": "God of War (PS4)"}]
    client = make_mock_client(products=products, info=info)

    result = fetch_products("ozon", "limited_games", client=client)

    assert result["ok"] is True
    assert any("hasApi" in e for e in result["errors"])