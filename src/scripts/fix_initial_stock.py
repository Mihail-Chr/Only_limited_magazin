"""
Корректировка начального остатка: добавляем к stock_manual количество проданного,
чтобы избежать отрицательных значений в отчётах.
Запуск: python -m src.scripts.fix_initial_stock
"""
from src.db import get_conn


def main() -> None:
    with get_conn() as conn:
        # 1. Считаем, сколько всего продано по каждому товару (за все годы)
        sold_rows = conn.execute(
            """
            SELECT pi.product_id, SUM(pi.quantity) AS total_sold
            FROM posting_item pi
            GROUP BY pi.product_id
            """
        ).fetchall()

        sold_map = {r["product_id"]: r["total_sold"] for r in sold_rows if r["product_id"]}

        # 2. Получаем текущий физический остаток
        stock_rows = conn.execute(
            "SELECT product_id, quantity FROM stock_manual"
        ).fetchall()
        stock_map = {r["product_id"]: r["quantity"] for r in stock_rows}

        updated = 0
        added_total = 0

        for product_id, total_sold in sold_map.items():
            current_stock = stock_map.get(product_id, 0)
            
            # Если текущий остаток меньше проданного, компенсируем разницу
            if current_stock < total_sold:
                new_stock = total_sold  # ставим искусственный остаток = всё проданное
                conn.execute(
                    """INSERT INTO stock_manual (product_id, quantity)
                       VALUES (?, ?)
                       ON CONFLICT(product_id) DO UPDATE SET
                           quantity = excluded.quantity,
                           updated_at = datetime('now')""",
                    (product_id, new_stock),
                )
                added_total += (new_stock - current_stock)
                updated += 1

        conn.commit()

    print(f"Обновлено товаров: {updated}")
    print(f"Добавлено единиц к остаткам (компенсация): {added_total}")
    print("Теперь в отчётах не должно быть отрицательных значений.")


if __name__ == "__main__":
    main()