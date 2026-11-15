"""
_duplicates.py — поиск дублей (8 полей, без роутов).

Ключ: baseGameName + platformId + editionId + regionId + mediaTypeId
      + publisherId + typeGoodId + restore (NULL ≠ значение, через -1).
"""
from .._shared.common import to_int_or_none


def _norm(value):
    if value is None or value == "":
        return -1
    return value


def _key(baseGameName, platformId, editionId, regionId, mediaTypeId,
         publisherId, typeGoodId, restore):
    return (
        (baseGameName or "").strip().lower(),
        _norm(platformId),
        _norm(editionId),
        _norm(regionId),
        _norm(mediaTypeId),
        _norm(publisherId),
        _norm(typeGoodId),
        int(restore or 0),
    )


def find_duplicate(conn, data: dict, exclude_product_id=None):
    """
    Ищет дубль среди isActive=1.
    Возвращает row (productId, offerId, baseGameName) или None.
    """
    key = _key(
        data.get("baseGameName"),
        to_int_or_none(data.get("platformId")),
        to_int_or_none(data.get("editionId")),
        to_int_or_none(data.get("regionId")),
        to_int_or_none(data.get("mediaTypeId")),
        to_int_or_none(data.get("publisherId")),
        to_int_or_none(data.get("typeGoodId")),
        to_int_or_none(data.get("restore")) or 0,
    )

    rows = conn.execute("""
        SELECT productId, offerId, baseGameName,
               platformId, editionId, regionId, mediaTypeId,
               publisherId, typeGoodId, restore
        FROM products
        WHERE isActive = 1
    """).fetchall()

    for r in rows:
        if exclude_product_id is not None and r["productId"] == exclude_product_id:
            continue
        rkey = _key(
            r["baseGameName"], r["platformId"], r["editionId"],
            r["regionId"], r["mediaTypeId"], r["publisherId"],
            r["typeGoodId"], r["restore"],
        )
        if rkey == key:
            return r
    return None