-- =====================================================================
-- Only_limited_magazin
-- Фаза 2: Товары и склад (7 таблиц)
-- PostgreSQL 14+
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 2.1. goods — Товары (SKU)
-- ---------------------------------------------------------------------
CREATE TABLE goods (
    "goodId"           SERIAL         PRIMARY KEY,
    "goodName"         VARCHAR(200)   NOT NULL UNIQUE,
    "baseGameName"     VARCHAR(150),
    "typeGoodId"       SMALLINT       NOT NULL REFERENCES "typeGoods"("typeGoodId"),
    "platformId"       SMALLINT       REFERENCES platforms("platformId"),
    "relatedGameId"    INTEGER        REFERENCES goods("goodId"),
    "publisherId"      SMALLINT       REFERENCES publishers("publisherId"),
    "regionId"         SMALLINT       REFERENCES regions("regionId"),
    "editionId"        SMALLINT       NOT NULL DEFAULT 1 REFERENCES "editionTypes"("editionId"),
    "firstReleaseYear" SMALLINT       CHECK ("firstReleaseYear" BETWEEN 1950 AND 2100),
    "firstYearEdition" SMALLINT       CHECK ("firstYearEdition" BETWEEN 1950 AND 2100),
    "remakeYear"       SMALLINT       CHECK ("remakeYear" BETWEEN 1950 AND 2100),
    "audience"         SMALLINT       CHECK ("audience" IN (0, 6, 12, 16, 18)),
    "ageRestricted"    BOOLEAN        NOT NULL DEFAULT FALSE,
    "dataQuality"      VARCHAR(10)    NOT NULL DEFAULT 'minimal'
                       CHECK ("dataQuality" IN ('full', 'partial', 'minimal')),
    "barcode"          VARCHAR(50)    UNIQUE,
    "sku"              VARCHAR(50)    UNIQUE,
    "notes"            TEXT,
    "isActive"         BOOLEAN        NOT NULL DEFAULT TRUE,
    "createdAt"        TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"        TIMESTAMP
);

CREATE INDEX "idx_goods_baseGameName" ON goods ("baseGameName");
CREATE INDEX "idx_goods_platformId" ON goods ("platformId");
CREATE INDEX "idx_goods_typeGoodId" ON goods ("typeGoodId");
CREATE INDEX "idx_goods_relatedGameId" ON goods ("relatedGameId");
CREATE INDEX "idx_goods_isActive" ON goods ("isActive");

-- ---------------------------------------------------------------------
-- 2.2. productGenres — Жанры товара (M2M)
-- ---------------------------------------------------------------------
CREATE TABLE "productGenres" (
    "productId" INTEGER      NOT NULL REFERENCES goods("goodId") ON DELETE CASCADE,
    "genreId"   SMALLINT     NOT NULL REFERENCES genres("genreId") ON DELETE RESTRICT,
    "createdAt" TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY ("productId", "genreId")
);

CREATE INDEX "idx_productGenres_genreId" ON "productGenres" ("genreId");

-- ---------------------------------------------------------------------
-- 2.3. productLanguages — Языки товара (M2M)
-- ---------------------------------------------------------------------
CREATE TABLE "productLanguages" (
    "productId"  INTEGER      NOT NULL REFERENCES goods("goodId") ON DELETE CASCADE,
    "languageId" SMALLINT     NOT NULL REFERENCES languages("languageId") ON DELETE RESTRICT,
    "createdAt"  TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY ("productId", "languageId")
);

CREATE INDEX "idx_productLanguages_languageId" ON "productLanguages" ("languageId");

-- ---------------------------------------------------------------------
-- 2.4. bundleItems — Состав сборника (M2M между товарами)
-- ---------------------------------------------------------------------
CREATE TABLE "bundleItems" (
    "bundleGoodId"   INTEGER      NOT NULL REFERENCES goods("goodId") ON DELETE CASCADE,
    "includedGoodId" INTEGER      NOT NULL REFERENCES goods("goodId") ON DELETE RESTRICT,
    "quantity"       SMALLINT     NOT NULL DEFAULT 1 CHECK ("quantity" > 0),
    "createdAt"      TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY ("bundleGoodId", "includedGoodId"),
    CONSTRAINT bundleItems_no_self_reference CHECK ("bundleGoodId" <> "includedGoodId")
);

