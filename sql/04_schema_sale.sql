-- =====================================================================
-- Only_limited_magazin
-- Фаза 4: Продажа (7 таблиц)
-- PostgreSQL 14+
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 4.1. buyers — Покупатели (минимум ПД)
-- ---------------------------------------------------------------------
CREATE TABLE buyers (
    "buyerId"       SERIAL         PRIMARY KEY,
    "buyerNickname" VARCHAR(100)   NOT NULL UNIQUE,
    "buyerCity"     VARCHAR(100),
    "buyerAgeGroup" VARCHAR(10)    
                    CHECK ("buyerAgeGroup" IN ('18-24', '25-34', '35-44', '45-54', '55+')),
    "createdAt"     TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"     TIMESTAMP
);

COMMENT ON COLUMN buyers."buyerNickname" 
    IS 'Псевдоним с маркетплейса. Для гостей автогенерация guest_YYYY_NNNN';

-- ---------------------------------------------------------------------
-- 4.2. payouts — Выплаты маркетплейсов
-- Создаем ДО salesOrders, так как заказ будет ссылаться на выплату.
-- ---------------------------------------------------------------------
CREATE TABLE payouts (
    "payoutId"      SERIAL         PRIMARY KEY,
    "marketplaceId" SMALLINT       NOT NULL REFERENCES marketplaces("marketplaceId"),
    "periodStart"   DATE           NOT NULL,
    "periodEnd"     DATE           NOT NULL,
    "paidAt"        DATE           NOT NULL,
    "totalAmount"   NUMERIC(12,2)  NOT NULL CHECK ("totalAmount" >= 0),
    "reportNumber"  VARCHAR(50),
    "notes"         TEXT,
    "createdAt"     TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"     TIMESTAMP
);

CREATE INDEX "idx_payouts_marketplaceId" ON payouts ("marketplaceId");
CREATE INDEX "idx_payouts_period" ON payouts ("periodStart", "periodEnd");
CREATE INDEX "idx_payouts_paidAt" ON payouts ("paidAt");

-- ---------------------------------------------------------------------
-- 4.3. salesOrders — Заказы на продажу
-- ---------------------------------------------------------------------
CREATE TABLE "salesOrders" (
    "salesOrderId"       SERIAL         PRIMARY KEY,
    "buyerId"            INTEGER        NOT NULL REFERENCES buyers("buyerId"),
    "marketplaceId"      SMALLINT       NOT NULL REFERENCES marketplaces("marketplaceId"),
    "marketplaceOrderId" VARCHAR(100),
    "currencyId"         SMALLINT       NOT NULL REFERENCES currencies("currencyId"),
    "orderDate"          DATE           NOT NULL,
    "payoutId"           INTEGER        REFERENCES payouts("payoutId"),
    "notes"              TEXT,
    "createdAt"          TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"          TIMESTAMP
);

CREATE INDEX "idx_salesOrders_buyerId" ON "salesOrders" ("buyerId");
CREATE INDEX "idx_salesOrders_marketplaceId" ON "salesOrders" ("marketplaceId");
CREATE INDEX "idx_salesOrders_orderDate" ON "salesOrders" ("orderDate");
CREATE INDEX "idx_salesOrders_payoutId" ON "salesOrders" ("payoutId");
CREATE INDEX "idx_salesOrders_marketplaceOrderId" ON "salesOrders" ("marketplaceOrderId");

-- ---------------------------------------------------------------------
-- 4.4. salesOrderItems — Позиции заказа на продажу
-- ---------------------------------------------------------------------
CREATE TABLE "salesOrderItems" (
    "salesOrderItemId" SERIAL         PRIMARY KEY,
    "salesOrderId"     INTEGER        NOT NULL REFERENCES "salesOrders"("salesOrderId") ON DELETE CASCADE,
    "goodId"           INTEGER        NOT NULL REFERENCES goods("goodId") ON DELETE RESTRICT,
    "quantity"         INTEGER        NOT NULL CHECK ("quantity" > 0),
    "salePrice"        NUMERIC(12,2)  NOT NULL CHECK ("salePrice" >= 0),
    "costAtSale"       NUMERIC(12,2)  CHECK ("costAtSale" >= 0),
    "warehouseId"      SMALLINT       NOT NULL REFERENCES warehouses("warehouseId"),
    "notes"            TEXT,
    "createdAt"        TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"        TIMESTAMP
);

