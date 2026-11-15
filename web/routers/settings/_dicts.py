"""
settings/_dicts.py — справочники для меню Настроек (v3.1).
"""


def get_settings_dicts(conn):
    return {
        "warehouses": conn.execute(
            "SELECT warehouseId AS id, name FROM warehouses WHERE isActive = 1 ORDER BY sortOrder"
        ).fetchall(),
        "platforms": conn.execute(
            "SELECT platformId, platformName, platformVersion FROM platforms ORDER BY sortOrder"
        ).fetchall(),
        "editions": conn.execute(
            "SELECT editionId, editionName, createdBy, needsReview FROM editionTypes ORDER BY sortOrder"
        ).fetchall(),
        "publishers": conn.execute(
            "SELECT publisherId, publisherName FROM publishers ORDER BY publisherName"
        ).fetchall(),
        "regions": conn.execute(
            "SELECT regionId, regionCode FROM regions ORDER BY sortOrder"
        ).fetchall(),
        "marketplaces": conn.execute(
            "SELECT marketplaceId, code, name FROM marketplaces ORDER BY sortOrder"
        ).fetchall(),
        "stores": conn.execute("""
            SELECT s.storeId, s.code, s.name, m.code AS marketplace_code
            FROM stores s
            JOIN marketplaces m ON m.marketplaceId = s.marketplaceId
            ORDER BY m.sortOrder, s.sortOrder
        """).fetchall(),
    }