CREATE INDEX "idx_bundleItems_includedGoodId" ON "bundleItems" ("includedGoodId");

-- ---------------------------------------------------------------------
-- 2.5. warehouses — Склады
-- ---------------------------------------------------------------------
CREATE TABLE warehouses (
    "warehouseId"   SMALLSERIAL   PRIMARY KEY,
    "warehouseName" VARCHAR(50)   NOT NULL UNIQUE,
    "sortOrder"     SMALLINT      NOT NULL DEFAULT 100,
    "isActive"      BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 2.6. stock — Остатки на складах
-- ---------------------------------------------------------------------
CREATE TABLE stock (
    "warehouseId"         SMALLINT       NOT NULL REFERENCES warehouses("warehouseId"),
    "goodId"              INTEGER        NOT NULL REFERENCES goods("goodId") ON DELETE RESTRICT,
    "quantity"            INTEGER        NOT NULL DEFAULT 0 CHECK ("quantity" >= 0),
    "countOfRepair"       INTEGER        NOT NULL DEFAULT 0 CHECK ("countOfRepair" >= 0),
    "avgCostRub"          NUMERIC(12,2)  CHECK ("avgCostRub" >= 0),
    "avgCostUsd"          NUMERIC(12,2)  CHECK ("avgCostUsd" >= 0),
    "avgCostEur"          NUMERIC(12,2)  CHECK ("avgCostEur" >= 0),
    "avgCostUpdatedAt"    DATE,
    "lastExchangeRateDate" DATE,
    "createdAt"           TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"           TIMESTAMP,
    PRIMARY KEY ("warehouseId", "goodId"),
    CONSTRAINT stock_repair_lte_quantity CHECK ("countOfRepair" <= "quantity")
);

CREATE INDEX "idx_stock_goodId" ON stock ("goodId");
CREATE INDEX "idx_stock_quantity" ON stock ("quantity");
CREATE INDEX "idx_stock_countOfRepair" ON stock ("countOfRepair");

-- ---------------------------------------------------------------------
-- 2.7. stockWriteOffs — Списания со склада
-- ---------------------------------------------------------------------
CREATE TABLE "stockWriteOffs" (
    "writeOffId"    SERIAL         PRIMARY KEY,
    "goodId"        INTEGER        NOT NULL REFERENCES goods("goodId") ON DELETE RESTRICT,
    "warehouseId"   SMALLINT       NOT NULL REFERENCES warehouses("warehouseId"),
    "quantity"      INTEGER        NOT NULL CHECK ("quantity" > 0),
    "reason"        VARCHAR(50)    NOT NULL 
                    CHECK ("reason" IN ('defect_on_receipt', 'defect_on_return', 'lost_in_delivery', 'lost_in_return', 'other')),
    "sourceType"    VARCHAR(20)    NOT NULL 
                    CHECK ("sourceType" IN ('purchase_receipt', 'sales_return', 'sales_delivery', 'manual')),
    "sourceId"      INTEGER,
    "writeOffDate"  DATE           NOT NULL,
    "notes"         TEXT,
    "createdAt"     TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"     TIMESTAMP
);

CREATE INDEX "idx_stockWriteOffs_goodId" ON "stockWriteOffs" ("goodId");
CREATE INDEX "idx_stockWriteOffs_writeOffDate" ON "stockWriteOffs" ("writeOffDate");
CREATE INDEX "idx_stockWriteOffs_reason" ON "stockWriteOffs" ("reason");

COMMIT;

-- =====================================================================
-- ГОТОВО. Проверка:
-- SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'public'
--   ORDER BY table_name;
-- Должно быть уже 22 таблицы.
-- =====================================================================