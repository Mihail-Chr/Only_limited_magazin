PRAGMA foreign_keys = ON;

-- ---------- Склады ----------
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

-- ---------- Магазины ----------
CREATE TABLE IF NOT EXISTS store (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    client_id       TEXT,
    api_key         TEXT,             -- хранится локально, не выгружать в git
    has_api         INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1,
    api_role        TEXT
);

-- ---------- Пользователи и роли ----------
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
    code            TEXT NOT NULL UNIQUE,   -- admin | warehouse_keeper | seller | auditor
    name            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_role (
    user_id         INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    role_id         INTEGER NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Кладовщик может быть на нескольких складах
CREATE TABLE IF NOT EXISTS user_warehouse (
    user_id         INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, warehouse_id)
);

-- Продавец привязан к магазину
CREATE TABLE IF NOT EXISTS user_store (
    user_id         INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    store_id        INTEGER NOT NULL REFERENCES store(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, store_id)
);

-- ---------- Товары ----------
CREATE TABLE IF NOT EXISTS product (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id        TEXT NOT NULL UNIQUE,         -- ваш артикул
    name            TEXT NOT NULL,
    brand           TEXT,
    product_type    TEXT,                         -- «Видеоигра»
    platform        TEXT,
    edition         TEXT,
    age_rating      TEXT,
    genre           TEXT,
    publisher       TEXT,
    developer       TEXT,
    media_type      TEXT,
    media_count     INTEGER,
    release_year    INTEGER,
    language        TEXT,
    view            TEXT,
    modes           TEXT,
    weight_g        INTEGER,
    width_mm        INTEGER,
    height_mm       INTEGER,
    length_mm       INTEGER,
    photo_main_url  TEXT,
    photo_extra_urls TEXT,                        -- список через \n
    country_of_origin TEXT,
    package_type    TEXT,
    package_size    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Публикация товара в конкретном магазине (листинг)
CREATE TABLE IF NOT EXISTS listing (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id        INTEGER NOT NULL REFERENCES store(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id),
    sku             TEXT,                         -- Ozon SKU, если уже есть
    barcode         TEXT,
    price           REAL,
    old_price       REAL,
    vat             TEXT,
    status          TEXT,                         -- draft | active | error
    error_text      TEXT,
    defects_text    TEXT,
    UNIQUE (store_id, product_id)
);

-- Остаток — на складе, не на магазине
CREATE TABLE IF NOT EXISTS stock (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    quantity        INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (warehouse_id, product_id)
);

-- История цен (мультивалютность)
CREATE TABLE IF NOT EXISTS price_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id      INTEGER NOT NULL REFERENCES listing(id) ON DELETE CASCADE,
    price           REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'RUB',
    old_price       REAL,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- История остатков
CREATE TABLE IF NOT EXISTS stock_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    quantity_delta  INTEGER NOT NULL,
    reason          TEXT,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_listing_store       ON listing(store_id);
CREATE INDEX IF NOT EXISTS idx_listing_sku         ON listing(sku);
CREATE INDEX IF NOT EXISTS idx_listing_barcode     ON listing(barcode);
CREATE INDEX IF NOT EXISTS idx_stock_warehouse     ON stock(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_product       ON stock(product_id);

-- Заготовки для будущей аналитики закупок и цен
ALTER TABLE product ADD COLUMN cost_price_synthetic REAL;
ALTER TABLE product ADD COLUMN cost_price_real REAL;
ALTER TABLE product ADD COLUMN avg_market_price REAL;
ALTER TABLE product ADD COLUMN avg_market_price_updated_at TEXT;

CREATE TABLE IF NOT EXISTS market_offers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    platform        TEXT NOT NULL,   -- 'ozon', 'wb', 'avito', 'ali', etc.
    price           REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'RUB',
    url             TEXT,
    fetched_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_market_offers_product ON market_offers(product_id);

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
    currency            TEXT
);

CREATE INDEX IF NOT EXISTS idx_posting_status ON posting(status);
CREATE INDEX IF NOT EXISTS idx_posting_created ON posting(created_at);
CREATE INDEX IF NOT EXISTS idx_posting_item_offer ON posting_item(offer_id);
CREATE INDEX IF NOT EXISTS idx_posting_item_sku ON posting_item(sku);