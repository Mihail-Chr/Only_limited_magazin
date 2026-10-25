python -c "
from datetime import datetime
from src.config import get_store
from src.ozon_client import OzonClient

client = OzonClient(get_store('limited_games'))

# Проверяем 2024 год (весь год)
since = '2024-01-01T00:00:00Z'
to = '2024-12-31T23:59:59Z'
print(f'--- Проверка за 2024 год ({since} — {to}) ---')

try:
    payload = {
        'dir': 'ASC',
        'filter': {'since': since, 'to': to, 'status': ''},
        'limit': 100,
        'cursor': '',
        'with': {'analytics_data': False, 'barcodes': False, 'financial_data': False}
    }
    data = client.post('/v4/posting/fbs/list', payload)
    postings = data.get('postings', [])
    print(f'Найдено отправлений за 2024: {len(postings)}')
    if postings:
        print(f'Пример номера: {postings[0].get(\"posting_number\")}')
except Exception as e:
    print(f'Ошибка: {e}')
"