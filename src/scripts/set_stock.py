"""
Установка физического остатка для товара.
Запуск: python -m src.scripts.set_stock --offer_id 1277 --qty 10
"""
import argparse
from src.db import get_conn


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offer_id", required=True, help="Артикул товара")
    ap.add_argument("--qty", type=int, required=True, help="Количество на складе")
    args = ap.parse_args()

    with get_conn() as conn:
        prod = conn.execute(
            "SELECT id, name FROM product WHERE offer_id = ?", (args.offer_id,)
        ).fetchone()
        if not prod:
            raise SystemExit(f"Товар с артикулом {args.offer_id} не найден в БД")

        conn.execute(
            """INSERT INTO stock_manual (product_id, quantity)
               VALUES (?, ?)
               ON CONFLICT(product_id) DO UPDATE SET
                   quantity = excluded.quantity,
                   updated_at = datetime('now')""",
            (prod["id"], args.qty),
        )
        conn.commit()

    print(f"Остаток для '{prod['name'][:50]}...' (арт. {args.offer_id}) установлен: {args.qty} шт.")


if __name__ == "__main__":
    main()