-- =====================================================================
-- Only_limited_magazin
-- Схема базы данных v3.1 (SQLite)
-- =====================================================================
-- Принципы:
--   - Таблицы: множественное число (products, buyers, salesOrders)
--   - Поля: единственное число, camelCase (productId, buyerId)
--   - Нормализация: только ID, без строк (JOIN при чтении)
--   - Аудит: createdAt, updatedAt (для сущностей действия)
--   - Feature flags: таблица modules (isEnabled)
--   - Однозначность: code + name в UI (ISO + название)
--   - UNIQUE: на все code и name (кроме products.name, products.baseGameName)
-- =====================================================================

PRAGMA foreign_keys = ON;

-- =====================================================================
-- ЧАСТЬ 1: ФУНДАМЕНТ (справочники)
-- =====================================================================

-- ---------------------------------------------------------------------
-- modules — Модули приложения (feature flags)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS modules (
    moduleName      TEXT PRIMARY KEY,           -- 'purchase', 'sale', 'monitoring', 'inventory', 'ozon_sync', 'manual_sale'
    isEnabled       INTEGER NOT NULL DEFAULT 0, -- 0 = выключен, 1 = включён (DEFAULT 0 — новый модуль выключен)
    sortOrder       INTEGER DEFAULT 100,
    description     TEXT,
    versionAdded    TEXT                        -- в какой версии появился (опц.)
);

-- ---------------------------------------------------------------------
-- currencies — Валюты
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS currencies (
    currencyId      INTEGER PRIMARY KEY AUTOINCREMENT,
    currencyCode    TEXT NOT NULL UNIQUE,       -- ISO 4217: 'USD', 'CAD', 'EUR', 'RUB', 'GBP', 'JPY'
    currencyName    TEXT NOT NULL UNIQUE,       -- полное: 'Доллар США', 'Канадский доллар', 'Евро'
    currencySymbol  TEXT,                       -- '₽', '$', '€', '£'
    isCrypto        INTEGER NOT NULL DEFAULT 0,
    isActive        INTEGER NOT NULL DEFAULT 1,
    sortOrder       INTEGER DEFAULT 100
);

