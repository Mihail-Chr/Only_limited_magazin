-- =====================================================================
-- Only_limited_magazin
-- Схема базы данных для локальной работы (SQLite)
-- Все таблицы создаются с IF NOT EXISTS, чтобы не удалять данные
-- =====================================================================

PRAGMA foreign_keys = ON;

-- =====================================================================
-- 1. СПРАВОЧНИКИ И ПОЛЬЗОВАТЕЛИ
-- =====================================================================

-- Склады (основной, архив, ремонт)
CREATE TABLE IF NOT EXISTS warehouse (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    default_currency TEXT NOT NULL DEFAULT 'RUB',
    is_active       INTEGER NOT NULL DEFAULT 1
);

-- Валюты, поддерживаемые складом (M2M)
CREATE TABLE IF NOT EXISTS warehouse_currency (
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    currency        TEXT NOT NULL,
    PRIMARY KEY (warehouse_id, currency)
);

-- Магазины (маркетплейсы)
CREATE TABLE IF NOT EXISTS store (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    client_id       TEXT,
    api_key         TEXT,
    has_api         INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1,
    api_role        TEXT
);

-- Пользователи
CREATE TABLE IF NOT EXISTS app_user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    login           TEXT NOT NULL UNIQUE,
    email           TEXT,
    password_hash   TEXT NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Роли (admin, warehouse_keeper, seller, auditor)
CREATE TABLE IF NOT EXISTS role (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL
);

-- Связь пользователей и ролей (M2M)
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

-- =====================================================================
-- 2. ТОВАРЫ
-- =====================================================================

-- Карточки товаров (SKU)
CREATE TABLE IF NOT EXISTS product (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id            TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    baseGameName        TEXT,                   -- базовое название игры (без издания/платформы)
    brand               TEXT,
    product_type        TEXT,                   -- 'game', 'bundle', 'steelbook' и т.д.
    platform            TEXT,                   -- 'PlayStation 4', 'Nintendo Switch 1'
    edition             TEXT,                   -- 'Deluxe', 'Ultimate', 'Standard'
    age_rating          TEXT,                   -- '18+', '12+'
    genre               TEXT,                   -- 'Action', 'Horror'
    publisher           TEXT,                   -- издатель
    developer           TEXT,                   -- разработчик
    media_type          TEXT,                   -- 'Blu-ray', 'Cartridge'
    media_count         INTEGER,                -- количество носителей
    release_year        INTEGER,                -- год релиза
    firstReleaseYear    INTEGER,                -- год первого релиза (для аналитики)
    firstYearEdition    INTEGER,                -- год выпуска этой версии
    remakeYear          INTEGER,                -- год ремейка (если есть)
    language            TEXT,                   -- языки (JSON-строка)
    view                TEXT,                   -- вид (для аксессуаров)
    modes               TEXT,                   -- режимы игры
    weight_g            INTEGER,
    width_mm            INTEGER,
    height_mm           INTEGER,
    length_mm           INTEGER,
    photo_main_url      TEXT,
    photo_extra_urls    TEXT,
    country_of_origin   TEXT,
    package_type        TEXT,
    package_size        TEXT,
    cost_price_synthetic REAL,                  -- искусственная себестоимость (для маржи)
    cost_price_real     REAL,                   -- реальная себестоимость (если известна)
    avg_market_price    REAL,                   -- средняя цена на рынке (для агента закупок)
    avg_market_price_updated_at TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Индексы для поиска товаров
CREATE INDEX IF NOT EXISTS idx_product_base_name ON product(baseGameName);
CREATE INDEX IF NOT EXISTS idx_product_type ON product(product_type);
CREATE INDEX IF NOT EXISTS idx_product_platform ON product(platform);

-- Публикация товара в конкретном магазине (листинг)
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
    status          TEXT,                       -- 'draft', 'active', 'error'
    error_text      TEXT,
    defects_text    TEXT,
    commission_rate REAL DEFAULT 0.45,          -- комиссия маркетплейса
    payout_amount   REAL,                       -- сумма на руки
    UNIQUE (store_id, product_id)
);

-- =====================================================================
-- 3. СКЛАД
-- =====================================================================

-- Остатки на складе (автоматический учёт по закупкам/продажам)
CREATE TABLE IF NOT EXISTS stock (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouse(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    quantity        INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (warehouse_id, product_id)
);

-- Ручной физический остаток (инвентаризация, вводит кладовщик)
CREATE TABLE IF NOT EXISTS stock_manual (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    quantity        INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (product_id)
);

-- История изменения остатков (для аудита)
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

-- История изменения цен (для аналитики)
CREATE TABLE IF NOT EXISTS price_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id      INTEGER NOT NULL REFERENCES listing(id) ON DELETE CASCADE,
    price           REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'RUB',
    old_price       REAL,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Предложения на рынке (для агента закупок)
CREATE TABLE IF NOT EXISTS market_offers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    platform        TEXT NOT NULL,              -- 'ozon', 'wb', 'avito', 'ebay'
    price           REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'RUB',
    url             TEXT,
    fetched_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- 5. ЗАКАЗЫ OZON (история продаж)
-- =====================================================================

-- Отправления (заказы)
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

-- Позиции отправлений
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
    cost_price_at_sale  REAL                    -- себестоимость на момент продажи
);

-- =====================================================================
-- 6. ИНДЕКСЫ ДЛЯ УСКОРЕНИЯ ЗАПРОСОВ
-- =====================================================================

-- Индексы для листингов
CREATE INDEX IF NOT EXISTS idx_listing_store ON listing(store_id);
CREATE INDEX IF NOT EXISTS idx_listing_sku ON listing(sku);
CREATE INDEX IF NOT EXISTS idx_listing_barcode ON listing(barcode);

-- Индексы для склада
CREATE INDEX IF NOT EXISTS idx_stock_warehouse ON stock(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_product ON stock(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_manual_product ON stock_manual(product_id);

-- Индексы для истории
CREATE INDEX IF NOT EXISTS idx_price_history_listing ON price_history(listing_id);
CREATE INDEX IF NOT EXISTS idx_stock_history_product ON stock_history(product_id);
CREATE INDEX IF NOT EXISTS idx_market_offers_product ON market_offers(product_id);

-- Индексы для заказов
CREATE INDEX IF NOT EXISTS idx_posting_status ON posting(status);
CREATE INDEX IF NOT EXISTS idx_posting_created ON posting(created_at);
CREATE INDEX IF NOT EXISTS idx_posting_item_offer ON posting_item(offer_id);
CREATE INDEX IF NOT EXISTS idx_posting_item_sku ON posting_item(sku);

-- =====================================================================
-- 7. СПРАВОЧНИКИ (для выпадающих списков)
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
-- ГОТОВО. Все таблицы и индексы созданы.
-- =====================================================================