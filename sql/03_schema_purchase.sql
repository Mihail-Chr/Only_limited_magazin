-- =====================================================================
-- Only_limited_magazin
-- Фаза 3: Закупка (5 таблиц)
-- PostgreSQL 14+
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 3.1. shipments — Посылки
-- Создаем ПЕРВОЙ, так как purchaseOrders будет на неё ссылаться.
-- ---------------------------------------------------------------------
CREATE TABLE shipments (
    "shipmentId"      SERIAL         PRIMARY KEY,
    "trackNumber"     VARCHAR(100),
    "carrierId"       SMALLINT       REFERENCES carriers("carrierId"),
    "originCountryId" SMALLINT       REFERENCES countries("countryId"),
    "currencyId"      SMALLINT       NOT NULL REFERENCES currencies("currencyId"),
    "deliveryCost"    NUMERIC(12,2)  CHECK ("deliveryCost" >= 0),
    "customsDuty"     NUMERIC(12,2)  CHECK ("customsDuty" >= 0),
    "notes"           TEXT,
    "createdAt"       TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"       TIMESTAMP
);

CREATE INDEX "idx_shipments_trackNumber" ON shipments ("trackNumber");
CREATE INDEX "idx_shipments_carrierId" ON shipments ("carrierId");
CREATE INDEX "idx_shipments_originCountryId" ON shipments ("originCountryId");
CREATE INDEX "idx_shipments_currencyId" ON shipments ("currencyId");

-- ---------------------------------------------------------------------
-- 3.2. purchaseOrders — Заказы на закупку
-- ---------------------------------------------------------------------
CREATE TABLE "purchaseOrders" (
    "purchaseOrderId" SERIAL         PRIMARY KEY,
    "sellerId"        SMALLINT       NOT NULL REFERENCES sellers("sellerId"),
    "currencyId"      SMALLINT       NOT NULL REFERENCES currencies("currencyId"),
    "orderDate"       DATE           NOT NULL,
    "externalNumber"  VARCHAR(50),
    "shipmentId"      INTEGER        REFERENCES shipments("shipmentId") ON DELETE RESTRICT,
    "notes"           TEXT,
    "createdAt"       TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"       TIMESTAMP
);

CREATE INDEX "idx_purchaseOrders_sellerId" ON "purchaseOrders" ("sellerId");
CREATE INDEX "idx_purchaseOrders_currencyId" ON "purchaseOrders" ("currencyId");
CREATE INDEX "idx_purchaseOrders_shipmentId" ON "purchaseOrders" ("shipmentId");
CREATE INDEX "idx_purchaseOrders_orderDate" ON "purchaseOrders" ("orderDate");

-- ---------------------------------------------------------------------
-- 3.3. purchaseOrderItems — Позиции заказа на закупку
-- ---------------------------------------------------------------------
CREATE TABLE "purchaseOrderItems" (
    "purchaseOrderItemId" SERIAL         PRIMARY KEY,
    "purchaseOrderId"     INTEGER        NOT NULL REFERENCES "purchaseOrders"("purchaseOrderId") ON DELETE CASCADE,
    "goodId"              INTEGER        NOT NULL REFERENCES goods("goodId") ON DELETE RESTRICT,
    "quantityOrdered"     INTEGER        NOT NULL CHECK ("quantityOrdered" > 0),
    "quantityReceived"    INTEGER,
    "supplierPrice"       NUMERIC(12,2)  NOT NULL CHECK ("supplierPrice" >= 0),
    "notes"               TEXT,
    "createdAt"           TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"           TIMESTAMP,
    CONSTRAINT po_items_received_lte_ordered 
        CHECK ("quantityReceived" >= 0 AND "quantityReceived" <= "quantityOrdered")
);

CREATE INDEX "idx_po_items_purchaseOrderId" ON "purchaseOrderItems" ("purchaseOrderId");
CREATE INDEX "idx_po_items_goodId" ON "purchaseOrderItems" ("goodId");
CREATE INDEX "idx_po_items_quantityReceived" ON "purchaseOrderItems" ("quantityReceived");

-- ---------------------------------------------------------------------
-- 3.4. shipmentStatusHistory — История статусов посылки
-- ---------------------------------------------------------------------
CREATE TABLE "shipmentStatusHistory" (
    "historyId"   SERIAL       PRIMARY KEY,
    "shipmentId"  INTEGER      NOT NULL REFERENCES shipments("shipmentId") ON DELETE CASCADE,
    "statusId"    SMALLINT     NOT NULL REFERENCES statuses("statusId"),
    "statusDate"  TIMESTAMP    NOT NULL DEFAULT NOW(),
    "comment"     TEXT,
    "createdAt"   TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX "idx_shipmentStatusHistory_shipmentId" ON "shipmentStatusHistory" ("shipmentId", "statusDate");
CREATE INDEX "idx_shipmentStatusHistory_statusId" ON "shipmentStatusHistory" ("statusId");

-- ---------------------------------------------------------------------
-- 3.5. shipmentLosses — Потери посылок
-- ---------------------------------------------------------------------
CREATE TABLE "shipmentLosses" (
    "lossId"         SERIAL         PRIMARY KEY,
    "shipmentId"     INTEGER        NOT NULL REFERENCES shipments("shipmentId") ON DELETE RESTRICT,
    "lossType"       VARCHAR(10)    NOT NULL CHECK ("lossType" IN ('full', 'partial')),
    "lossDate"       DATE           NOT NULL,
    "reason"         VARCHAR(50)    NOT NULL 
                     CHECK ("reason" IN ('customs_rejected', 'destroyed', 'returned_to_seller', 'lost_in_transit', 'defect', 'incomplete')),
    "lossAmount"     NUMERIC(12,2)  NOT NULL CHECK ("lossAmount" >= 0),
    "refundReceived" NUMERIC(12,2)  CHECK ("refundReceived" >= 0) DEFAULT 0,
    "notes"          TEXT,
    "createdAt"      TIMESTAMP      NOT NULL DEFAULT NOW(),
    "updatedAt"      TIMESTAMP
);

CREATE INDEX "idx_shipmentLosses_shipmentId" ON "shipmentLosses" ("shipmentId");
CREATE INDEX "idx_shipmentLosses_lossDate" ON "shipmentLosses" ("lossDate");
CREATE INDEX "idx_shipmentLosses_reason" ON "shipmentLosses" ("reason");

COMMIT;

-- =====================================================================
-- ГОТОВО. Проверка:
-- Должно быть уже 27 таблиц.
-- =====================================================================