CREATE INDEX "idx_salesOrderItems_salesOrderId" ON "salesOrderItems" ("salesOrderId");
CREATE INDEX "idx_salesOrderItems_goodId" ON "salesOrderItems" ("goodId");
CREATE INDEX "idx_salesOrderItems_warehouseId" ON "salesOrderItems" ("warehouseId");

-- ---------------------------------------------------------------------
-- 4.5. salesOrderStatusHistory — История статусов заказа
-- ---------------------------------------------------------------------
CREATE TABLE "salesOrderStatusHistory" (
    "historyId"    SERIAL       PRIMARY KEY,
    "salesOrderId" INTEGER      NOT NULL REFERENCES "salesOrders"("salesOrderId") ON DELETE CASCADE,
    "statusId"     SMALLINT     NOT NULL REFERENCES statuses("statusId"),
    "statusDate"   TIMESTAMP    NOT NULL DEFAULT NOW(),
    "comment"      TEXT,
    "createdAt"    TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX "idx_salesOrderStatusHistory_salesOrderId" ON "salesOrderStatusHistory" ("salesOrderId", "statusDate");
CREATE INDEX "idx_salesOrderStatusHistory_statusId" ON "salesOrderStatusHistory" ("statusId");

-- ---------------------------------------------------------------------
-- 4.6. salesReturns — Возвраты товара
-- ---------------------------------------------------------------------
CREATE TABLE "salesReturns" (
    "returnId"           SERIAL         PRIMARY KEY,
    "salesOrderId"       INTEGER        NOT NULL REFERENCES "salesOrders"("salesOrderId") ON DELETE RESTRICT,
    "returnDate"         DATE           NOT NULL,
    "reason"             VARCHAR(50)    NOT NULL 
                         CHECK ("reason" IN ('customer_refusal', 'damaged', 'wrong_item', 'not_as_described')),
    "refundAmount"       NUMERIC(12,2)  CHECK ("refundAmount" >= 0) DEFAULT 0,
    "returnShippingCost" NUMERIC(12,2)  CHECK ("returnShippingCost" >= 0) DEFAULT 0,
    "returnCondition"    VARCHAR(20)    NOT NULL 
                         CHECK ("returnCondition" IN ('new', 'used', 'damaged')),
    "warehouseId"        SMALLINT       NOT NULL REFERENCES warehouses("warehouseId"),
    "notes"              TEXT,
    "createdAt"          TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"          TIMESTAMP
);

CREATE INDEX "idx_salesReturns_salesOrderId" ON "salesReturns" ("salesOrderId");
CREATE INDEX "idx_salesReturns_returnDate" ON "salesReturns" ("returnDate");
CREATE INDEX "idx_salesReturns_reason" ON "salesReturns" ("reason");

-- ---------------------------------------------------------------------
-- 4.7. payoutAdjustments — Детализация выплаты по заказам
-- ---------------------------------------------------------------------
CREATE TABLE "payoutAdjustments" (
    "adjustmentId"   SERIAL         PRIMARY KEY,
    "payoutId"       INTEGER        NOT NULL REFERENCES payouts("payoutId") ON DELETE CASCADE,
    "salesOrderId"   INTEGER        NOT NULL REFERENCES "salesOrders"("salesOrderId") ON DELETE RESTRICT,
    "adjustmentType" VARCHAR(30)    NOT NULL 
                     CHECK ("adjustmentType" IN ('order_amount', 'commission', 'refund', 'lost_in_delivery', 'lost_in_return', 'commission_correction', 'other')),
    "amount"         NUMERIC(12,2)  NOT NULL,
    "notes"          TEXT,
    "createdAt"      TIMESTAMP      NOT NULL DEFAULT NOW()
);

CREATE INDEX "idx_payoutAdjustments_payoutId" ON "payoutAdjustments" ("payoutId");
CREATE INDEX "idx_payoutAdjustments_salesOrderId" ON "payoutAdjustments" ("salesOrderId");
CREATE INDEX "idx_payoutAdjustments_adjustmentType" ON "payoutAdjustments" ("adjustmentType");

COMMIT;

-- =====================================================================
-- ГОТОВО! 
-- Проверка: SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';
-- Должно быть 34 таблицы.
-- =====================================================================