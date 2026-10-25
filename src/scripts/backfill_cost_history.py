"""
Заполнение cost_price_at_sale в posting_item: себестоимость на момент продажи.
Запуск: python -m src.scripts.backfill_cost_history --discount 0.7
"""
import argparse
from src.db import get_conn

DEFAULT_DISCOUNT = 0.7


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discount", type=float, default=DEFAULT_DISCOUNT, help="Доля скидки, например 0.7")
    args = ap.parse_args()

    discount = args.discount

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, price FROM posting_item WHERE cost_price_at_sale IS NULL"
        ).fetchall()

        updated = 0
        for r in rows:
            price = float(r["price"] or 0)
            if price <= 0:
                continue
            cost = round(price * (1 - discount), 2)
            conn.execute(
                "UPDATE posting_item SET cost_price_at_sale = ? WHERE id = ?",
                (cost, r["id"]),
            )
            updated += 1

        conn.commit()

    print(f"Обновлено записей: {updated}")
    print(f"Дисконт: {discount}")


if __name__ == "__main__":
    main()