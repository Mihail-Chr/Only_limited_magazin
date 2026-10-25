import time
import requests
from .config import settings, Store


class OzonClient:
    def __init__(self, store: Store):
        if not store.has_api or not store.client_id or not store.api_key:
            raise ValueError(f"У магазина {store.code} нет API-доступа")
        self.store = store
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Client-Id": store.client_id,
                "Api-Key": store.api_key,
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
        last_exc: Exception | None = None
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
                    print("!!! Ответ Ozon:", e.response.text) # <--- ДОБАВИТЬ ЭТО
                last_exc = e
                if attempt < settings.ozon_retry_max:
                    time.sleep(settings.ozon_retry_backoff * attempt)
        raise RuntimeError(f"Ozon API failed after retries: {last_exc}")