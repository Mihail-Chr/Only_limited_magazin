import sqlite3
from datetime import datetime
import os

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

DB = 'db/only_limited.sqlite3'
OUT = f'data/exports/duplicates_{datetime.now():%Y%m%d_%H%M%S}.xlsx'

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Логика та же: группы по (baseGameName, platform), где больше 1 товара. Без LIMIT — все группы.
duplicates = conn.execute("""
    SELECT
        baseGameName,
        platform,
        COUNT(*) as cnt,
        GROUP_CONCAT(id) as ids
    FROM product
    WHERE baseGameName IS NOT NULL
      AND baseGameName != ''
      AND platform IS NOT NULL
    GROUP BY baseGameName, platform
    HAVING cnt > 1
    ORDER BY cnt DESC, baseGameName
""").fetchall()

# Готовим книгу
wb = Workbook()
ws = wb.active
ws.title = "Дубли"

# Заголовки
headers = [
    "GROUP_ID", "GROUP_SIZE", "PRODUCT_ID", "OFFER_ID", "TYPE", "EDITION",
    "BASE_NAME", "PLATFORM", "SALES_CNT", "SALES_QTY", "STOCK", "LISTINGS", "NAME"
]
ws.append(headers)

# Стиль заголовка
header_font = Font(bold=True, color="FFFFFF")
header_fill = PatternFill("solid", fgColor="305496")
for col_idx, _ in enumerate(headers, start=1):
    cell = ws.cell(row=1, column=col_idx)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")

total_groups = 0
total_products = 0
row_idx = 2

# Чередование цвета групп (для читаемости)
group_fill_even = PatternFill("solid", fgColor="F2F2F2")
group_fill_odd = PatternFill("solid", fgColor="FFFFFF")

for group_idx, d in enumerate(duplicates, start=1):
    total_groups += 1
    ids = [int(x) for x in d['ids'].split(',')]

    fill = group_fill_even if group_idx % 2 == 0 else group_fill_odd

    for product_id in ids:
        total_products += 1

        prod = conn.execute(
            "SELECT id, offer_id, name, product_type, edition FROM product WHERE id = ?",
            (product_id,)
        ).fetchone()

        listings = conn.execute("""
            SELECT s.name AS store_name, l.price, l.status
            FROM listing l
            JOIN store s ON s.id = l.store_id
            WHERE l.product_id = ?
        """, (product_id,)).fetchall()

        sales = conn.execute("""
            SELECT COUNT(*) as cnt, SUM(quantity) as total_qty
            FROM posting_item
            WHERE product_id = ?
        """, (product_id,)).fetchone()

        stock = conn.execute(
            "SELECT quantity FROM stock_manual WHERE product_id = ?",
            (product_id,)
        ).fetchone()

        listings_str = "; ".join(
            f"{l['store_name']}:{l['price']}({l['status']})" for l in listings
        ) or "-"

        ws.append([
            group_idx,
            d['cnt'],
            product_id,
            prod['offer_id'],
            prod['product_type'],
            prod['edition'],
            d['baseGameName'],
            d['platform'],
            sales['cnt'],
            sales['total_qty'] or 0,
            stock['quantity'] if stock else 0,
            listings_str,
            prod['name'],
        ])

        # Красим строку в цвет группы
        for col_idx in range(1, len(headers) + 1):
            ws.cell(row=row_idx, column=col_idx).fill = fill

        row_idx += 1

# Автоширина колонок (по максимальному содержимому, с ограничением сверху)
for col_idx, header in enumerate(headers, start=1):
    max_len = len(header)
    for row in ws.iter_rows(min_col=col_idx, max_col=col_idx, min_row=2, values_only=True):
        val = row[0]
        if val is not None:
            max_len = max(max_len, len(str(val)))
    ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 60)

# Закрепляем шапку
ws.freeze_panes = "A2"

# Автофильтр по шапке
ws.auto_filter.ref = ws.dimensions

# Лист «Итого»
ws2 = wb.create_sheet("Итого")
ws2.append(["Показатель", "Значение"])
ws2.append(["Сформирован", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
ws2.append(["База", DB])
ws2.append(["Группировка", "baseGameName + platform (строки как есть, без нормализации)"])
ws2.append(["Групп дублей", total_groups])
ws2.append(["Товаров в них", total_products])
for col_idx in (1, 2):
    ws2.cell(row=1, column=col_idx).font = header_font
    ws2.cell(row=1, column=col_idx).fill = header_fill
ws2.column_dimensions["A"].width = 30
ws2.column_dimensions["B"].width = 60

# Сохраняем
os.makedirs('data/exports', exist_ok=True)
wb.save(OUT)

print(f"Готово: {OUT}")
print(f"Групп: {total_groups}, товаров: {total_products}")