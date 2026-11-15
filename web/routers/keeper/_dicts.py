"""
_dicts.py — справочники для форм (без роутов).
"""
from src.db import get_conn


def get_dictionaries(conn):
    """Все справочники, нужные формам Кладовщика (v3.1)."""
    return {
        "typeGoods": conn.execute(
            "SELECT typeGoodId, typeGoodName FROM typeGoods ORDER BY sortOrder"
        ).fetchall(),
        "platforms": conn.execute(
            "SELECT platformId, platformName, platformVersion FROM platforms ORDER BY sortOrder"
        ).fetchall(),
        "editions": conn.execute(
            "SELECT editionId, editionName FROM editionTypes ORDER BY sortOrder"
        ).fetchall(),
        "regions": conn.execute(
            "SELECT regionId, regionCode FROM regions ORDER BY sortOrder"
        ).fetchall(),
        "publishers": conn.execute(
            "SELECT publisherId, publisherName FROM publishers ORDER BY publisherName"
        ).fetchall(),
        "mediaTypes": conn.execute(
            "SELECT mediaTypeId, mediaTypeName FROM mediaTypes ORDER BY sortOrder"
        ).fetchall(),
        "warehouses": conn.execute(
            "SELECT warehouseId AS id, name FROM warehouses WHERE isActive = 1"
        ).fetchall(),
        "games": conn.execute(
            "SELECT DISTINCT baseGameName FROM products WHERE baseGameName IS NOT NULL"
        ).fetchall(),
    }


def get_warehouses(conn):
    return conn.execute(
        "SELECT warehouseId AS id, name FROM warehouses WHERE isActive = 1"
    ).fetchall()