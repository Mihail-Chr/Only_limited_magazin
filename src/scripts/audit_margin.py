"""
Аудит маржи: сравнение цены Ozon и себестоимости с учётом комиссии Ozon.
Запуск: python -m src.scripts.audit_margin
"""
from src.db import get_conn


def main() -> None:
    with get_conn() as conn:
        # Пересчитываем payout_amount для тех, у кого не заполнено
        conn.execute(
            """
            UPDATE listing
            SET payout_amount = price * (1 - COALESCE(commission_rate, 0.45))
            WHERE price IS NOT NULL AND price > 0 AND payout_amount IS NULL
            """
        )
        conn.commit()

        rows = conn.execute(
            """
            SELECT 
                p.offer_id, 
                p.name, 
                l.price, 
                l.commission_rate,
                l.payout_amount,
                p.cost_price_synthetic,
                CASE WHEN p.cost_price_synthetic > 0 
                     THEN ROUND((l.price - p.cost_price_synthetic) / l.price * 100, 1)
                     ELSE NULL END AS margin_gross_pct,
                CASE WHEN p.cost_price_synthetic > 0 AND l.payout_amount > 0
                     THEN ROUND((l.payout_amount - p.cost_price_synthetic) / l.payout_amount * 100, 1)
                     ELSE NULL END AS margin_net_pct
            FROM product p
            JOIN listing l ON l.product_id = p.id
            WHERE l.price IS NOT NULL AND l.price > 0
            ORDER BY margin_net_pct ASC
            LIMIT 20
            """
        ).fetchall()

    print(f"{'Артикул':<10} | {'Цена':<8} | {'Комис.':<6} | {'На руки':<8} | {'Себест.':<8} | {'Вал.%':<6} | {'Чист.%':<6} | {'Название':<30}")
    print("-" * 110)
    for r in rows:
        name = (r["name"] or "")[:27] + "..." if len(r["name"] or "") > 30 else (r["name"] or "")
        comm = f"{r['commission_rate']*100:.0f}%"
        print(f"{r['offer_id']:<10} | {r['price']:<8.2f} | {comm:<6} | {r['payout_amount']:<8.2f} | {r['cost_price_synthetic']:<8.2f} | {r['margin_gross_pct']:<6.1f} | {r['margin_net_pct']:<6.1f} | {name:<30}")


if __name__ == "__main__":
    main()