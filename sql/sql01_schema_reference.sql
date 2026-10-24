-- =====================================================================
-- Only_limited_magazin
-- Фаза 1: справочники (15 таблиц)
-- PostgreSQL 14+
-- =====================================================================
-- Все таблицы используют camelCase в именах полей → требуются
-- двойные кавычки при обращении к ним в SQL.
--
-- Порядок создания: сначала независимые, потом с FK.
-- Все справочники (кроме countries и exchangeRates) имеют:
--   - sortOrder SMALLINT NOT NULL DEFAULT 100
--   - isActive  BOOLEAN  NOT NULL DEFAULT TRUE
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 1.1. countries — Страны (ISO 3166-1)
-- Заполняется из готового дампа (stefangabos/world_countries).
-- ---------------------------------------------------------------------
CREATE TABLE countries (
    "countryId"     SMALLSERIAL   PRIMARY KEY,
    "isoAlpha2"     CHAR(2)       NOT NULL UNIQUE,
    "isoAlpha3"     CHAR(3)       UNIQUE,
    "countryName"   VARCHAR(100)  NOT NULL,
    "countryNameRu" VARCHAR(100)  NOT NULL,
    "isActive"      BOOLEAN       NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE  countries IS 'Справочник стран по ISO 3166-1';
COMMENT ON COLUMN countries."countryNameRu" IS 'Название на русском — обязательно для интерфейса';

-- ---------------------------------------------------------------------
-- 1.2. regions — Регионы выпуска
-- US, EU, RU, Asia, JP, CN, AUS, SA
-- ---------------------------------------------------------------------
CREATE TABLE regions (
    "regionId"   SMALLSERIAL   PRIMARY KEY,
    "regionCode" VARCHAR(10)   NOT NULL UNIQUE,
    "regionName" VARCHAR(50)   NOT NULL,
    "sortOrder"  SMALLINT      NOT NULL DEFAULT 100,
    "isActive"   BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 1.3. platforms — Платформы (с версией/поколением)
-- PlayStation 4, PlayStation 5, Nintendo Switch 1, Sega Mega Drive...
-- ---------------------------------------------------------------------
CREATE TABLE platforms (
    "platformId"      SMALLSERIAL   PRIMARY KEY,
    "platformName"    VARCHAR(50)   NOT NULL,
    "platformVersion" VARCHAR(20)   NOT NULL,
    "sortOrder"       SMALLINT      NOT NULL DEFAULT 100,
    "isActive"        BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT platforms_name_version_unique
        UNIQUE ("platformName", "platformVersion")
);

-- ---------------------------------------------------------------------
-- 1.4. genres — Жанры
-- ---------------------------------------------------------------------
CREATE TABLE genres (
    "genreId"   SMALLSERIAL   PRIMARY KEY,
    "genreName" VARCHAR(50)   NOT NULL UNIQUE,
    "sortOrder" SMALLINT      NOT NULL DEFAULT 100,
    "isActive"  BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 1.5. languages — Языки (ISO 639-1)
-- ---------------------------------------------------------------------
CREATE TABLE languages (
    "languageId"     SMALLSERIAL   PRIMARY KEY,
    "languageCode"   CHAR(10)       NOT NULL UNIQUE,
    "languageName"   VARCHAR(50)   NOT NULL,
    "languageNameRu" VARCHAR(50)   NOT NULL,
    "sortOrder"      SMALLINT      NOT NULL DEFAULT 100,
    "isActive"       BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 1.6. editionTypes — Типы изданий
-- Standard (editionId=1), Deluxe, Collector's, Steelbook...
-- ---------------------------------------------------------------------
CREATE TABLE "editionTypes" (
    "editionId"   SMALLSERIAL   PRIMARY KEY,
    "editionName" VARCHAR(50)   NOT NULL UNIQUE,
    "sortOrder"   SMALLINT      NOT NULL DEFAULT 100,
    "isActive"    BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 1.7. typeGoods — Типы товаров
-- game, bundle, steelbook, gamepad...
-- ---------------------------------------------------------------------
CREATE TABLE "typeGoods" (
    "typeGoodId"   SMALLSERIAL   PRIMARY KEY,
    "typeGoodName" VARCHAR(50)   NOT NULL UNIQUE,
    "sortOrder"    SMALLINT      NOT NULL DEFAULT 100,
    "isActive"     BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 1.8. currencies — Валюты
-- RUB, USD, EUR, JPY, GBP, BTC, USDT, ETH
-- ---------------------------------------------------------------------
CREATE TABLE currencies (
    "currencyId"     SMALLSERIAL   PRIMARY KEY,
    "currencyCode"   CHAR(5)       NOT NULL UNIQUE,
    "currencyName"   VARCHAR(50)   NOT NULL,
    "currencySymbol" VARCHAR(5),
    "isCrypto"       BOOLEAN       NOT NULL DEFAULT FALSE,
    "sortOrder"      SMALLINT      NOT NULL DEFAULT 100,
    "isActive"       BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 1.9. marketplaces — Маркетплейсы (ПРОДАЖА)
-- OZON, Avito, WB, YM, VK, SelfSite
-- ВНИМАНИЕ: не путать с purchasePlatforms (ЗАКУПКА)
-- ---------------------------------------------------------------------
CREATE TABLE marketplaces (
    "marketplaceId"         SMALLSERIAL   PRIMARY KEY,
    "marketplaceName"       VARCHAR(50)   NOT NULL UNIQUE,
    "defaultCommissionRate" NUMERIC(5,4)  NOT NULL DEFAULT 0.45
                            CHECK ("defaultCommissionRate" >= 0 AND "defaultCommissionRate" <= 1),
    "sortOrder"             SMALLINT      NOT NULL DEFAULT 100,
    "isActive"              BOOLEAN       NOT NULL DEFAULT TRUE
);

COMMENT ON COLUMN marketplaces."defaultCommissionRate"
    IS 'Комиссия для ПРЕДВАРИТЕЛЬНОЙ оценки. Точная — в payoutAdjustments';

-- ---------------------------------------------------------------------
-- 1.10. statuses — Статусы (purchase/sale)
-- UNIQUE (statusName, statusType) — позволяет "shipped" дважды
-- ---------------------------------------------------------------------
CREATE TABLE statuses (
    "statusId"   SMALLSERIAL   PRIMARY KEY,
    "statusName" VARCHAR(30)   NOT NULL,
    "statusType" VARCHAR(20)   NOT NULL
                 CHECK ("statusType" IN ('purchase', 'sale')),
    "sortOrder"  SMALLINT      NOT NULL DEFAULT 100,
    "isActive"   BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT statuses_name_type_unique
        UNIQUE ("statusName", "statusType")
);

-- ---------------------------------------------------------------------
-- 1.11. exchangeRates — Курсы валют (история)
-- Источник: ЦБ РФ для RUB. Кросс-курсы — через RUB.
-- ---------------------------------------------------------------------
CREATE TABLE "exchangeRates" (
    "exchangeRateId" SERIAL         PRIMARY KEY,
    "rateDate"       DATE           NOT NULL,
    "currencyFromId" SMALLINT       NOT NULL REFERENCES currencies("currencyId"),
    "currencyToId"   SMALLINT       NOT NULL REFERENCES currencies("currencyId"),
    "rate"           NUMERIC(14,4)  NOT NULL CHECK ("rate" > 0),
    "source"         VARCHAR(50)    NOT NULL DEFAULT 'CBR',
    "createdAt"      TIMESTAMP      NOT NULL DEFAULT NOW(),
    CONSTRAINT exchangeRates_date_pair_unique
        UNIQUE ("rateDate", "currencyFromId", "currencyToId"),
    CONSTRAINT exchangeRates_diff_currencies
        CHECK ("currencyFromId" <> "currencyToId")
);

CREATE INDEX "idx_exchangeRates_rateDate" ON "exchangeRates" ("rateDate");

-- ---------------------------------------------------------------------
-- 1.12. publishers — Издатели / производители
-- Nintendo, Sega, Sony, Microsoft...
-- ---------------------------------------------------------------------
CREATE TABLE publishers (
    "publisherId"   SMALLSERIAL    PRIMARY KEY,
    "publisherName" VARCHAR(100)   NOT NULL UNIQUE,
    "countryId"     SMALLINT       REFERENCES countries("countryId"),
    "sortOrder"     SMALLINT       NOT NULL DEFAULT 100,
    "isActive"      BOOLEAN        NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 1.13. purchasePlatforms — Площадки ЗАКУПКИ
-- eBay US, eBay EU, Amazon JP, Play-Asia, Avito, YM...
-- ВНИМАНИЕ: не путать с marketplaces (ПРОДАЖА)
-- ---------------------------------------------------------------------
CREATE TABLE "purchasePlatforms" (
    "purchasePlatformId"   SMALLSERIAL   PRIMARY KEY,
    "purchasePlatformName" VARCHAR(50)   NOT NULL UNIQUE,
    "countryId"            SMALLINT      REFERENCES countries("countryId"),
    "sortOrder"            SMALLINT      NOT NULL DEFAULT 100,
    "isActive"             BOOLEAN       NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 1.14. carriers — Службы доставки
-- DHL, FedEx, USPS, EMS, Почта России, СДЭК...
-- ---------------------------------------------------------------------
CREATE TABLE carriers (
    "carrierId"           SMALLSERIAL   PRIMARY KEY,
    "carrierName"         VARCHAR(50)   NOT NULL UNIQUE,
    "trackingUrlTemplate" VARCHAR(200),
    "sortOrder"           SMALLINT      NOT NULL DEFAULT 100,
    "isActive"            BOOLEAN       NOT NULL DEFAULT TRUE
);

COMMENT ON COLUMN carriers."trackingUrlTemplate"
    IS 'Шаблон для будущего API-трекинга. Пример: https://.../track?num={trackNumber}';

-- ---------------------------------------------------------------------
-- 1.15. sellers — Поставщики
-- Физлица группируем: одна запись на площадку/регион
-- (eBay private seller (US), marketplaceSellerId = NULL)
-- ---------------------------------------------------------------------
CREATE TABLE sellers (
    "sellerId"            SMALLSERIAL    PRIMARY KEY,
    "sellerName"          VARCHAR(100)   NOT NULL,
    "purchasePlatformId"  SMALLINT       NOT NULL
                          REFERENCES "purchasePlatforms"("purchasePlatformId"),
    "marketplaceSellerId" VARCHAR(100),
    "sellerType"          VARCHAR(20)    NOT NULL
                          CHECK ("sellerType" IN ('shop', 'private', 'forwarder')),
    "countryId"           SMALLINT       REFERENCES countries("countryId"),
    "contactEmail"        VARCHAR(100),
    "website"             VARCHAR(200),
    "notes"               TEXT,
    "sortOrder"           SMALLINT       NOT NULL DEFAULT 100,
    "isActive"            BOOLEAN        NOT NULL DEFAULT TRUE,
    "createdAt"           TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"           TIMESTAMP,
    -- уникальность в рамках площадки
    CONSTRAINT sellers_platform_name_unique
        UNIQUE ("purchasePlatformId", "sellerName"),
    -- если внутренний ID заполнен, он уникален в рамках площадки
    -- (NULL-ы считаются разными — можно несколько групп физлиц)
    CONSTRAINT sellers_platform_marketplaceId_unique
        UNIQUE ("purchasePlatformId", "marketplaceSellerId")
);

CREATE INDEX "idx_sellers_countryId" ON sellers ("countryId");

COMMIT;

-- =====================================================================
-- ГОТОВО. Проверка:
-- SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'public'
--   ORDER BY table_name;
-- Должно быть 15 таблиц.
-- =====================================================================