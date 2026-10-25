"""
Расчёт и установка «искусственной» входной цены (себестоимости).
Берёт текущую цену в Ozon и отнимает фиксированный дисконт (по умолчанию 35%).
Запуск: python -m src.scripts.set_synthetic_cost
"""
import argparse
from src.db import get_conn

DISCOUNT = 0.70  # 70%


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discount", type=float, default=DISCOUNT, help="Доля дисконта, например 0.70")
    args = ap.parse_args()

    discount = args.discount

    with get_conn() as conn:
        # Берём товары, у которых есть цена в листинге
        rows = conn.execute(
            """
            SELECT p.id, p.offer_id, l.price
            FROM product p
            JOIN listing l ON l.product_id = p.id
            WHERE l.price IS NOT NULL AND l.price > 0             
            """
        ).fetchall()

        updated = 0
        for r in rows:
            synthetic_cost = round(r["price"] * (1 - discount), 2)
            conn.execute(
                """UPDATE product
                   SET cost_price_synthetic = ?,
                       cost_price_real = ?
                   WHERE id = ?""",
                (synthetic_cost, synthetic_cost, r["id"]),
            )
            updated += 1
        conn.commit()

    print(f"Обновлено товаров: {updated}")
    print(f"Дисконт от цены Ozon: {discount * 100:.1f}%")
    print("Пример: цена 1000 -> искусственная себестоимость 300")


if __name__ == "__main__":
    main()