"""
Тесты для проверки структуры (схемы) ответов OZON API.
Контрактное тестирование: если OZON меняет формат, тест падает.
"""
import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

# Схема ответа для /v4/posting/fbs/list
# Ожидаем, что на верхнем уровне будет массив postings
# и флаг has_next (для курсорной пагинации)
POSTINGS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "result": {
            "type": "object",
            "properties": {
                "postings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "posting_number": {"type": "string"},
                            "status": {"type": "string"},
                            "products": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "offer_id": {"type": "string"},
                                        "quantity": {"type": "integer"},
                                        "price": {
                                            "type": "object",
                                            "properties": {
                                                "amount": {"type": "string"},
                                                "currency": {"type": "string"}
                                            },
                                            "required": ["amount"]
                                        }
                                    },
                                    "required": ["offer_id", "quantity"]
                                }
                            }
                        },
                        "required": ["posting_number", "status", "products"]
                    }
                },
                "has_next": {"type": "boolean"},
                "cursor": {"type": "string"}
            },
            "required": ["postings", "has_next"]
        }
    },
    "required": ["result"]
}

def test_ozon_postings_schema():
    """Проверяем, что реальный ответ OZON соответствует ожидаемой схеме."""
    # Ищем последний скачанный JSON с отправлениями
    api_raw_dir = Path("data/api_raw")
    files = list(api_raw_dir.glob("*postings*.json"))
    
    if not files:
        pytest.skip("Нет скачанных JSON-файлов для проверки схемы")
        
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    
    with open(latest_file, encoding="utf-8") as f:
        data = json.load(f)
        
    # OZON возвращает список постингов на верхнем уровне, 
    # но мы в fetch_postings сохраняем сырой ответ.
    # Если это список, оборачиваем его для проверки по схеме.
    if isinstance(data, list):
        data = {"result": {"postings": data, "has_next": False}}
        
    try:
        validate(instance=data, schema=POSTINGS_RESPONSE_SCHEMA)
    except ValidationError as e:
        pytest.fail(f"Структура ответа OZON изменилась! Ошибка: {e.message}. Путь: {e.path}")