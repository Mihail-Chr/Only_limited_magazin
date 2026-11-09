"""
Тесты для FastAPI-приложения (роутеры).
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Временное приложение (пока нет web/app.py v3.1)
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    """Проверка, что сервер отвечает на /health."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}