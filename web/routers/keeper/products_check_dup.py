"""
products_check_dup.py — GET /keeper/check_duplicate.

AJAX-проверка дублей по 8 полям (для предупреждения перед сохранением).

Query: baseGameName, platformId, editionId, regionId, mediaTypeId,
       publisherId, typeGoodId, restore, exclude_product_id (опц.)
Ответ: {"exists": bool, "product": {...}}
"""
from fastapi import APIRouter

from src.db import get_conn
from ._duplicates import find_duplicate

router = APIRouter()


@router.get("/check_duplicate")
def check_duplicate(
    baseGameName: str = "",
    platformId: int | None = None,
    editionId: int | None = None,
    regionId: int | None = None,
    mediaTypeId: int | None = None,
    publisherId: int | None = None,
    typeGoodId: int | None = None,
    restore: int = 0,
    exclude_product_id: int | None = None,
):
    data = {
        "baseGameName": baseGameName,
        "platformId": platformId,
        "editionId": editionId,
        "regionId": regionId,
        "mediaTypeId": mediaTypeId,
        "publisherId": publisherId,
        "typeGoodId": typeGoodId,
        "restore": restore,
    }
    with get_conn() as conn:
        dup = find_duplicate(conn, data, exclude_product_id=exclude_product_id)

    if dup:
        return {
            "exists": True,
            "product": {
                "productId": dup["productId"],
                "offerId": dup["offerId"],
                "baseGameName": dup["baseGameName"],
            },
        }
    return {"exists": False}