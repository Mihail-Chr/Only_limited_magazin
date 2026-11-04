-- =====================================================================
-- Only_limited_magazin
-- Схема базы данных v2 (SQLite)
-- =====================================================================

PRAGMA foreign_keys = ON;

-- =====================================================================
-- 1. СПРАВОЧНИКИ И ПОЛЬЗОВАТЕЛИ
-- =====================================================================

CREATE TABLE IF NOT EXISTS warehouse (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    default_currency TEXT NOT NULL DEFAULT 'RUB',
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS warehouse_currency (
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    currency        TEXT NOT NULL,
    PRIMARY KEY (warehouse_id, currency)
);

CREATE TABLE IF NOT EXISTS store (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    platform        TEXT DEFAULT 'ozon',
    client_id       TEXT,
    api_key         TEXT,
    has_api         INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1,
    api_role        TEXT
);

CREATE TABLE IF NOT EXISTS app_user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    login           TEXT NOT NULL UNIQUE,
    email           TEXT,
    password_hash   TEXT NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS role (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_role (
    user_id         INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    role_id         INTEGER NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS user_warehouse (
    user_id         INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, warehouse_id)
);

CREATE TABLE IF NOT EXISTS user_store (
    user_id         INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    store_id        INTEGER NOT NULL REFERENCES store(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, store_id)
);

-- =====================================================================
-- 2. ТОВАРЫ (v2)
-- =====================================================================

CREATE TABLE IF NOT EXISTS product (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id            TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    baseGameName        TEXT,
    brand               TEXT,
    product_type        TEXT,
    platform            TEXT,
    platform_set        TEXT,                   -- JSON-массив для дублей ["PlayStation 4", "PlayStation 5"]
    edition             TEXT,
    age_rating          TEXT,
    genre               TEXT,
    publisher           TEXT,
    developer           TEXT,
    media_type          TEXT,
    media_count         INTEGER,
    release_year        INTEGER,
    firstReleaseYear    INTEGER,
    firstYearEdition    INTEGER,
    remakeYear          INTEGER,
    language            TEXT,
    view                TEXT,
    modes               TEXT,
    restore             INTEGER DEFAULT 0,
    weight_g            INTEGER,
    width_mm            INTEGER,
    height_mm           INTEGER,
    length_mm           INTEGER,
    photo_main_url      TEXT,
    photo_extra_urls    TEXT,
    photo_filename      TEXT,                   -- имя файла в папке data/images/
    country_of_origin   TEXT,
    package_type        TEXT,
    package_size        TEXT,
    cost_price_synthetic REAL,
    cost_price_real     REAL,
    avg_market_price    REAL,
    avg_market_price_updated_at TEXT,
    regionId            INTEGER REFERENCES regions(regionId),
    is_active           INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_product_offer_id ON product(offer_id);
CREATE INDEX IF NOT EXISTS idx_product_name ON product(name);
CREATE INDEX IF NOT EXISTS idx_product_base_name ON product(baseGameName);
CREATE INDEX IF NOT EXISTS idx_product_type ON product(product_type);
CREATE INDEX IF NOT EXISTS idx_product_platform ON product(platform);
CREATE INDEX IF NOT EXISTS idx_product_is_active ON product(is_active);

CREATE TABLE IF NOT EXISTS listing (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id        INTEGER NOT NULL REFERENCES store(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id),
    sku             TEXT,
    barcode         TEXT,
    price           REAL,
    old_price       REAL,
    vat             TEXT,
    status          TEXT,
    error_text      TEXT,
    defects_text    TEXT,
    commission_rate REAL DEFAULT 0.45,
    payout_amount   REAL,
    UNIQUE (store_id, product_id)
);

-- =====================================================================
-- 3. СКЛАД
-- =====================================================================

CREATE TABLE IF NOT EXISTS stock (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    quantity        INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (warehouse_id, product_id)
);

CREATE TABLE IF NOT EXISTS stock_manual (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    quantity        INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (product_id)
);

CREATE TABLE IF NOT EXISTS stock_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    quantity_delta  INTEGER NOT NULL,
    reason          TEXT,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- 4. ЦЕНЫ И РЫНОК
-- =====================================================================

CREATE TABLE IF NOT EXISTS price_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id      INTEGER NOT NULL REFERENCES listing(id) ON DELETE CASCADE,
    price           REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'RUB',
    old_price       REAL,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS market_offers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    platform        TEXT NOT NULL,
    price           REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'RUB',
    url             TEXT,
    fetched_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- 5. ПОКУПАТЕЛИ И СИНХРОНИЗАЦИЯ
-- =====================================================================

CREATE TABLE IF NOT EXISTS buyer (
    buyerId         INTEGER PRIMARY KEY AUTOINCREMENT,
    buyerNickname   TEXT NOT NULL UNIQUE,
    buyerCity       TEXT,
    buyerAgeGroup   TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sync_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type       TEXT NOT NULL,              -- 'ozon_sales', 'ozon_products'
    date_from       TEXT,
    date_to         TEXT,
    records_count   INTEGER DEFAULT 0,
    synced_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- 6. ЗАКАЗЫ OZON (ИСТОРИЯ ПРОДАЖ)
-- =====================================================================

CREATE TABLE IF NOT EXISTS posting (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    posting_number      TEXT NOT NULL UNIQUE,
    order_id            INTEGER,
    store_id            INTEGER NOT NULL REFERENCES store(id),
    status              TEXT,
    substatus           TEXT,
    created_at          TEXT,
    in_process_at       TEXT,
    shipment_date       TEXT,
    delivering_date     TEXT,
    tracking_number     TEXT,
    raw_json            TEXT,
    source              TEXT NOT NULL DEFAULT 'ozon', -- 'ozon' / 'manual'
    buyer_id            INTEGER REFERENCES buyer(buyerId), -- Ссылка на покупателя
    buyer_nickname      TEXT,                   -- Дублируем для истории, если buyer_id NULL
    is_preorder         INTEGER DEFAULT 0,      -- 1 = товар под заказ (не было на складе)
    fetched_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS posting_item (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    posting_id          INTEGER NOT NULL REFERENCES posting(id) ON DELETE CASCADE,
    product_id          INTEGER REFERENCES product(id),
    offer_id            TEXT,
    sku                 TEXT,
    name                TEXT,
    quantity            INTEGER NOT NULL DEFAULT 0,
    price               REAL,
    currency            TEXT,
    cost_price_at_sale  REAL
);

-- =====================================================================
-- 7. ИНДЕКСЫ
-- =====================================================================

CREATE INDEX IF NOT EXISTS idx_listing_store ON listing(store_id);
CREATE INDEX IF NOT EXISTS idx_listing_sku ON listing(sku);
CREATE INDEX IF NOT EXISTS idx_listing_barcode ON listing(barcode);

CREATE INDEX IF NOT EXISTS idx_stock_warehouse ON stock(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_product ON stock(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_manual_product ON stock_manual(product_id);

CREATE INDEX IF NOT EXISTS idx_price_history_listing ON price_history(listing_id);
CREATE INDEX IF NOT EXISTS idx_stock_history_product ON stock_history(product_id);
CREATE INDEX IF NOT EXISTS idx_market_offers_product ON market_offers(product_id);

CREATE INDEX IF NOT EXISTS idx_posting_status ON posting(status);
CREATE INDEX IF NOT EXISTS idx_posting_created ON posting(created_at);
CREATE INDEX IF NOT EXISTS idx_posting_item_offer ON posting_item(offer_id);
CREATE INDEX IF NOT EXISTS idx_posting_item_sku ON posting_item(sku);

-- =====================================================================
-- 8. СПРАВОЧНИКИ
-- =====================================================================

CREATE TABLE IF NOT EXISTS "typeGoods" (
    "typeGoodId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "typeGoodName" TEXT NOT NULL UNIQUE,
    "sortOrder" INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS platforms (
    "platformId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "platformName" TEXT NOT NULL,
    "platformVersion" TEXT NOT NULL,
    "revision" TEXT,                            -- Например, "X", "S", "Pro", "OLED"
    "is_portable" INTEGER DEFAULT 0,            -- 1 для GB, GBA, NDS
    "sortOrder" INTEGER DEFAULT 100,
    UNIQUE ("platformName", "platformVersion")
);

CREATE TABLE IF NOT EXISTS "editionTypes" (
    "editionId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "editionName" TEXT NOT NULL UNIQUE,
    "sortOrder" INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS regions (
    "regionId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "regionCode" TEXT NOT NULL UNIQUE,
    "sortOrder" INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS publishers (
    "publisherId" INTEGER PRIMARY KEY AUTOINCREMENT,
    "publisherName" TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS "exchangeRates" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "currency" TEXT NOT NULL UNIQUE,
    "rate_to_rub" REAL NOT NULL
);

-- =====================================================================
-- ГОТОВО. Все таблицы и индексы созданы (v2).
-- =====================================================================