-- =====================================================================
-- Only_limited_magazin
-- Наполнение базовых справочников (стандартные данные)
-- =====================================================================

BEGIN;

-- 1. Валюты (порядок важен: RUB должна быть первой)
INSERT INTO currencies ("currencyCode", "currencyName", "currencySymbol", "isCrypto", "sortOrder") VALUES
('RUB', 'Российский рубль', '₽', FALSE, 10),
('USD', 'Доллар США', '$', FALSE, 20),
('EUR', 'Евро', '€', FALSE, 30),
('JPY', 'Японская йена', '¥', FALSE, 40),
('GBP', 'Фунт стерлингов', '£', FALSE, 50),
('BTC', 'Биткоин', '₿', TRUE, 60),
('USDT', 'Tether', '₮', TRUE, 70),
('ETH', 'Эфириум', 'Ξ', TRUE, 80);

-- 2. Регионы выпуска
INSERT INTO regions ("regionCode", "regionName", "sortOrder") VALUES
('RU', 'Россия / СНГ', 10),
('US', 'Северная Америка (US)', 20),
('EU', 'Европа (EU)', 30),
('JP', 'Япония (JP)', 40),
('Asia', 'Азия (Asia)', 50),
('CN', 'Китай (CN)', 60),
('AUS', 'Австралия (AUS)', 70),
('SA', 'Южная Америка (SA)', 80);

-- 3. Типы изданий (editionId = 1 должен быть Standard)
INSERT INTO "editionTypes" ("editionName", "sortOrder") VALUES
('Standard', 10),
('Deluxe', 20),
('Ultimate', 30),
('Collector''s', 40),
('Limited', 50),
('Steelbook', 60),
('Signature', 70),
('Day One', 80),
('Gold', 90),
('Anniversary', 100),
('Special', 110),
('Premium', 120),
('Limited Collector''s', 130);

-- 4. Типы товаров
INSERT INTO "typeGoods" ("typeGoodName", "sortOrder") VALUES
('game', 10),
('bundle', 20),
('steelbook', 30),
('gamepad', 40),
('joystick', 50),
('collectorBox', 60),
('accessory', 70),
('card', 80),
('toy', 90),
('figure', 100),
('badge', 110),
('sticker', 120);

-- 5. Статусы (только purchase и sale)
INSERT INTO statuses ("statusName", "statusType", "sortOrder") VALUES
('at_carrier', 'purchase', 10),
('shipped', 'purchase', 20),
('customs', 'purchase', 30),
('out_for_delivery', 'purchase', 40),
('received', 'purchase', 50),
('paid', 'sale', 60),
('shipped', 'sale', 70),
('received', 'sale', 80),
('refusal', 'sale', 90);

-- 6. Маркетплейсы (продажа)
INSERT INTO marketplaces ("marketplaceName", "defaultCommissionRate", "sortOrder") VALUES
('OZON', 0.45, 10),
('Avito', 0.05, 20),
('Wildberries', 0.25, 30),
('YandexMarket', 0.20, 40),
('VK', 0.10, 50),
('SelfSite', 0.00, 60);

-- 7. Площадки закупки (международные и внутренние)
-- Сначала нам нужны ID стран, но мы используем подзапросы для надежности
INSERT INTO "purchasePlatforms" ("purchasePlatformName", "countryId", "sortOrder") VALUES
('eBay US', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US'), 10),
('eBay EU', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'DE'), 20),
('Amazon JP', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP'), 30),
('Amazon US', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US'), 40),
('Play-Asia', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'HK'), 50),
('CDJapan', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP'), 60),
('Avito', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'RU'), 70),
('YandexMarket', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'RU'), 80),
('OZON (как продавец)', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'RU'), 90);

-- 8. Службы доставки
INSERT INTO carriers ("carrierName", "sortOrder") VALUES
('DHL', 10),
('FedEx', 20),
('UPS', 30),
('USPS', 40),
('EMS (Japan Post)', 50),
('Почта России', 60),
('СДЭК', 70),
('Boxberry', 80),
('Cainiao', 90);

-- 9. Жанры
INSERT INTO genres ("genreName", "sortOrder") VALUES
('Action', 10),
('Horror', 20),
('Strategy', 30),
('Adventure', 40),
('RPG', 50),
('Simulation', 60),
('Racing', 70),
('Sports', 80),
('Fighting', 90),
('Puzzle', 100),
('Indie', 110),
('Fiction', 120);

COMMIT;