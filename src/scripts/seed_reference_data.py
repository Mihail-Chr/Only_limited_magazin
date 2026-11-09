"""
Заполнение справочников (v3.1).

Запуск: python -m src.scripts.seed_reference_data

Идемпотентен: INSERT OR IGNORE (повторный запуск не ломает).
"""
from src.db import get_conn


def seed_modules(conn):
    """Модули (feature flags)."""
    modules = [
        ('purchase', 0, 10, 'Закупка (purchaseOrders, shipments)'),
        ('sale', 1, 20, 'Продажа (salesOrders, payouts)'),
        ('inventory', 1, 30, 'Инвентаризация (stockHistory)'),
        ('ozon_sync', 1, 40, 'Синхронизация с OZON'),
        ('manual_sale', 1, 50, 'Ручная продажа'),
        ('monitoring', 0, 60, 'Мониторинг цен (avgSellCost)'),
    ]
    for name, enabled, sort, desc in modules:
        conn.execute(
            "INSERT OR IGNORE INTO modules (moduleName, isEnabled, sortOrder, description, versionAdded) VALUES (?, ?, ?, ?, '3.1')",
            (name, enabled, sort, desc)
        )


def seed_currencies(conn):
    """Валюты (RUB id=1 — явно, для salesOrders.currencyId)."""
    currencies = [
        (1, 'RUB', 'Российский рубль', '₽', 10),
        (2, 'USD', 'Доллар США', '$', 20),
        (3, 'EUR', 'Евро', '€', 30),
        (4, 'GBP', 'Фунт стерлингов', '£', 40),
        (5, 'JPY', 'Японская иена', '¥', 50),
    ]
    for cid, code, name, symbol, sort in currencies:
        conn.execute(
            "INSERT OR IGNORE INTO currencies (currencyId, currencyCode, currencyName, currencySymbol, sortOrder) VALUES (?, ?, ?, ?, ?)",
            (cid, code, name, symbol, sort)
        )


def seed_regions(conn):
    """Регионы (с полными названиями)."""
    regions = [
        ('RU', 'Россия', 10),
        ('US', 'США', 20),
        ('EU', 'Европа', 30),
        ('JP', 'Япония', 40),
        ('Asia', 'Азия', 50),
        ('CN', 'Китай', 60),
        ('AUS', 'Австралия', 70),
        ('SA', 'Южная Америка', 80),
        ('KR', 'Корея', 90),
    ]
    for code, name, sort in regions:
        conn.execute(
            "INSERT OR IGNORE INTO regions (regionCode, regionName, sortOrder) VALUES (?, ?, ?)",
            (code, name, sort)
        )


def seed_platforms(conn):
    """Платформы (с версиями, ревизиями, портативностью)."""
    platforms = [
        ('PC', 'Windows', None, 0),
        ('Steam Deck', 'LCD/OLED', None, 0),
        ('PlayStation', '5', None, 0),
        ('PlayStation', '5', 'Slim', 0),
        ('PlayStation', '5', 'Pro', 0),
        ('PlayStation', '4', None, 0),
        ('PlayStation', '4', 'Slim', 0),
        ('PlayStation', '4', 'Pro', 0),
        ('PlayStation', '4/5', None, 0),
        ('PlayStation', '3', None, 0),
        ('PlayStation', '3', 'Slim', 0),
        ('PlayStation', '3', 'Super Slim', 0),
        ('PlayStation', '2', None, 0),
        ('PlayStation', '2', 'Slim', 0),
        ('PlayStation', '1', None, 0),
        ('Xbox', 'Series', 'X', 0),
        ('Xbox', 'Series', 'S', 0),
        ('Xbox', 'One', None, 0),
        ('Xbox', 'One', 'S', 0),
        ('Xbox', 'One', 'X', 0),
        ('Xbox', '360', None, 0),
        ('Xbox', '360', 'S', 0),
        ('Xbox', '360', 'E', 0),
        ('Xbox', 'Original', None, 0),
        ('Xbox', 'One / Series', None, 0),
        ('Nintendo Switch', '2', None, 0),
        ('Nintendo Switch', '1', None, 0),
        ('Nintendo Switch', '1', 'OLED', 0),
        ('Nintendo Switch', '1', 'Lite', 1),
        ('Nintendo Switch', '1 / 2', None, 0),
        ('Nintendo', 'Wii U', None, 0),
        ('Nintendo', 'Wii', None, 0),
        ('Nintendo', 'GameCube', None, 0),
        ('Nintendo', '64', None, 0),
        ('Nintendo', 'SNES', None, 0),
        ('Nintendo', 'NES', None, 0),
        ('Nintendo', '3DS', None, 1),
        ('Nintendo', 'DS', None, 1),
        ('Nintendo', 'Game Boy Advance', None, 1),
        ('Nintendo', 'Game Boy Color', None, 1),
        ('Nintendo', 'Game Boy', None, 1),
        ('Sega', 'Mega Drive', None, 0),
        ('Sega', 'Dreamcast', None, 0),
        ('Sega', 'Saturn', None, 0),
        ('Sega', 'Game Gear', None, 1),
        ('Atari', '2600', None, 0),
    ]
    for i, (name, version, revision, is_portable) in enumerate(platforms):
        conn.execute(
            """INSERT OR IGNORE INTO platforms 
               (platformName, platformVersion, revision, isPortable, sortOrder) 
               VALUES (?, ?, ?, ?, ?)""",
            (name, version, revision, is_portable, (i + 1) * 10)
        )


