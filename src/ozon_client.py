"""
HTTP-клиент для OZON API.
"""
import time
import requests
from .config import settings, Store


class OzonClient:
    def __init__(self, store: Store):
        # Проверяем, что у магазина есть ключи
        if not store.store_id or not store.store_key:
            raise ValueError(f"У магазина {store.code} нет API-доступа (ID или KEY пусты)")
        
        self.store = store
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Client-Id": store.store_id,
                "Api-Key": store.store_key,
                "Content-Type": "application/json",
            }
        )
        self._min_interval = 1.0 / max(settings.ozon_rate_limit_per_sec, 1)
        self._last_call = 0.0

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()

    def post(self, path: str, payload: dict) -> dict:
        url = f"{settings.ozon_base_url}{path}"
        last_exc = None
        
        for attempt in range(1, settings.ozon_retry_max + 1):
            self._throttle()
            try:
                resp = self.session.post(url, json=payload, timeout=settings.ozon_timeout)
                if resp.status_code == 429:
                    time.sleep(settings.ozon_retry_backoff * attempt)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    print(f"!!! Ответ Ozon: {e.response.text}")
                last_exc = e
                if attempt < settings.ozon_retry_max:
                    time.sleep(settings.ozon_retry_backoff * attempt)
        
        raise RuntimeError(f"Ozon API failed after retries: {last_exc}")