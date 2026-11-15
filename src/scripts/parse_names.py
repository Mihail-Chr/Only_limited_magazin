"""
parse_names.py — разбор названий товаров (v4.0). Обёртка над src.parsers.

Читает products.name, вызывает parse_name, пишет ID + parseStatus + parseNote.

Запуск: python -m src.scripts.parse_names
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db import get_conn
from src.parsers.extractor import load_dictionaries, parse_name


def main():
    with get_conn() as conn:
        load_dictionaries(conn)

        rows = conn.execute(
            "SELECT productId, name FROM products WHERE name IS NOT NULL"
        ).fetchall()

        total = len(rows)
        needs_review = 0

        for i, r in enumerate(rows):
            p = parse_name(r["name"], conn)

            # parseNote — список → JSON (для UI)
            note_json = json.dumps(p["parseNote"], ensure_ascii=False) if p["parseNote"] else None

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
                    parseStatus = ?,
                    parseNote = ?,
                    updatedAt = datetime('now')
                WHERE productId = ?
                """,
                (
                    p["typeGoodId"],
                    p["baseGameName"],
                    p["platformId"],
                    p["editionId"],
                    p["publisherId"],
                    p["regionId"],
                    p["mediaTypeId"],
                    p["restore"],
                    p["parseStatus"],
                    note_json,
                    r["productId"],
                ),
            )

            if p["parseStatus"] == "needs_review":
                needs_review += 1

            if (i + 1) % 200 == 0:
                conn.commit()
                print(f"  → Обработано: {i + 1}/{total}")

        conn.commit()

    print(f"Обработано товаров: {total}")
    print(f"needs_review: {needs_review}")
    print(f"ok: {total - needs_review}")


if __name__ == "__main__":
    main()