-- ---------------------------------------------------------------------
-- regions — Регионы выпуска
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regions (
    regionId        INTEGER PRIMARY KEY AUTOINCREMENT,
    regionCode      TEXT NOT NULL UNIQUE,       -- 'US', 'EU', 'RU', 'JP', 'Asia', 'CN', 'AUS', 'SA', 'KR'
    regionName      TEXT NOT NULL UNIQUE,       -- полное: 'США', 'Европа', 'Европа (расширенная)'
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------------
-- platforms — Платформы
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS platforms (
    platformId      INTEGER PRIMARY KEY AUTOINCREMENT,
    platformName    TEXT NOT NULL,              -- 'PlayStation', 'Nintendo Switch'
    platformVersion TEXT NOT NULL,              -- '4', '5', '1', '2', '4/5'
    revision        TEXT,                       -- 'Slim', 'Pro', 'OLED' (опц.)
    isPortable      INTEGER NOT NULL DEFAULT 0, -- 1 для GB, GBA, NDS
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1,
    UNIQUE (platformName, platformVersion)
);

-- ---------------------------------------------------------------------
-- typeGoods — Типы товаров
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS typeGoods (
    typeGoodId      INTEGER PRIMARY KEY AUTOINCREMENT,
    typeGoodName    TEXT NOT NULL UNIQUE,       -- 'game', 'bundle', 'steelbook', 'gamepad', ...
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------------
-- editionTypes — Типы изданий
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS editionTypes (
    editionId       INTEGER PRIMARY KEY AUTOINCREMENT,
    editionName     TEXT NOT NULL UNIQUE,       -- 'Standard', 'Deluxe', "Collector's", ...
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------------
-- publishers — Издатели
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS publishers (
    publisherId     INTEGER PRIMARY KEY AUTOINCREMENT,
    publisherName   TEXT NOT NULL UNIQUE,       -- 'Nintendo', 'Sega', 'Limited Run Games', ...
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------------
-- statuses — Статусы заказов
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS statuses (
    statusId        INTEGER PRIMARY KEY AUTOINCREMENT,
    statusName      TEXT NOT NULL,              -- 'paid', 'shipped', 'received', 'refusal', ...
    statusType      TEXT NOT NULL CHECK (statusType IN ('purchase', 'sale')),
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1,
    UNIQUE (statusName, statusType)
);

-- ---------------------------------------------------------------------
-- mediaTypes — Типы носителей
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mediaTypes (
    mediaTypeId     INTEGER PRIMARY KEY AUTOINCREMENT,
    mediaTypeName   TEXT NOT NULL UNIQUE,       -- 'physical', 'digital', 'cartridge', 'disc', ...
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------------
-- ageGroups — Возрастные группы покупателей
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ageGroups (
    ageGroupId      INTEGER PRIMARY KEY AUTOINCREMENT,
    ageGroupName    TEXT NOT NULL UNIQUE,       -- '18-24', '25-34', '35-44', '45-54', '55+'
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------------
-- adjustmentTypes — Типы корректировок выплат
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS adjustmentTypes (
    adjustmentTypeId INTEGER PRIMARY KEY AUTOINCREMENT,
    code             TEXT NOT NULL UNIQUE,      -- 'order_amount', 'commission', 'refund', ...
    name             TEXT NOT NULL UNIQUE,      -- 'Сумма заказа', 'Комиссия'
    sortOrder        INTEGER DEFAULT 100,
    isActive         INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------------
-- exchangeRates — Курсы валют (история по датам)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exchangeRates (
    exchangeRateId  INTEGER PRIMARY KEY AUTOINCREMENT,
    rateDate        TEXT NOT NULL,              -- '2026-11-05'
    currencyId      INTEGER NOT NULL REFERENCES currencies(currencyId),
    rateToRub       REAL NOT NULL,              -- 1 USD = 90.50 RUB
    source          TEXT DEFAULT 'CBR',         -- 'CBR', 'manual'
    createdAt       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (rateDate, currencyId)
);

-- =====================================================================
-- ЧАСТЬ 2: ПЛОЩАДКИ И СКЛАДЫ
-- =====================================================================

-- ---------------------------------------------------------------------
-- purchasePlatforms — Площадки закупки
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchasePlatforms (
    purchasePlatformId INTEGER PRIMARY KEY AUTOINCREMENT,
    code               TEXT NOT NULL UNIQUE,    -- 'ebay_uk', 'avito_ru', 'amazon_uk'
    name               TEXT NOT NULL UNIQUE,    -- 'eBay UK', 'Avito (Россия)'
    url                TEXT,                    -- 'https://www.ebay.co.uk'
    countryCode        TEXT,                    -- 'GB', 'RU', 'US' (ISO 3166-1 alpha-2)
    defaultCurrencyId  INTEGER REFERENCES currencies(currencyId),
    hasApi             INTEGER NOT NULL DEFAULT 0,
    isActive           INTEGER NOT NULL DEFAULT 1,
    sortOrder          INTEGER DEFAULT 100
);

-- ---------------------------------------------------------------------
-- marketplaces — Площадки продажи
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketplaces (
    marketplaceId         INTEGER PRIMARY KEY AUTOINCREMENT,
    code                  TEXT NOT NULL UNIQUE, -- 'ozon', 'avito', 'ym', 'wb', 'manual'
    name                  TEXT NOT NULL UNIQUE, -- 'OZON', 'Avito', 'Яндекс.Маркет'
    url                   TEXT,                 -- 'https://www.ozon.ru'
    countryCode           TEXT,                 -- 'RU'
    defaultCurrencyId     INTEGER REFERENCES currencies(currencyId),
    defaultCommissionRate REAL,                 -- 0.45 для OZON
    hasApi                INTEGER NOT NULL DEFAULT 0,
    isActive              INTEGER NOT NULL DEFAULT 1,
    sortOrder             INTEGER DEFAULT 100
);

-- ---------------------------------------------------------------------
-- warehouses — Склады
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouses (
    warehouseId       INTEGER PRIMARY KEY AUTOINCREMENT,
    code              TEXT NOT NULL UNIQUE,     -- 'warehouse1', 'warehouse2'
    name              TEXT NOT NULL UNIQUE,     -- 'Виталий', 'Вениамин'
    defaultCurrencyId INTEGER REFERENCES currencies(currencyId),
    sortOrder         INTEGER DEFAULT 100,
    isActive          INTEGER NOT NULL DEFAULT 1,
    createdAt         TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- stores — Наши магазины на площадках
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stores (
    storeId       INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT NOT NULL UNIQUE,         -- 'limited_games', 'console_games', 'manual'
    name          TEXT NOT NULL UNIQUE,         -- 'LimitedGames', 'ConsoleGames'
    marketplaceId INTEGER NOT NULL REFERENCES marketplaces(marketplaceId),
    warehouseId   INTEGER REFERENCES warehouses(warehouseId),  -- склад по умолчанию (FBS)
    hasApi        INTEGER NOT NULL DEFAULT 0,
    isActive      INTEGER NOT NULL DEFAULT 1,
    sortOrder     INTEGER DEFAULT 100
);

-- =====================================================================
-- ЧАСТЬ 3: ТОВАРЫ
-- =====================================================================

-- ---------------------------------------------------------------------
-- products — Товары
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    productId               INTEGER PRIMARY KEY AUTOINCREMENT,
    offerId                 TEXT,                           -- артикул площадки (без UNIQUE)
    name                    TEXT,                           -- название в карточке площадки (из API)
    baseGameName            TEXT,                           -- базовое название игры (после парсинга)
    description             TEXT,                           -- свободное описание
    typeGoodId              INTEGER REFERENCES typeGoods(typeGoodId),
    platformId              INTEGER REFERENCES platforms(platformId),
    editionId               INTEGER REFERENCES editionTypes(editionId),
    publisherId             INTEGER REFERENCES publishers(publisherId),
    mediaTypeId             INTEGER REFERENCES mediaTypes(mediaTypeId),
    regionId                INTEGER REFERENCES regions(regionId),
    releaseYear             INTEGER,
    restore                 INTEGER NOT NULL DEFAULT 0,     -- лицензия (0/1)
    weightG                 INTEGER,                        -- вес (г)
    widthMm                 INTEGER,                        -- ширина (мм)
    heightMm                INTEGER,                        -- высота (мм)
    lengthMm                INTEGER,                        -- длина (мм)
    photoFilename           TEXT,                           -- JSON-массив имён файлов
    cost                    REAL,                           -- себестоимость за 1 шт (в валюте закупки)
    costCurrencyId          INTEGER REFERENCES currencies(currencyId),
    avgSellCost             REAL,                           -- средняя рыночная цена (RUB)
    avgSellCostUpdatedAt    TEXT,                           -- когда обновлено
    avgSellCostSamples      INTEGER,                        -- сколько образцов
    avgSellCostBreakdown    TEXT,                           -- JSON (mock, для «конструктора»)
    isActive                INTEGER NOT NULL DEFAULT 1,
    createdAt               TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt               TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_products_offerId ON products(offerId);
CREATE INDEX IF NOT EXISTS idx_products_baseGameName ON products(baseGameName);
CREATE INDEX IF NOT EXISTS idx_products_platformId ON products(platformId);
CREATE INDEX IF NOT EXISTS idx_products_typeGoodId ON products(typeGoodId);
CREATE INDEX IF NOT EXISTS idx_products_isActive ON products(isActive);

-- ---------------------------------------------------------------------
-- listings — Листинги (привязка товара к магазину)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS listings (
    listingId       INTEGER PRIMARY KEY AUTOINCREMENT,
    storeId         INTEGER NOT NULL REFERENCES stores(storeId) ON DELETE CASCADE,
    productId       INTEGER NOT NULL REFERENCES products(productId) ON DELETE CASCADE,
    sku             TEXT,                           -- SKU на площадке
    brand           TEXT,                           -- бренд (из API)
    price           REAL,                           -- цена
    priceAPI        REAL,                           -- старая цена из API (old_price)
    status          TEXT DEFAULT 'draft',           -- 'draft', 'active', 'archived'
    errorText       TEXT,                           -- ошибка (из API)
    defectsText     TEXT,                           -- дефекты (из API)
    commissionRate  REAL,                           -- комиссия
    payoutAmount    REAL,                           -- сумма выплаты (из API)
    UNIQUE (storeId, productId)
);

CREATE INDEX IF NOT EXISTS idx_listings_storeId ON listings(storeId);
CREATE INDEX IF NOT EXISTS idx_listings_productId ON listings(productId);
CREATE INDEX IF NOT EXISTS idx_listings_sku ON listings(sku);

-- ---------------------------------------------------------------------
-- productGenres — Жанры товаров (M2M)
-- ---------------------------------------------------------------------
-- Пока не используется (0 записей). Таблица есть, наполнение — позже.
CREATE TABLE IF NOT EXISTS productGenres (
    productId   INTEGER NOT NULL REFERENCES products(productId) ON DELETE CASCADE,
    genreId     INTEGER NOT NULL,               -- ссылка на genres (таблица будет позже)
    PRIMARY KEY (productId, genreId)
);

-- ---------------------------------------------------------------------
-- productLanguages — Языки товаров (M2M)
-- ---------------------------------------------------------------------
-- Пока не используется (0 записей). Таблица есть, наполнение — позже.
CREATE TABLE IF NOT EXISTS productLanguages (
    productId   INTEGER NOT NULL REFERENCES products(productId) ON DELETE CASCADE,
    languageId  INTEGER NOT NULL,               -- ссылка на languages (таблица будет позже)
    PRIMARY KEY (productId, languageId)
);

-- ---------------------------------------------------------------------
-- bundleItems — Состав сборника (M2M)
-- ---------------------------------------------------------------------
-- Пока не используется (0 записей). Таблица есть, наполнение — позже.
CREATE TABLE IF NOT EXISTS bundleItems (
    bundleGoodId    INTEGER NOT NULL REFERENCES products(productId) ON DELETE CASCADE,
    includedGoodId  INTEGER NOT NULL REFERENCES products(productId) ON DELETE RESTRICT,
    quantity        SMALLINT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    PRIMARY KEY (bundleGoodId, includedGoodId)
);

-- =====================================================================
-- ЧАСТЬ 4: СКЛАД И ДЕЙСТВИЯ
-- =====================================================================

-- ---------------------------------------------------------------------
-- stocks — Остатки на складах
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stocks (
    stockId         INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouseId     INTEGER NOT NULL REFERENCES warehouses(warehouseId),
    productId       INTEGER NOT NULL REFERENCES products(productId),
    quantity        INTEGER NOT NULL DEFAULT 0,     -- физическое количество
    countOfRepair   INTEGER NOT NULL DEFAULT 0,     -- в предпродажной подготовке
    createdAt       TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (warehouseId, productId)
);

CREATE INDEX IF NOT EXISTS idx_stocks_warehouseId ON stocks(warehouseId);
CREATE INDEX IF NOT EXISTS idx_stocks_productId ON stocks(productId);

-- ---------------------------------------------------------------------
-- stockHistory — История изменений остатков (аудит)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stockHistory (
    historyId       INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouseId     INTEGER NOT NULL REFERENCES warehouses(warehouseId),
    productId       INTEGER NOT NULL REFERENCES products(productId),
    quantityDelta   INTEGER NOT NULL,               -- изменение (+/-)
    reasonId        INTEGER REFERENCES returnReasons(reasonId),
    sourceType      TEXT,                           -- 'purchaseOrder', 'salesOrder', 'manual'
    sourceId        INTEGER,                        -- ID источника
    createdAt       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_stockHistory_productId ON stockHistory(productId);
CREATE INDEX IF NOT EXISTS idx_stockHistory_warehouseId ON stockHistory(warehouseId);

-- ---------------------------------------------------------------------
-- returnReasons — Справочник причин возвратов/списаний
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS returnReasons (
    reasonId        INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,           -- 'defect_on_receipt', 'lost_in_transit', ...
    name            TEXT NOT NULL UNIQUE,           -- 'Брак при приёмке', 'Потеря в пути'
    context         TEXT NOT NULL CHECK (context IN ('purchase', 'sale', 'both')),
    sortOrder       INTEGER DEFAULT 100,
    isActive        INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------------
-- stockWriteOffs — Списания (товар не подлежит восстановлению)
-- ---------------------------------------------------------------------
-- Структура есть. Логика (обработка) — позже (после MVP).
CREATE TABLE IF NOT EXISTS stockWriteOffs (
    writeOffId      INTEGER PRIMARY KEY AUTOINCREMENT,
    productId       INTEGER NOT NULL REFERENCES products(productId),
    warehouseId     INTEGER NOT NULL REFERENCES warehouses(warehouseId),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    reasonId        INTEGER REFERENCES returnReasons(reasonId),
    sourceType      TEXT,                           -- 'purchaseReturn', 'salesReturn', 'manual'
    sourceId        INTEGER,
    writeOffDate    TEXT NOT NULL,
    notes           TEXT,
    createdAt       TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_stockWriteOffs_productId ON stockWriteOffs(productId);
CREATE INDEX IF NOT EXISTS idx_stockWriteOffs_writeOffDate ON stockWriteOffs(writeOffDate);

-- ---------------------------------------------------------------------
-- salesReturns — Возвраты продажи (товар вернулся)
-- ---------------------------------------------------------------------
-- Структура есть. Логика (обработка) — позже (после MVP).
CREATE TABLE IF NOT EXISTS salesReturns (
    returnId        INTEGER PRIMARY KEY AUTOINCREMENT,
    salesOrderId    INTEGER REFERENCES salesOrders(salesOrderId),
    productId       INTEGER NOT NULL REFERENCES products(productId),
    warehouseId     INTEGER NOT NULL REFERENCES warehouses(warehouseId),  -- NOT NULL (товар вернулся)
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    reasonId        INTEGER REFERENCES returnReasons(reasonId),
    returnDate      TEXT NOT NULL,
    refundAmount    REAL CHECK (refundAmount >= 0),
    notes           TEXT,
    createdAt       TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- purchaseReturns — Возвраты/потери покупки
-- ---------------------------------------------------------------------
-- Структура есть. Логика (обработка) — позже (после MVP).
CREATE TABLE IF NOT EXISTS purchaseReturns (
    returnId        INTEGER PRIMARY KEY AUTOINCREMENT,
    purchaseOrderId INTEGER,                        -- ссылка на purchaseOrders (таблица будет позже)
    productId       INTEGER NOT NULL REFERENCES products(productId),
    warehouseId     INTEGER REFERENCES warehouses(warehouseId),  -- nullable (товар может не вернуться)
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    reasonId        INTEGER REFERENCES returnReasons(reasonId),
    returnDate      TEXT NOT NULL,
    refundAmount    REAL CHECK (refundAmount >= 0),
    notes           TEXT,
    createdAt       TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- ЧАСТЬ 5: ТРАНЗАКЦИИ
-- =====================================================================

-- ---------------------------------------------------------------------
-- buyers — Покупатели
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS buyers (
    buyerId         INTEGER PRIMARY KEY AUTOINCREMENT,
    buyerNickname   TEXT NOT NULL UNIQUE,           -- 'Физлицо', 'guest_2026_0001'
    buyerCity       TEXT,                           -- город (опц.)
    ageGroupId      INTEGER REFERENCES ageGroups(ageGroupId),  -- по умолчанию 25-34
    isActive        INTEGER NOT NULL DEFAULT 1,
    createdAt       TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- salesOrders — Заказы на продажу
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS salesOrders (
    salesOrderId        INTEGER PRIMARY KEY AUTOINCREMENT,
    buyerId             INTEGER NOT NULL REFERENCES buyers(buyerId),
    marketplaceId       INTEGER NOT NULL REFERENCES marketplaces(marketplaceId),
    marketplaceOrderId  TEXT,                       -- номер заказа на площадке
    currencyId          INTEGER NOT NULL REFERENCES currencies(currencyId),  -- в коде явно (RUB)
    payoutId            INTEGER REFERENCES payouts(payoutId),
    notes               TEXT,
    createdAt           TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_salesOrders_buyerId ON salesOrders(buyerId);
CREATE INDEX IF NOT EXISTS idx_salesOrders_marketplaceId ON salesOrders(marketplaceId);
CREATE INDEX IF NOT EXISTS idx_salesOrders_marketplaceOrderId ON salesOrders(marketplaceOrderId);

-- ---------------------------------------------------------------------
-- salesOrderItems — Позиции заказа
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS salesOrderItems (
    salesOrderItemId    INTEGER PRIMARY KEY AUTOINCREMENT,
    salesOrderId        INTEGER NOT NULL REFERENCES salesOrders(salesOrderId) ON DELETE CASCADE,
    productId           INTEGER NOT NULL REFERENCES products(productId),
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    salePrice           REAL NOT NULL CHECK (salePrice >= 0),
    warehouseId         INTEGER NOT NULL REFERENCES warehouses(warehouseId),  -- откуда списано
    notes               TEXT,
    createdAt           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_salesOrderItems_salesOrderId ON salesOrderItems(salesOrderId);
CREATE INDEX IF NOT EXISTS idx_salesOrderItems_productId ON salesOrderItems(productId);

-- ---------------------------------------------------------------------
-- salesOrderStatusHistory — История статусов заказа
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS salesOrderStatusHistory (
    historyId       INTEGER PRIMARY KEY AUTOINCREMENT,
    salesOrderId    INTEGER NOT NULL REFERENCES salesOrders(salesOrderId) ON DELETE CASCADE,
    statusId        INTEGER NOT NULL REFERENCES statuses(statusId),
    statusDate      TEXT NOT NULL,                  -- когда установлен
    comment         TEXT
);

CREATE INDEX IF NOT EXISTS idx_salesOrderStatusHistory_salesOrderId ON salesOrderStatusHistory(salesOrderId);

-- ---------------------------------------------------------------------
-- payouts — Выплаты маркетплейсов
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payouts (
    payoutId        INTEGER PRIMARY KEY AUTOINCREMENT,
    marketplaceId   INTEGER NOT NULL REFERENCES marketplaces(marketplaceId),
    periodStart     TEXT NOT NULL,
    periodEnd       TEXT NOT NULL,
    paidAt          TEXT NOT NULL,                  -- дата перечисления
    totalAmount     REAL NOT NULL CHECK (totalAmount >= 0),
    reportNumber    TEXT,                           -- номер отчёта OZON
    notes           TEXT,
    createdAt       TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- payoutAdjustments — Детализация выплаты
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payoutAdjustments (
    adjustmentId        INTEGER PRIMARY KEY AUTOINCREMENT,
    payoutId            INTEGER NOT NULL REFERENCES payouts(payoutId) ON DELETE CASCADE,
    salesOrderId        INTEGER NOT NULL REFERENCES salesOrders(salesOrderId),
    adjustmentTypeId    INTEGER NOT NULL REFERENCES adjustmentTypes(adjustmentTypeId),
    amount              REAL NOT NULL,              -- + нам, − удержание
    notes               TEXT,
    createdAt           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_payoutAdjustments_payoutId ON payoutAdjustments(payoutId);
CREATE INDEX IF NOT EXISTS idx_payoutAdjustments_salesOrderId ON payoutAdjustments(salesOrderId);

-- ---------------------------------------------------------------------
-- syncLog — Лог синхронизации
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS syncLog (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    syncType        TEXT NOT NULL,                  -- 'ozon_sales', 'ozon_products'
    dateFrom        TEXT,
    dateTo          TEXT,
    recordsCount    INTEGER DEFAULT 0,
    syncedAt        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- ГОТОВО. Все таблицы и индексы созданы (v3.1).
-- =====================================================================