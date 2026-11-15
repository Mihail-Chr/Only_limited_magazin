"""
export_xlsx.py — выгрузка в Excel (v4.0).

Листы:
- parsed: parseStatus='ok'
- review: parseStatus='needs_review'
- duplicates: пары по (baseGameName, platformId, editionId, regionId,
  mediaTypeId, publisherId, restore), только parseStatus='ok'.

Запуск: python -m src.scripts.export_xlsx
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import openpyxl
from openpyxl.styles import Font
from src.db import get_conn
from src.config import settings


HEADERS = [
    "productId", "offerId", "name", "baseGameName",
    "type", "platform", "edition", "publisher", "region", "media",
    "restore", "parseStatus", "parseNote",
]

DUP_HEADERS = [
    "pairId", "productIdA", "offerIdA", "nameA", "baseGameNameA",
    "productIdB", "offerIdB", "nameB", "baseGameNameB",
    "platform", "edition", "publisher", "region", "media", "restore",
]


def _rows(conn, status):
    return conn.execute(
        """
        SELECT
            p.productId, p.offerId, p.name, p.baseGameName,
            tg.typeGoodName   AS type,
            pl.platformName || ' ' || pl.platformVersion AS platform,
            ed.editionName    AS edition,
            pub.publisherName AS publisher,
            r.regionCode      AS region,
            mt.mediaTypeName  AS media,
            p.restore, p.parseStatus, p.parseNote
        FROM products p
        LEFT JOIN typeGoods    tg  ON tg.typeGoodId    = p.typeGoodId
        LEFT JOIN platforms    pl  ON pl.platformId    = p.platformId
        LEFT JOIN editionTypes ed  ON ed.editionId     = p.editionId
        LEFT JOIN publishers   pub ON pub.publisherId  = p.publisherId
        LEFT JOIN regions      r   ON r.regionId       = p.regionId
        LEFT JOIN mediaTypes   mt  ON mt.mediaTypeId   = p.mediaTypeId
        WHERE p.parseStatus = ?
        ORDER BY p.baseGameName, p.offerId
        """,
        (status,),
    ).fetchall()


def _write_sheet(ws, headers, rows):
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for r in rows:
        ws.append([r[h] for h in headers])
    # автоширина (простая)
    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)


def _find_duplicates(conn):
    """Пары по (baseGameName, platformId, editionId, regionId, mediaTypeId, publisherId, restore)."""
    rows = conn.execute(
        """
        SELECT
            p.productId, p.offerId, p.name, p.baseGameName,
            pl.platformName || ' ' || pl.platformVersion AS platform,
            ed.editionName    AS edition,
            pub.publisherName AS publisher,
            r.regionCode      AS region,
            mt.mediaTypeName  AS media,
            p.restore,
            p.platformId, p.editionId, p.regionId, p.mediaTypeId, p.publisherId,p.typeGoodId
        FROM products p
        LEFT JOIN platforms    pl  ON pl.platformId    = p.platformId
        LEFT JOIN editionTypes ed  ON ed.editionId     = p.editionId
        LEFT JOIN publishers   pub ON pub.publisherId  = p.publisherId
        LEFT JOIN regions      r   ON r.regionId       = p.regionId
        LEFT JOIN mediaTypes   mt  ON mt.mediaTypeId   = p.mediaTypeId
        WHERE p.parseStatus = 'ok'
        ORDER BY p.baseGameName, p.platformId, p.offerId
        """
    ).fetchall()

    # Группировка по ключу (NULL ≠ значение — учитываем через -1)
    groups = {}
    for r in rows:
        key = (
            (r["baseGameName"] or "").strip().lower(),
            r["platformId"] if r["platformId"] is not None else -1,
            r["editionId"] if r["editionId"] is not None else -1,
            r["regionId"] if r["regionId"] is not None else -1,
            r["mediaTypeId"] if r["mediaTypeId"] is not None else -1,
            r["publisherId"] if r["publisherId"] is not None else -1,
            r["typeGoodId"] if r["typeGoodId"] is not None else -1,  # NEW
            r["restore"] or 0,
        )
        groups.setdefault(key, []).append(r)

    pairs = []
    pair_id = 0
    for key, items in groups.items():
        if len(items) < 2:
            continue
        # попарно (A, B) для всех комбинаций внутри группы
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                pair_id += 1
                a, b = items[i], items[j]
                pairs.append({
                    "pairId": pair_id,
                    "productIdA": a["productId"],
                    "offerIdA": a["offerId"],
                    "nameA": a["name"],
                    "baseGameNameA": a["baseGameName"],
                    "productIdB": b["productId"],
                    "offerIdB": b["offerId"],
                    "nameB": b["name"],
                    "baseGameNameB": b["baseGameName"],
                    "platform": a["platform"],
                    "edition": a["edition"],
                    "publisher": a["publisher"],
                    "region": a["region"],
                    "media": a["media"],
                    "restore": a["restore"],
                })
    return pairs


def main():
    settings.data_exports.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = settings.data_exports / f"parsed_products_{stamp}.xlsx"

    with get_conn() as conn:
        ok_rows = _rows(conn, "ok")
        review_rows = _rows(conn, "needs_review")
        dup_pairs = _find_duplicates(conn)

    wb = openpyxl.Workbook()

    ws_parsed = wb.active
    ws_parsed.title = "parsed"
    _write_sheet(ws_parsed, HEADERS, ok_rows)

    ws_review = wb.create_sheet("review")
    _write_sheet(ws_review, HEADERS, review_rows)

    ws_dup = wb.create_sheet("duplicates")
    _write_sheet(ws_dup, DUP_HEADERS, dup_pairs)

    wb.save(out_path)

    print(f"Файл: {out_path}")
    print(f"  parsed:     {len(ok_rows)}")
    print(f"  review:     {len(review_rows)}")
    print(f"  duplicates: {len(dup_pairs)} пар")


if __name__ == "__main__":
    main()