"""
Тесты для роутеров Настроек (API).
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from web.routers.settings import refs, history

app = FastAPI()
app.include_router(refs.router, prefix="/settings")
app.include_router(history.router, prefix="/settings")

client = TestClient(app)

"""
Тесты для роутеров настроек:
- refs.py (add_item, delete_item)
- history.py (get_history)
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from web.routers.settings import refs, history
from src.db import get_conn

# Создаем временное приложение для тестов
app = FastAPI()
app.include_router(refs.router, prefix="/settings")
app.include_router(history.router, prefix="/settings")

client = TestClient(app)


# =====================================================================
# ТЕСТЫ ДЛЯ refs.py
# =====================================================================

def test_add_edition_success(db_conn):
    """Добавление нового издания."""
    response = client.post("/settings/add_item", data={
        "item_type": "edition",
        "name": "Test Edition Abracadabra"
    })
    assert response.status_code == 200
    assert response.json()["ok"] is True

    # Проверяем в БД
    row = db_conn.execute("SELECT editionName FROM editionTypes WHERE editionName = 'Test Edition Abracadabra'").fetchone()
    assert row is not None


def test_add_edition_duplicate_error(db_conn):
    """Добавление существующего издания (UNIQUE constraint)."""
    # У нас в seed есть 'Standard'
    response = client.post("/settings/add_item", data={
        "item_type": "edition",
        "name": "Standard"
    })
    assert response.status_code == 400
    assert "уже существует" in response.json()["error"].lower()


def test_delete_unused_edition_success(db_conn):
    """Удаление издания, которое не используется в товарах."""
    # Сначала создадим
    cur = db_conn.execute("INSERT INTO editionTypes (editionName, createdBy) VALUES ('ToDelete', 'manual')")
    db_conn.commit() 
    edition_id = cur.lastrowid
    
    response = client.post("/settings/delete_item", data={
        "item_type": "edition",
        "item_id": edition_id
    })
    assert response.status_code == 200
    assert response.json()["ok"] is True

    # Проверяем, что удалилось
    row = db_conn.execute("SELECT editionId FROM editionTypes WHERE editionId = ?", (edition_id,)).fetchone()
    assert row is None


def test_delete_used_edition_fails(db_conn):
    """Попытка удалить издание, которое используется в товаре."""
    # Найдем ID издания 'Standard'
    edition_id = db_conn.execute("SELECT editionId FROM editionTypes WHERE editionName = 'Standard'").fetchone()[0]
    
    # Создадим товар с этим изданием
    db_conn.execute("INSERT INTO products (offerId, name, editionId) VALUES ('TEST-DEL', 'Test Product', ?)", (edition_id,))
    db_conn.commit() 
    response = client.post("/settings/delete_item", data={
        "item_type": "edition",
        "item_id": edition_id
    })
    assert response.status_code == 400
    assert "нельзя удалить" in response.json()["error"].lower()


# =====================================================================
# ТЕСТЫ ДЛЯ history.py
# =====================================================================

def test_get_history_empty(db_conn):
    """Если syncLog пуст — возвращается пустой список."""
    response = client.get("/settings/history")
    assert response.status_code == 200
    assert response.json() == {"history": []}


def test_get_history_success(db_conn):
    """Если есть записи — они возвращаются."""
    db_conn.execute("""
        INSERT INTO syncLog (syncType, dateFrom, dateTo, recordsCount, notes)
        VALUES ('ozon_sales', '2026-01-01', '2026-01-31', 100, 'All ok')
    """)
    db_conn.commit() 
    response = client.get("/settings/history")
    assert response.status_code == 200
    data = response.json()["history"]
    assert len(data) == 1
    assert data[0]["syncType"] == "ozon_sales"
    assert data[0]["recordsCount"] == 100
    assert data[0]["notes"] == "All ok"