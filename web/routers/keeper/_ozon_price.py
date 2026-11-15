"""
_ozon_price.py — цена OZON для формы (без роутов).

Логика:
1. Если есть listings.price (storeId=1) — берём его.
2. Иначе — последняя продажа (salesOrderItems.salePrice > 0).
3. Иначе — None.
"""


def get_ozon_price(conn, product_id: int, fallback_listing_price=None):
    if fallback_listing_price:
        return fallback_listing_price

    listing = conn.execute(
        "SELECT price FROM listings WHERE storeId = 1 AND productId = ?",
        (product_id,),
    ).fetchone()
    if listing and listing["price"]:
        return listing["price"]

    row = conn.execute("""
        SELECT salePrice FROM salesOrderItems
        WHERE productId = ? AND salePrice > 0
        ORDER BY salesOrderItemId DESC LIMIT 1
    """, (product_id,)).fetchone()
    return row["salePrice"] if row else None