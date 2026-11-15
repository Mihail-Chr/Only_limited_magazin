"""
fetch_postings.py — универсальная загрузка отправлений (продаж) с площадки (v3.3).

Логика:
1. Проверяем магазин в БД и .env.
2. Загружаем отправления в память.
3. Сохраняем сырой JSON (для истории).
4. Идём по заказам:
   - Ищем по marketplaceOrderId.
   - Если ЕСТЬ: пропускаем. Проверяем "чудеса" (дата/сумма) -> в warnings.
   - Если НЕТ: создаём salesOrder + salesOrderItem + statusHistory.
5. Сохраняем отчет в logs/ и в syncLog.notes.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db import get_conn
from src.config import settings

DATA_API_RAW = Path("data/api_raw")
LOGS_DIR = Path("logs")


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ
# =====================================================================

def _read_env(platform: str, store_code: str) -> tuple[str | None, str | None]:
    prefix = platform.upper()
    store_upper = store_code.upper()
    client_id = os.getenv(f"{prefix}_{store_upper}_CLIENT_ID")
    api_key = os.getenv(f"{prefix}_{store_upper}_API_KEY")
    if client_id: client_id = client_id.strip().strip('"').strip("'")
    if api_key: api_key = api_key.strip().strip('"').strip("'")
    return client_id or None, api_key or None


def _create_client(platform: str, client_id: str, api_key: str):
    if platform == "ozon":
        from src.clients.ozon import OzonClient
        return OzonClient(client_id, api_key)
    raise ValueError(f"Неизвестная площадка: {platform}")


def _parse_quantity(value) -> tuple[int, str | None]:
    if value is None:
        return 0, "quantity None -> 0"
    if isinstance(value, str):
        s = value.strip()
        if not s: return 0, "quantity пустой -> 0"
        try: num = int(s)
        except ValueError: return 0, f"quantity '{value}' -> 0"
    else:
        try: num = int(value)
        except (ValueError, TypeError): return 0, f"quantity '{value}' -> 0"

    if num < 0: return abs(num), f"quantity < 0 (abs): {num} -> {abs(num)}"
    if num == 0: return 0, "quantity = 0 -> ошибка (не создаём)"
    return num, None


def _parse_price(value) -> tuple[float, str | None]:
    if value is None: return 0.0, "price None -> 0"
    if isinstance(value, dict): value = value.get("amount")
    if isinstance(value, str):
        s = value.strip()
        if not s: return 0.0, "price пустой -> 0"
        try: num = float(s)
        except ValueError: return 0.0, f"price '{value}' -> 0"
    else:
        try: num = float(value)
        except (ValueError, TypeError): return 0.0, f"price '{value}' -> 0"

    if num < 0: return abs(num), f"price < 0 (abs): {num} -> {abs(num)}"
    return num, None


def _find_or_create_status(conn, status_name: str) -> int | None:
    if not status_name: return None
    row = conn.execute("SELECT statusId FROM statuses WHERE statusName = ? AND statusType = 'sale'", (status_name,)).fetchone()
    if row: return row["statusId"]
    cur = conn.execute("INSERT INTO statuses (statusName, statusType, sortOrder, isActive) VALUES (?, 'sale', 999, 1)", (status_name,))
    return cur.lastrowid


def _find_or_create_buyer(conn, buyer_nickname: str | None) -> int:
    nickname = (buyer_nickname or "").strip()
    if not nickname: return 1
    row = conn.execute("SELECT buyerId FROM buyers WHERE buyerNickname = ?", (nickname,)).fetchone()
    if row: return row["buyerId"]
    cur = conn.execute("INSERT INTO buyers (buyerNickname, ageGroupId) VALUES (?, 2)", (nickname,))
    return cur.lastrowid


def _find_or_create_product(conn, offer_id: str) -> int:
    row = conn.execute("SELECT productId FROM products WHERE offerId = ?", (offer_id,)).fetchone()
    if row: return row["productId"]
    cur = conn.execute("INSERT INTO products (offerId, name, isActive) VALUES (?, ?, 1)", (offer_id, f"Товар {offer_id}"))
    return cur.lastrowid


# =====================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# =====================================================================

def fetch_postings(platform: str, store_code: str, date_from: str, date_to: str, client=None) -> dict:
    errors = []
    warnings = []
    created = 0
    skipped = 0

    with get_conn() as conn:
        store = conn.execute("SELECT storeId, marketplaceId, hasApi FROM stores WHERE code = ?", (store_code,)).fetchone()
        if not store:
            return {"ok": False, "error": f"Магазин '{store_code}' не найден"}

        client_id, api_key = _read_env(platform, store_code)
        has_api = store["hasApi"]
        has_env = bool(client_id and api_key)

        if has_api and not has_env:
            return {"ok": False, "error": "hasApi=1, но нет ключей в .env"}

        if platform not in ("ozon", "ym", "wb"):
            return {"ok": False, "error": f"Площадка '{platform}' не найдена"}

        # Проверка hasApi=0
        if not has_api and not has_env:
            return {"ok": False, "error": f"hasApi=0 и нет ключей в .env для '{store_code}'"}
        
        # Предупреждение hasApi=0, но ключи есть
        if not has_api and has_env:
            errors.append(f"hasApi=0, но ключи в .env есть. Обновите stores.hasApi для '{store_code}'")

        if client is None:
            try:
                client = _create_client(platform, client_id, api_key)
            except Exception as e:
                return {"ok": False, "error": str(e)}

        print(f"[1/4] Загрузка отправлений ({platform}/{store_code})...")
        try:
            postings = client.get_postings(date_from, date_to)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        print(f"  -> Получено: {len(postings)}")
        if not postings:
            return {"ok": True, "created": 0, "skipped": 0, "warnings": [], "report": "Нет данных"}

        # Сохраняем сырой JSON
        DATA_API_RAW.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_path = DATA_API_RAW / f"{platform}_{store_code}_postings_{date_from}_{stamp}.json"
        raw_path.write_text(json.dumps(postings, ensure_ascii=False, indent=2), encoding="utf-8")

        marketplace_id = store["marketplaceId"]
        print(f"[2/4] Обработка заказов (дедупликация)...")

        for p in postings:
            if not p:
                warnings.append("Пропущен пустой заказ (None) в ответе API")
                continue
            posting_number = p.get("posting_number")
            if not posting_number: continue

            # --- 1. ИЩЕМ СУЩЕСТВУЮЩИЙ ЗАКАЗ ---
            existing = conn.execute(
                "SELECT salesOrderId, createdAt FROM salesOrders WHERE marketplaceOrderId = ?",
                (posting_number,)
            ).fetchone()

            if existing:
                skipped += 1
                # Проверка на "чудеса" (дата)
                db_date = existing["createdAt"][:10] if existing["createdAt"] else "?"
                api_date = (p.get("created_at") or "")[:10]
                if db_date != api_date and api_date:
                    warnings.append(f"Заказ {posting_number}: Дата в БД {db_date}, в OZON {api_date}")
                continue # Пропускаем заказ

            # --- 2. СОЗДАЕМ НОВЫЙ ЗАКАЗ ---
            buyer_id = _find_or_create_buyer(conn, p.get("buyer_nickname"))
            created_at = p.get("created_at") or datetime.now().isoformat()
            
            cur = conn.execute(
                """INSERT INTO salesOrders (buyerId, marketplaceId, marketplaceOrderId, currencyId, createdAt)
                   VALUES (?, ?, ?, 1, ?)""",
                (buyer_id, marketplace_id, posting_number, created_at)
            )
            sales_order_id = cur.lastrowid
            created += 1

            # Статус
            status_name = p.get("status")
            status_id = _find_or_create_status(conn, status_name)
            if status_id:
                conn.execute(
                    "INSERT INTO salesOrderStatusHistory (salesOrderId, statusId, statusDate) VALUES (?, ?, ?)",
                    (sales_order_id, status_id, created_at)
                )

            # Товары
            for prod in p.get("products", []) or []:
                if not prod: continue
                offer_id = prod.get("offer_id")
                if not offer_id: continue

                quantity, q_err = _parse_quantity(prod.get("quantity"))
                if q_err: warnings.append(f"Заказ {posting_number}: {q_err}")
                if quantity <= 0: continue

                price, p_err = _parse_price(prod.get("price"))
                if p_err: warnings.append(f"Заказ {posting_number}: {p_err}")

                product_id = _find_or_create_product(conn, offer_id)
                conn.execute(
                    "INSERT INTO salesOrderItems (salesOrderId, productId, quantity, salePrice, warehouseId) VALUES (?, ?, ?, ?, 1)",
                    (sales_order_id, product_id, quantity, price)
                )

        conn.commit()
        print(f"  -> Создано: {created}, пропущено (дубли): {skipped}, предупреждений: {len(warnings)}")

        # --- ФОРМИРУЕМ ОТЧЕТ ---
        report_lines = [
            f"=== Отчет о загрузке движений ({platform}/{store_code}) ===",
            f"Период: {date_from} — {date_to}",
            f"Всего в API: {len(postings)}",
            f"Создано новых: {created}",
            f"Пропущено (уже в БД): {skipped}",
            f"Предупреждений: {len(warnings)}",
            "",
        ]
        if warnings:
            report_lines.append("--- ПРЕДУПРЕЖДЕНИЯ (ЧУДЕСА) ---")
            report_lines.extend(warnings)
        report_text = "\n".join(report_lines)

        # Сохраняем в файл
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOGS_DIR / f"postings_{platform}_{store_code}_{stamp}.txt"
        log_path.write_text(report_text, encoding="utf-8")

        # Сохраняем в БД (syncLog)
        conn.execute(
            "INSERT INTO syncLog (syncType, dateFrom, dateTo, recordsCount, notes) VALUES ('ozon_sales', ?, ?, ?, ?)",
            (date_from, date_to, created, report_text)
        )
        conn.commit()

        print(f"[4/4] Отчет сохранен: {log_path}")
        return {
            "ok": True,
            "created": created,
            "skipped": skipped,
            "warnings": warnings,
            "report": report_text,
        }

# =====================================================================
# CLI
# =====================================================================

def main():
    if len(sys.argv) < 5:
        print("Использование: python -m src.scripts.fetch_postings <platform> <store_code> <date_from> <date_to>")
        sys.exit(1)

    result = fetch_postings(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

    if result["ok"]:
        print(result["report"])
        sys.exit(0)
    else:
        print(f"ОШИБКА: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()