def seed_typeGoods(conn):
    """Типы товаров."""
    types = [
        ('game', 10), ('bundle', 20), ('steelbook', 30), ('gamepad', 40),
        ('joystick', 50), ('collectorBox', 60), ('accessory', 70),
        ('card', 80), ('toy', 90), ('figure', 100), ('badge', 110), ('sticker', 120)
    ]
    for name, sort in types:
        conn.execute(
            "INSERT OR IGNORE INTO typeGoods (typeGoodName, sortOrder) VALUES (?, ?)",
            (name, sort)
        )


def seed_editionTypes(conn):
    """
    Типы изданий — ВСЁ, что парсер может найти (точное совпадение, нормализованное).

    Источник истины. Парсер НЕ создаёт. Если фразы нет — editionId = None.
    GOTY и Game of the Year — ОБА (разные написания в данных).
    """
    editions = [
        # Базовые
        ('Standard', 10),
        ('Deluxe', 20),
        ('Ultimate', 30),
        ("Collector's", 40),
        ('Limited', 50),
        ('Steelbook', 60),
        ('Signature', 70),
        ('Day One', 80),
        ('Gold', 90),
        ('Anniversary', 100),
        ('Special', 110),
        ('Premium', 120),
        ('K.O.', 130),
        ('Classic', 140),
        ('Definitive', 150),
        ('Complete', 160),
        ('Enhanced', 170),
        ('Extended', 180),
        ('Exclusive', 190),
        # Составные
        ('Slip Case Gold', 200),
        ('France Exclusive', 210),
        ('Картонный бокс', 220),
        ('Ultimate 30th Anniversary', 230),
        ('Essence of Art', 240),
        ('Mirror', 250),
        ("Collector's K.O.", 260),
        ('Vengeance', 270),
        ('Steelbook Premium', 280),
        ('Ultimate Steelbook', 290),
        ('Legendary Edition', 300),
        ('Legendary Edition Steelbook', 310),
        ('Anniversary Collection', 320),
        ('Collection', 330),
        # GOTY / Game of the Year — оба (разные написания в данных)
        ('GOTY', 340),
        ('Game of the Year', 350),
        # Готовые фразы (встречаются в данных)
        ('First Year', 360),
        ('New Year', 370),
        ('Three Fairies', 380),
        ('Three Fairies Edition', 390),
        ('Survivor Steelbook', 400),
        ('Survivor', 410),
        ('Legendary', 420),
        # Одиночные в скобках (бывшие SINGLE_WORD_EDITION_MAP)
        ('Platinum', 430),
        ('Black', 440),
        ('Journey', 470)  
        # ('Tails', 450),
        # ('Knuckles', 460),
    ]
    for name, sort in editions:
        conn.execute(
            "INSERT OR IGNORE INTO editionTypes (editionName, sortOrder) VALUES (?, ?)",
            (name, sort)
        )


