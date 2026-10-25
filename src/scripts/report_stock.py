"""
Отчёт по остаткам: физический остаток, в пути, доступно к продаже.
Запуск: python -m src.scripts.report_stock
"""
from src.db import get_conn


def main() -> None:
    with get_conn() as conn:
        # Собираем данные: товар, физический остаток, сколько в пути
        rows = conn.execute(
            """
            SELECT 
                p.offer_id,
                p.name,
                COALESCE(sm.quantity, 0) AS physical_qty,
                COALESCE(SUM(pi.quantity), 0) AS in_transit_qty
            FROM product p
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            LEFT JOIN posting_item pi ON pi.product_id = p.id
            LEFT JOIN posting post ON post.id = pi.posting_id
                AND post.status NOT IN ('delivered', 'cancelled')
            GROUP BY p.id
            ORDER BY in_transit_qty DESC, p.offer_id
            """
        ).fetchall()

    print(f"{'Артикул':<10} | {'Физ. остаток':<12} | {'В пути':<8} | {'Доступно':<8} | {'Название':<40}")
    print("-" * 90)
    
    total_physical = 0
    total_transit = 0
    total_available = 0

    for r in rows:
        physical = r["physical_qty"]
        transit = r["in_transit_qty"]
        available = physical - transit
        name = (r["name"] or "")[:37] + "..." if len(r["name"] or "") > 40 else (r["name"] or "")

        # Показываем только те товары, где есть физический остаток или товар в пути
        if physical > 0 or transit > 0:
            print(f"{r['offer_id']:<10} | {physical:<12} | {transit:<8} | {available:<8} | {name:<40}")
        
        total_physical += physical
        total_transit += transit
        total_available += available

    print("-" * 90)
    print(f"ИТОГО: Физ. остаток: {total_physical}, В пути: {total_transit}, Доступно: {total_available}")


if __name__ == "__main__":
    main()