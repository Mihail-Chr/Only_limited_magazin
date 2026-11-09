"""
OzonClient — клиент OZON (наследует BaseClient).

Реализует get_products, get_product_info, get_postings через OZON API.
"""
import requests
from datetime import datetime, timedelta
from src.clients.base import BaseClient


class OzonClient(BaseClient):
    """Клиент OZON."""

    BASE_URL = "https://api-seller.ozon.ru"

    def __init__(self, client_id: str, api_key: str):
        super().__init__(client_id, api_key)
        self.session = requests.Session()
        self.session.headers.update({
            "Client-Id": client_id,
            "Api-Key": api_key,
            "Content-Type": "application/json",
        })

    def _post(self, path: str, payload: dict) -> dict:
        """POST-запрос к OZON API. Возвращает JSON (или raise)."""
        url = f"{self.BASE_URL}{path}"
        response = self.session.post(url, json=payload, timeout=30)
        if response.status_code == 401:
            raise ValueError("Невалидный API-ключ (401)")
        if response.status_code == 400:
            raise ValueError(f"Ошибка 400 Bad Request: {response.text}")
        if response.status_code >= 500:
            raise ValueError(f"Ошибка сервера OZON ({response.status_code})")
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            raise ValueError(f"Невалидный JSON в ответе: {response.text[:200]}")

    def get_products(self) -> list[dict]:
        """Загружает список товаров (все страницы)."""
        items = []
        last_id = ""
        total = None
        while True:
            payload = {
                "filter": {"visibility": "ALL"},
                "last_id": last_id,
                "limit": 1000,
            }
            data = self._post("/v3/product/list", payload)
            result = data.get("result", {})
            batch = result.get("items", [])
            items.extend(batch)
            if total is None:
                total = result.get("total", 0)
            last_id = result.get("last_id", "")
            if not batch or not last_id:
                break
        if total is not None and total > len(items):
            raise ValueError(
                f"Неполный ответ: total={total}, получено={len(items)}"
            )
        return items

    def get_product_info(self, offer_ids: list[str]) -> list[dict]:
        """Загружает названия товаров (батчами по 1000)."""
        details = []
        for i in range(0, len(offer_ids), 1000):
            batch = offer_ids[i:i + 1000]
            payload = {"offer_id": batch, "product_id": [], "sku": []}
            data = self._post("/v3/product/info/list", payload)
            details.extend(data.get("items", []))
        return details

    def _get_postings_chunk(self, date_from: str, date_to: str) -> list[dict]:
        """Загружает отправления за ОДИН кусок периода (не больше года)."""
        since = f"{date_from}T00:00:00Z"
        to = f"{date_to}T23:59:59Z"

        all_postings = []
        cursor = ""
        has_next = True
        limit = 100  # OZON v4 требует не больше 100

        while has_next:
            payload = {
                "dir": "ASC",
                "filter": {
                    "since": since,
                    "to": to,
                    "statuses": []  # все статусы
                },
                "limit": limit,
                "cursor": cursor,
                "with": {
                    "analytics_data": False,
                    "barcodes": False,
                    "financial_data": False,
                },
            }
            data = self._post("/v4/posting/fbs/list", payload)
            
            batch = data.get("postings", [])
            all_postings.extend(batch)

            has_next = data.get("has_next", False)
            cursor = data.get("cursor", "")

            if not batch:
                break

        return all_postings

    def get_postings(self, date_from: str, date_to: str) -> list[dict]:
        """
        Загружает отправления (все страницы) за период.
        Режет период на куски по 360 дней (требование OZON).
        """
        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        
        all_postings = []
        
        current_start = start
        while current_start <= end:
            # Берем 360 дней (чуть меньше года, чтобы точно влезть)
            current_end = current_start + timedelta(days=360)
            if current_end > end:
                current_end = end
            
            chunk_from = current_start.strftime("%Y-%m-%d")
            chunk_to = current_end.strftime("%Y-%m-%d")
            
            print(f"  → Запрос порции: {chunk_from} — {chunk_to}")
            chunk_postings = self._get_postings_chunk(chunk_from, chunk_to)
            all_postings.extend(chunk_postings)
            
            current_start = current_end + timedelta(days=1)

        return all_postings