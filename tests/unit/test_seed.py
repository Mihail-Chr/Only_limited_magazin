"""
Тесты для seed_reference_data.py (v3.1).

Запуск: pytest tests/unit/test_seed.py -v
"""
import sqlite3


TEST_DB_PATH = "db/test_only_limited.sqlite3"


def get_test_conn():
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def test_modules_seeded():
    """modules: 6 модулей, sale=1, purchase=0."""
    conn = get_test_conn()
    rows = conn.execute("SELECT moduleName, isEnabled FROM modules").fetchall()
    conn.close()

    names = {r["moduleName"]: r["isEnabled"] for r in rows}
    assert len(rows) == 6, f"Ожидалось 6 модулей, получено {len(rows)}"
    assert names.get("sale") == 1
    assert names.get("purchase") == 0
    assert names.get("inventory") == 1
    assert names.get("manual_sale") == 1
    assert names.get("ozon_sync") == 1
    assert names.get("monitoring") == 0


def test_currencies_seeded():
    """currencies: 5 валют, RUB id=1."""
    conn = get_test_conn()
    rows = conn.execute("SELECT currencyId, currencyCode FROM currencies").fetchall()
    conn.close()

    assert len(rows) == 5, f"Ожидалось 5 валют, получено {len(rows)}"
    rub = [r for r in rows if r["currencyCode"] == "RUB"]
    assert len(rub) == 1
    assert rub[0]["currencyId"] == 1


def test_regions_seeded():
    """regions: 9 регионов, с regionName."""
    conn = get_test_conn()
    rows = conn.execute("SELECT regionCode, regionName FROM regions").fetchall()
    conn.close()

    assert len(rows) == 9, f"Ожидалось 9 регионов, получено {len(rows)}"
    codes = {r["regionCode"] for r in rows}
    assert "RU" in codes
    assert "US" in codes
    assert "EU" in codes
    for r in rows:
        assert r["regionName"], f"regionName пустой для {r['regionCode']}"


def test_platforms_seeded():
    """platforms: 30+, PlayStation 4/5, isPortable."""
    conn = get_test_conn()
    rows = conn.execute("SELECT platformName, platformVersion, isPortable FROM platforms").fetchall()
    conn.close()

    assert len(rows) >= 30, f"Ожидалось 30+ платформ, получено {len(rows)}"

    ps45 = [r for r in rows if r["platformName"] == "PlayStation" and r["platformVersion"] == "4/5"]
    assert len(ps45) == 1, "PlayStation 4/5 не найдена"

    portable = [r for r in rows if r["isPortable"] == 1]
    assert len(portable) >= 5, f"Ожидалось 5+ портативных, получено {len(portable)}"


def test_typeGoods_seeded():
    """typeGoods: 12 типов."""
    conn = get_test_conn()
    rows = conn.execute("SELECT typeGoodName FROM typeGoods").fetchall()
    conn.close()

    assert len(rows) == 12, f"Ожидалось 12 типов, получено {len(rows)}"
    names = {r["typeGoodName"] for r in rows}
    assert "game" in names
    assert "bundle" in names
    assert "steelbook" in names


def test_editionTypes_seeded():
    """editionTypes: 45+ изданий (включая GOTY и Game of the Year)."""
    conn = get_test_conn()
    rows = conn.execute("SELECT editionName FROM editionTypes ORDER BY sortOrder").fetchall()
    conn.close()

    assert len(rows) >= 45, f"Ожидалось 45+ изданий, получено {len(rows)}"
    names = {r["editionName"] for r in rows}

    assert "Standard" in names
    assert "Deluxe" in names
    assert "Ultimate" in names
    assert "Collector's" in names
    assert "Steelbook" in names

    assert "GOTY" in names
    assert "Game of the Year" in names

    assert "Legendary Edition" in names
    assert "Legendary Edition Steelbook" in names
    assert "Anniversary Collection" in names
    assert "Collection" in names
    assert "Survivor Steelbook" in names

    assert "Platinum" in names
    assert "Black" in names
    assert "Tails" in names
    assert "Knuckles" in names


def test_editionTypes_no_duplicates():
    """editionTypes: нет дублей по editionName."""
    conn = get_test_conn()
    rows = conn.execute(
        "SELECT editionName, COUNT(*) as cnt FROM editionTypes GROUP BY editionName HAVING cnt > 1"
    ).fetchall()
    conn.close()
    assert len(rows) == 0, f"Дубли в editionTypes: {[r['editionName'] for r in rows]}"


