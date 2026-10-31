"""
Прогон тест-кейсов для parse_name.

Использование:
    python -m src.parsers.tests.runner                # прогон фикс-кейсов
    python -m src.parsers.tests.runner --random 20    # 20 случайных из БД (только печать)

Импортирует parse_name из src.scripts.parse_names — пока не вынесли в отдельный модуль.
"""
import sys
import argparse

from src.parsers.tests.cases import CASES
from src.scripts.parse_names import parse_name


CHECK_FIELDS = ["type", "base_name", "platform", "edition", "publisher", "region", "media_type"]


def run_fixed_cases() -> int:
    """Прогоняет фикс-кейсы. Возвращает число упавших."""
    failed = 0
    total = len(CASES)

    for case in CASES:
        case_id = case["id"]
        input_name = case["input"]
        expect = case["expect"]

        try:
            actual = parse_name(input_name)
        except Exception as e:
            print(f"❌ [{case_id}] ИСКЛЮЧЕНИЕ при разборе: {e}")
            failed += 1
            continue

        mismatches = []
        for field in CHECK_FIELDS:
            if field not in expect:
                continue
            exp_val = expect[field]
            act_val = actual.get(field)
            if exp_val != act_val:
                mismatches.append(f"      {field}: ожидали {exp_val!r}, получили {act_val!r}")

        if mismatches:
            failed += 1
            print(f"❌ [{case_id}] {input_name!r}")
            for m in mismatches:
                print(m)
            if "note" in case:
                print(f"      note: {case['note']}")
        else:
            print(f"✅ [{case_id}] {input_name!r}")

    print()
    print(f"Итого: {total - failed} / {total} зелёных, {failed} красных.")
    return failed


def run_random(n: int) -> int:
    """Печатает n случайных товаров из БД — как парсер их собирает (для глаз)."""
    import sqlite3

    conn = sqlite3.connect("db/only_limited.sqlite3")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT offer_id, name FROM product WHERE name IS NOT NULL ORDER BY RANDOM() LIMIT ?",
        (n,),
    ).fetchall()

    print(f"Случайные {len(rows)} товаров (только печать, без проверки):\n")
    for r in rows:
        parsed = parse_name(r["name"])
        print(f"  offer_id: {r['offer_id']}")
        print(f"  name:     {r['name']}")
        print(f"    type:      {parsed.get('type')}")
        print(f"    base_name: {parsed.get('base_name')}")
        print(f"    platform:  {parsed.get('platform')}")
        print(f"    edition:   {parsed.get('edition')}")
        print(f"    publisher: {parsed.get('publisher')}")
        print(f"    region:    {parsed.get('region')}")
        print(f"    media:     {parsed.get('media_type')}")
        print()

    return 0


def main():
    parser = argparse.ArgumentParser(description="Прогон тест-кейсов parse_name")
    parser.add_argument(
        "--random", type=int, metavar="N",
        help="Печать N случайных товаров из БД (без проверки)",
    )
    args = parser.parse_args()

    if args.random:
        sys.exit(run_random(args.random))
    else:
        failed = run_fixed_cases()
        sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()