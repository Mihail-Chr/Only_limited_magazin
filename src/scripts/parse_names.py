"""
parse_names.py — разбор названий товаров (v3.7).

Запуск:
    python -m src.scripts.parse_names

Что делает:
- Читает products.name (сырое из API).
- Разбирает через parse_name(name, conn).
- Обновляет products: typeGoodId, baseGameName, platformId,
  editionId, publisherId, regionId, mediaTypeId, restore.
"""
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db import get_conn
from src.parsers.parser import load_dictionaries, parse_name


def main():
    with get_conn() as conn:
        # Загружаем справочники в модуль парсера
        load_dictionaries(conn)

        rows = conn.execute(
            "SELECT productId, name FROM products WHERE name IS NOT NULL"
        ).fetchall()

        updated = 0

        for r in rows:
            parsed = parse_name(r["name"], conn)

            conn.execute(
                """
                UPDATE products SET
                    typeGoodId = ?,
                    baseGameName = ?,
                    platformId = ?,
                    editionId = ?,
                    publisherId = ?,
                    regionId = ?,
                    mediaTypeId = ?,
                    restore = ?,
                    updatedAt = datetime('now')
                WHERE productId = ?
                """,
                (
                    parsed["typeGoodId"],
                    parsed["baseGameName"],
                    parsed["platformId"],
                    parsed["editionId"],
                    parsed["publisherId"],
                    parsed["regionId"],
                    parsed["mediaTypeId"],
                    parsed["restore"],
                    r["productId"],
                ),
            )
            updated += 1

        conn.commit()

    print(f"Обработано товаров: {updated}")

    with get_conn() as conn:
        print("\nСлучайные примеры после разбора:")
        samples = conn.execute("""
            SELECT productId, offerId, name, baseGameName, typeGoodId,
                   platformId, editionId, publisherId, regionId, mediaTypeId, restore
            FROM products
            ORDER BY RANDOM()
            LIMIT 10
        """).fetchall()
        for s in samples:
            print(f"  productId: {s['productId']}, offerId: {s['offerId']}")
            print(f"    name: {s['name']}")
            print(f"    baseGameName: {s['baseGameName']}")
            print(f"    typeGoodId: {s['typeGoodId']}, platformId: {s['platformId']}, editionId: {s['editionId']}")
            print(f"    publisherId: {s['publisherId']}, regionId: {s['regionId']}, mediaTypeId: {s['mediaTypeId']}")
            print(f"    restore: {s['restore']}")
            print()


if __name__ == "__main__":
    main()