def seed_publishers(conn):
    """Издатели."""
    publishers = [
        'Nintendo', 'Sega', 'Sony Interactive Entertainment', 'Microsoft / Xbox Game Studios',
        'Electronic Arts', 'Ubisoft', 'Activision Blizzard', 'Bandai Namco', 'Capcom',
        'Square Enix', 'Konami', 'Take-Two Interactive', 'CD Projekt', 'Paradox Interactive',
        '1C', 'Limited Run Games', 'Strictly Limited Games', 'Merge Games', 'NIS America',
        'Idea Factory International', 'Special Reserve Games', 'Super Rare Games',
        'Eastasiasoft', 'Play-Asia', 'Red Art Games', "Pix'n Love",
        'Signature Edition Games', 'Fangamer', 'iam8bit', 'Retro-Bit'
    ]
    for name in publishers:
        conn.execute(
            "INSERT OR IGNORE INTO publishers (publisherName) VALUES (?)",
            (name,)
        )


def seed_statuses(conn):
    """Статусы заказов (продажа + закупка)."""
    statuses = [
        ('paid', 'sale', 10),
        ('shipped', 'sale', 20),
        ('received', 'sale', 30),
        ('refusal', 'sale', 40),
        ('cancelled', 'sale', 50),
        ('at_carrier', 'purchase', 60),
        ('shipped', 'purchase', 70),
        ('customs', 'purchase', 80),
        ('out_for_delivery', 'purchase', 90),
        ('received', 'purchase', 100),
    ]
    for name, stype, sort in statuses:
        conn.execute(
            "INSERT OR IGNORE INTO statuses (statusName, statusType, sortOrder) VALUES (?, ?, ?)",
            (name, stype, sort)
        )


def seed_mediaTypes(conn):
    """Типы носителей."""
    media = [
        ('physical', 10), ('digital', 20), ('cartridge', 30),
        ('disc', 40), ('code_in_a_box', 50), ('download_code', 60),
    ]
    for name, sort in media:
        conn.execute(
            "INSERT OR IGNORE INTO mediaTypes (mediaTypeName, sortOrder) VALUES (?, ?)",
            (name, sort)
        )


def seed_ageGroups(conn):
    """Возрастные группы (по умолчанию 25-34 — id=2)."""
    age_groups = [
        (1, '18-24', 10),
        (2, '25-34', 20),
        (3, '35-44', 30),
        (4, '45-54', 40),
        (5, '55+', 50),
    ]
    for gid, name, sort in age_groups:
        conn.execute(
            "INSERT OR IGNORE INTO ageGroups (ageGroupId, ageGroupName, sortOrder) VALUES (?, ?, ?)",
            (gid, name, sort)
        )


def seed_adjustmentTypes(conn):
    """Типы корректировок выплат."""
    types = [
        ('order_amount', 'Сумма заказа', 10),
        ('commission', 'Комиссия', 20),
        ('refund', 'Возврат покупателю', 30),
        ('lost_in_delivery', 'Компенсация за потерю при доставке', 40),
        ('lost_in_return', 'Компенсация за потерю при возврате', 50),
        ('commission_correction', 'Корректировка комиссии', 60),
        ('other', 'Прочее', 70),
    ]
    for code, name, sort in types:
        conn.execute(
            "INSERT OR IGNORE INTO adjustmentTypes (code, name, sortOrder) VALUES (?, ?, ?)",
            (code, name, sort)
        )


def seed_warehouses(conn):
    """Склады (Виталий id=1, Вениамин id=2 — явно)."""
    warehouses = [
        (1, 'warehouse1', 'Виталий', 1, 10),
        (2, 'warehouse2', 'Вениамин', 1, 20),
    ]
    for wid, code, name, currency_id, sort in warehouses:
        conn.execute(
            "INSERT OR IGNORE INTO warehouses (warehouseId, code, name, defaultCurrencyId, sortOrder) VALUES (?, ?, ?, ?, ?)",
            (wid, code, name, currency_id, sort)
        )


