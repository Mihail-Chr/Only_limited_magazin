-- =====================================================================
-- Only_limited_magazin
-- Тестовые данные (Сквозной сценарий: Закупка -> Склад -> Продажа)
-- =====================================================================

DO $$
DECLARE
    v_warehouseId INT;
    v_goodId INT;
    v_sellerId INT;
    v_shipmentId INT;
    v_poId INT;
    v_buyerId INT;
    v_soId INT;
    v_payoutId INT;
BEGIN
    -- 1. Создаем склад
    INSERT INTO warehouses ("warehouseName") VALUES ('main') RETURNING "warehouseId" INTO v_warehouseId;

    -- 2. Создаем товар (Doom Eternal Deluxe для PS4, регион US)
    INSERT INTO goods ("goodName", "baseGameName", "typeGoodId", "platformId", "publisherId", "regionId", "editionId", "firstReleaseYear", "dataQuality") 
    VALUES (
        'Doom Eternal Deluxe Edition (PS4, US)', 
        'Doom Eternal', 
        (SELECT "typeGoodId" FROM "typeGoods" WHERE "typeGoodName" = 'game'),
        (SELECT "platformId" FROM platforms WHERE "platformName" = 'PlayStation' AND "platformVersion" = '4'),
        (SELECT "publisherId" FROM publishers WHERE "publisherName" = 'Activision Blizzard'), -- условно
        (SELECT "regionId" FROM regions WHERE "regionCode" = 'US'),
        (SELECT "editionId" FROM "editionTypes" WHERE "editionName" = 'Deluxe'),
        2020,
        'full'
    ) RETURNING "goodId" INTO v_goodId;

    -- Привязываем жанры и языки (M2M)
    INSERT INTO "productGenres" ("productId", "genreId") 
    VALUES (v_goodId, (SELECT "genreId" FROM genres WHERE "genreName" = 'Action')),
           (v_goodId, (SELECT "genreId" FROM genres WHERE "genreName" = 'Horror'));

    INSERT INTO "productLanguages" ("productId", "languageId") 
    VALUES (v_goodId, (SELECT "languageId" FROM languages WHERE "languageCode" = 'en')),
           (v_goodId, (SELECT "languageId" FROM languages WHERE "languageCode" = 'ru'));

    -- 3. Создаем поставщика (частник на eBay US)
    INSERT INTO sellers ("sellerName", "purchasePlatformId", "sellerType") 
    VALUES (
        'eBay private seller (US)', 
        (SELECT "purchasePlatformId" FROM "purchasePlatforms" WHERE "purchasePlatformName" = 'eBay US'),
        'private'
    ) RETURNING "sellerId" INTO v_sellerId;

    -- 4. СОЗДАЕМ ЗАКУПКУ
    -- Создаем посылку (из США в РФ, доставка 20 USD, пошлина 5 USD)
    INSERT INTO shipments ("originCountryId", "currencyId", "deliveryCost", "customsDuty") 
    VALUES (
        (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US'),
        (SELECT "currencyId" FROM currencies WHERE "currencyCode" = 'USD'),
        20.00, 5.00
    ) RETURNING "shipmentId" INTO v_shipmentId;

    -- Создаем заказ на закупку
    INSERT INTO "purchaseOrders" ("sellerId", "currencyId", "orderDate", "shipmentId") 
    VALUES (
        v_sellerId, 
        (SELECT "currencyId" FROM currencies WHERE "currencyCode" = 'USD'), 
        '2026-10-01', 
        v_shipmentId
    ) RETURNING "purchaseOrderId" INTO v_poId;

    -- Добавляем позицию (10 штук по 30 USD)
    INSERT INTO "purchaseOrderItems" ("purchaseOrderId", "goodId", "quantityOrdered", "supplierPrice") 
    VALUES (v_poId, v_goodId, 10, 30.00);

    -- Добавляем историю статусов посылки (поступила в СД, отправлена, получена)
    INSERT INTO "shipmentStatusHistory" ("shipmentId", "statusId", "statusDate") VALUES 
    (v_shipmentId, (SELECT "statusId" FROM statuses WHERE "statusName" = 'at_carrier' AND "statusType" = 'purchase'), '2026-10-02'),
    (v_shipmentId, (SELECT "statusId" FROM statuses WHERE "statusName" = 'shipped' AND "statusType" = 'purchase'), '2026-10-05'),
    (v_shipmentId, (SELECT "statusId" FROM statuses WHERE "statusName" = 'received' AND "statusType" = 'purchase'), '2026-10-20');

    -- 5. ПРИЕМКА НА СКЛАД
    -- Имитируем, что мы все получили
    UPDATE "purchaseOrderItems" SET "quantityReceived" = 10 WHERE "purchaseOrderId" = v_poId;

    -- Рассчитываем себестоимость (Landed cost)
    -- 10 шт * 30 USD = 300 USD (стоимость товара). Доставка 20 + Пошлина 5 = 25 USD.
    -- Итого 325 USD за 10 шт = 32.5 USD за штуку.
    -- Курс условно 1 USD = 90 RUB. Итоговая цена в рублях: 32.5 * 90 = 2925 RUB.
    INSERT INTO stock ("warehouseId", "goodId", "quantity", "avgCostUsd", "avgCostRub", "avgCostUpdatedAt") 
    VALUES (v_warehouseId, v_goodId, 10, 32.50, 2925.00, '2026-10-20');

    -- 6. ПРОДАЖА
    -- Создаем покупателя
    INSERT INTO buyers ("buyerNickname") VALUES ('gamer_pro_99') RETURNING "buyerId" INTO v_buyerId;

    -- Создаем заказ на Ozon
    INSERT INTO "salesOrders" ("buyerId", "marketplaceId", "currencyId", "orderDate") 
    VALUES (
        v_buyerId, 
        (SELECT "marketplaceId" FROM marketplaces WHERE "marketplaceName" = 'OZON'),
        (SELECT "currencyId" FROM currencies WHERE "currencyCode" = 'RUB'),
        '2026-10-22'
    ) RETURNING "salesOrderId" INTO v_soId;

    -- Добавляем позицию (продаем 2 штуки по 5000 RUB, себестоимость на момент продажи 2925)
    INSERT INTO "salesOrderItems" ("salesOrderId", "goodId", "quantity", "salePrice", "costAtSale", "warehouseId") 
    VALUES (v_soId, v_goodId, 2, 5000.00, 2925.00, v_warehouseId);

    -- СПИСЫВАЕМ СО СКЛАДА (было 10, стало 8)
    UPDATE stock SET "quantity" = "quantity" - 2 WHERE "warehouseId" = v_warehouseId AND "goodId" = v_goodId;

    -- История статусов продажи (оплачен, отправлен, получен)
    INSERT INTO "salesOrderStatusHistory" ("salesOrderId", "statusId", "statusDate") VALUES 
    (v_soId, (SELECT "statusId" FROM statuses WHERE "statusName" = 'paid' AND "statusType" = 'sale'), '2026-10-22'),
    (v_soId, (SELECT "statusId" FROM statuses WHERE "statusName" = 'shipped' AND "statusType" = 'sale'), '2026-10-23'),
    (v_soId, (SELECT "statusId" FROM statuses WHERE "statusName" = 'received' AND "statusType" = 'sale'), '2026-10-25');

    -- 7. ВЫПЛАТА ОТ OZON
    -- Создаем выплату за период
    INSERT INTO payouts ("marketplaceId", "periodStart", "periodEnd", "paidAt", "totalAmount") 
    VALUES (
        (SELECT "marketplaceId" FROM marketplaces WHERE "marketplaceName" = 'OZON'),
        '2026-10-16', '2026-10-31', '2026-11-05', 5500.00 -- Условная общая сумма
    ) RETURNING "payoutId" INTO v_payoutId;

    -- Привязываем заказ к выплате
    UPDATE "salesOrders" SET "payoutId" = v_payoutId WHERE "salesOrderId" = v_soId;

    -- Добавляем детализацию: сумма заказа +10000, комиссия Ozon 45% = -4500
    INSERT INTO "payoutAdjustments" ("payoutId", "salesOrderId", "adjustmentType", "amount") VALUES 
    (v_payoutId, v_soId, 'order_amount', 10000.00),
    (v_payoutId, v_soId, 'commission', -4500.00);

END $$;