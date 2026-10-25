"""
Экспорт остатков в CSV (для открытия в Excel).
Запуск: python -m src.scripts.export_stock_csv
"""
import csv
from datetime import datetime
from src.config import settings
from src.db import get_conn


def main() -> None:
    settings.data_exports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = settings.data_exports / f"stock_report_{stamp}.csv"

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT 
                p.offer_id,
                p.name,
                COALESCE(sm.quantity, 0) AS physical_qty,
                COALESCE(SUM(pi.quantity), 0) AS in_transit_qty,
                COALESCE(sm.quantity, 0) - COALESCE(SUM(pi.quantity), 0) AS available_qty
            FROM product p
            LEFT JOIN stock_manual sm ON sm.product_id = p.id
            LEFT JOIN posting_item pi ON pi.product_id = p.id
            LEFT JOIN posting post ON post.id = pi.posting_id
                AND post.status NOT IN ('delivered', 'cancelled')
            GROUP BY p.id
            ORDER BY available_qty ASC
            """
        ).fetchall()

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Артикул", "Название", "Физ. остаток", "В пути", "Доступно"])
        for r in rows:
            writer.writerow([
                r["offer_id"],
                r["name"],
                r["physical_qty"],
                r["in_transit_qty"],
                r["available_qty"],
            ])

    print(f"Отчёт сохранён: {path}")


if __name__ == "__main__":
    main()