def seed_marketplaces(conn):
    """Площадки продажи (ozon, avito, ym, wb, manual)."""
    marketplaces = [
        ('ozon', 'OZON', 'https://www.ozon.ru', 'RU', 1, 0.45, 1, 10),
        ('avito', 'Avito', 'https://www.avito.ru', 'RU', 1, 0.05, 1, 20),
        ('ym', 'Яндекс.Маркет', 'https://market.yandex.ru', 'RU', 1, 0.20, 1, 30),
        ('wb', 'Wildberries', 'https://www.wildberries.ru', 'RU', 1, 0.25, 1, 40),
        ('manual', 'Ручная продажа (Others)', None, None, 1, 0.00, 0, 50),
    ]
    for code, name, url, country, currency_id, commission, has_api, sort in marketplaces:
        conn.execute(
            """INSERT OR IGNORE INTO marketplaces 
               (code, name, url, countryCode, defaultCurrencyId, defaultCommissionRate, hasApi, sortOrder) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (code, name, url, country, currency_id, commission, has_api, sort)
        )


def seed_purchasePlatforms(conn):
    """Площадки закупки (10)."""
    platforms = [
        ('avito_ru', 'Avito (Россия)', 'https://www.avito.ru', 'RU', 1, 1, 10),
        ('ebay_uk', 'eBay UK', 'https://www.ebay.co.uk', 'GB', 4, 1, 20),
        ('ebay_de', 'eBay DE', 'https://www.ebay.de', 'DE', 3, 1, 30),
        ('ebay_fr', 'eBay FR', 'https://www.ebay.fr', 'FR', 3, 1, 40),
        ('ebay_us', 'eBay US', 'https://www.ebay.com', 'US', 2, 1, 50),
        ('superrare', 'Super Rare Games', 'https://superraregames.com', 'GB', 4, 0, 60),
        ('amazon_uk', 'Amazon UK', 'https://www.amazon.co.uk', 'GB', 4, 1, 70),
        ('redart', 'Red Art Games', 'https://www.redartgames.com', 'FR', 3, 0, 80),
        ('justforgames', 'Shop Just For Games', 'https://www.shop-justforgames.com', 'FR', 3, 0, 90),
        ('vinted_be', 'Vinted BE', 'https://www.vinted.be', 'BE', 3, 0, 100),
    ]
    for code, name, url, country, currency_id, has_api, sort in platforms:
        conn.execute(
            """INSERT OR IGNORE INTO purchasePlatforms 
               (code, name, url, countryCode, defaultCurrencyId, hasApi, sortOrder) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (code, name, url, country, currency_id, has_api, sort)
        )


def seed_stores(conn):
    """Магазины (limited_games, console_games, manual)."""
    stores = [
        ('limited_games', 'LimitedGames', 1, 1, 1, 10),
        ('console_games', 'ConsoleGames', 1, 1, 1, 20),
        ('manual', 'Ручная продажа', 5, 1, 0, 30),
    ]
    for code, name, marketplace_id, warehouse_id, has_api, sort in stores:
        conn.execute(
            """INSERT OR IGNORE INTO stores 
               (code, name, marketplaceId, warehouseId, hasApi, sortOrder) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (code, name, marketplace_id, warehouse_id, has_api, sort)
        )


def seed_buyers(conn):
    """Покупатель по умолчанию (Физлицо id=1)."""
    conn.execute(
        "INSERT OR IGNORE INTO buyers (buyerId, buyerNickname, ageGroupId) VALUES (1, 'Физлицо', 2)"
    )


def main():
    with get_conn() as conn:
        seed_modules(conn)
        seed_currencies(conn)
        seed_regions(conn)
        seed_platforms(conn)
        seed_typeGoods(conn)
        seed_editionTypes(conn)
        seed_publishers(conn)
        seed_statuses(conn)
        seed_mediaTypes(conn)
        seed_ageGroups(conn)
        seed_adjustmentTypes(conn)
        seed_warehouses(conn)
        seed_marketplaces(conn)
        seed_purchasePlatforms(conn)
        seed_stores(conn)
        seed_buyers(conn)
        conn.commit()

    with get_conn() as conn:
        print("\n=== Заполнено ===")
        tables = [
            'modules', 'currencies', 'regions', 'platforms', 'typeGoods',
            'editionTypes', 'publishers', 'statuses', 'mediaTypes', 'ageGroups',
            'adjustmentTypes', 'warehouses', 'marketplaces', 'purchasePlatforms',
            'stores', 'buyers'
        ]
        for t in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t}: {count}")

    print("\n✅ Справочники заполнены (v3.1).")


if __name__ == "__main__":
    main()