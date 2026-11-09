"""
BaseClient — абстрактный клиент площадки.

Интерфейс для всех площадок (OZON, YM, WB, ...).
fetch_products вызывает методы через этот интерфейс — не знает, какая площадка.
"""
from abc import ABC, abstractmethod


class BaseClient(ABC):
    """Абстрактный клиент площадки."""

    def __init__(self, client_id: str, api_key: str):
        self.client_id = client_id
        self.api_key = api_key

    @abstractmethod
    def get_products(self) -> list[dict]:
        """
        Загружает список товаров с площадки.

        Returns:
            list[dict]: [{"offer_id": str, "product_id": int, "sku": int}, ...]
        """
        ...

    @abstractmethod
    def get_product_info(self, offer_ids: list[str]) -> list[dict]:
        """
        Загружает детали товаров (названия).

        Args:
            offer_ids: список артикулов.

        Returns:
            list[dict]: [{"offer_id": str, "name": str}, ...]
        """
        ...