def test_publishers_seeded():
    """publishers: 30 издателей."""
    conn = get_test_conn()
    rows = conn.execute("SELECT publisherName FROM publishers").fetchall()
    conn.close()

    assert len(rows) == 30, f"Ожидалось 30 издателей, получено {len(rows)}"
    names = {r["publisherName"] for r in rows}
    assert "Nintendo" in names
    assert "Limited Run Games" in names
    assert "Super Rare Games" in names


def test_statuses_seeded():
    """statuses: 10 статусов (5 продажа + 5 закупка)."""
    conn = get_test_conn()
    rows = conn.execute("SELECT statusName, statusType FROM statuses").fetchall()
    conn.close()

    assert len(rows) == 10, f"Ожидалось 10 статусов, получено {len(rows)}"
    sale = [r for r in rows if r["statusType"] == "sale"]
    purchase = [r for r in rows if r["statusType"] == "purchase"]
    assert len(sale) == 5, f"Ожидалось 5 статусов продажи, получено {len(sale)}"
    assert len(purchase) == 5, f"Ожидалось 5 статусов закупки, получено {len(purchase)}"


def test_mediaTypes_seeded():
    """mediaTypes: 6 типов."""
    conn = get_test_conn()
    rows = conn.execute("SELECT mediaTypeName FROM mediaTypes").fetchall()
    conn.close()

    assert len(rows) == 6, f"Ожидалось 6 типов носителей, получено {len(rows)}"
    names = {r["mediaTypeName"] for r in rows}
    assert "physical" in names
    assert "digital" in names


def test_ageGroups_seeded():
    """ageGroups: 5 групп, 25-34 id=2."""
    conn = get_test_conn()
    rows = conn.execute("SELECT ageGroupId, ageGroupName FROM ageGroups").fetchall()
    conn.close()

    assert len(rows) == 5, f"Ожидалось 5 групп, получено {len(rows)}"
    for r in rows:
        if r["ageGroupName"] == "25-34":
            assert r["ageGroupId"] == 2


def test_adjustmentTypes_seeded():
    """adjustmentTypes: 7 типов."""
    conn = get_test_conn()
    rows = conn.execute("SELECT code FROM adjustmentTypes").fetchall()
    conn.close()

    assert len(rows) == 7, f"Ожидалось 7 типов корректировок, получено {len(rows)}"
    codes = {r["code"] for r in rows}
    assert "commission" in codes
    assert "refund" in codes


def test_warehouses_seeded():
    """warehouses: 2 склада (Виталий id=1, Вениамин id=2)."""
    conn = get_test_conn()
    rows = conn.execute("SELECT warehouseId, name FROM warehouses").fetchall()
    conn.close()

    assert len(rows) == 2, f"Ожидалось 2 склада, получено {len(rows)}"
    names = {r["name"] for r in rows}
    assert "Виталий" in names
    assert "Вениамин" in names
    vit = [r for r in rows if r["name"] == "Виталий"]
    assert vit[0]["warehouseId"] == 1


def test_marketplaces_seeded():
    """marketplaces: 5 площадок."""
    conn = get_test_conn()
    rows = conn.execute("SELECT code FROM marketplaces").fetchall()
    conn.close()

    assert len(rows) == 5, f"Ожидалось 5 площадок, получено {len(rows)}"
    codes = {r["code"] for r in rows}
    assert "ozon" in codes
    assert "manual" in codes


def test_purchasePlatforms_seeded():
    """purchasePlatforms: 10 площадок."""
    conn = get_test_conn()
    rows = conn.execute("SELECT code FROM purchasePlatforms").fetchall()
    conn.close()

    assert len(rows) == 10, f"Ожидалось 10 площадок закупки, получено {len(rows)}"
    codes = {r["code"] for r in rows}
    assert "avito_ru" in codes
    assert "ebay_us" in codes


def test_stores_seeded():
    """stores: 3 магазина."""
    conn = get_test_conn()
    rows = conn.execute("SELECT code FROM stores").fetchall()
    conn.close()

    assert len(rows) == 3, f"Ожидалось 3 магазина, получено {len(rows)}"
    codes = {r["code"] for r in rows}
    assert "limited_games" in codes
    assert "console_games" in codes
    assert "manual" in codes


def test_buyers_seeded():
    """buyers: 1 покупатель (Физлицо id=1)."""
    conn = get_test_conn()
    rows = conn.execute("SELECT buyerId, buyerNickname FROM buyers").fetchall()
    conn.close()

    assert len(rows) == 1, f"Ожидалось 1 покупатель, получено {len(rows)}"
    assert rows[0]["buyerId"] == 1
    assert rows[0]["buyerNickname"] == "Физлицо"