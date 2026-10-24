-- =====================================================================
-- Only_limited_magazin
-- Наполнение справочников: Страны, Платформы, Языки, Издатели
-- =====================================================================

BEGIN;

-- 1. СТРАНЫ (Основные для игрового рынка и логистики)
INSERT INTO countries ("isoAlpha2", "isoAlpha3", "countryName", "countryNameRu") VALUES
('RU', 'RUS', 'Russia', 'Россия'),
('US', 'USA', 'United States', 'США'),
('JP', 'JPN', 'Japan', 'Япония'),
('CN', 'CHN', 'China', 'Китай'),
('HK', 'HKG', 'Hong Kong', 'Гонконг'),
('GB', 'GBR', 'United Kingdom', 'Великобритания'),
('DE', 'DEU', 'Germany', 'Германия'),
('FR', 'FRA', 'France', 'Франция'),
('IT', 'ITA', 'Italy', 'Италия'),
('ES', 'ESP', 'Spain', 'Испания'),
('CA', 'CAN', 'Canada', 'Канада'),
('AU', 'AUS', 'Australia', 'Австралия'),
('KR', 'KOR', 'South Korea', 'Южная Корея'),
('TW', 'TWN', 'Taiwan', 'Тайвань'),
('BR', 'BRA', 'Brazil', 'Бразилия'),
('PL', 'POL', 'Poland', 'Польша'),
('NL', 'NLD', 'Netherlands', 'Нидерланды'),
('SE', 'SWE', 'Sweden', 'Швеция'),
('CH', 'CHE', 'Switzerland', 'Швейцария'),
('AE', 'ARE', 'United Arab Emirates', 'ОАЭ');

-- 2. ПЛАТФОРМЫ (Основные поколения)
INSERT INTO platforms ("platformName", "platformVersion", "sortOrder") VALUES
('PC', 'Windows', 10),
('PlayStation', '5', 20),
('PlayStation', '4', 30),
('PlayStation', '3', 40),
('PlayStation', '2', 50),
('PlayStation', '1', 60),
('Xbox', 'Series X/S', 70),
('Xbox', 'One', 80),
('Xbox', '360', 90),
('Xbox', 'Original', 100),
('Nintendo Switch', '2', 110),
('Nintendo Switch', '1', 120),
('Nintendo', 'Wii U', 130),
('Nintendo', 'Wii', 140),
('Nintendo', 'GameCube', 150),
('Nintendo', '64', 160),
('Nintendo', 'SNES', 170),
('Nintendo', 'NES', 180),
('Sega', 'Mega Drive/Genesis', 190),
('Sega', 'Dreamcast', 200),
('Sega', 'Saturn', 210),
('Atari', '2600', 220),
('Steam Deck', 'LCD/OLED', 230);

-- 3. ЯЗЫКИ (10-15 самых популярных + multi)
INSERT INTO languages ("languageCode", "languageName", "languageNameRu", "sortOrder") VALUES
('en', 'English', 'Английский', 10),
('ru', 'Russian', 'Русский', 20),
('ja', 'Japanese', 'Японский', 30),
('zh', 'Chinese (Simplified)', 'Китайский (упрощенный)', 40),
('es', 'Spanish', 'Испанский', 50),
('de', 'German', 'Немецкий', 60),
('fr', 'French', 'Французский', 70),
('it', 'Italian', 'Итальянский', 80),
('ko', 'Korean', 'Корейский', 90),
('pt', 'Portuguese', 'Португальский', 100),
('pl', 'Polish', 'Польский', 110),
('tr', 'Turkish', 'Турецкий', 120),
('multi', 'Multi-language', 'Мультиязычный', 130);

-- 4. ИЗДАТЕЛИ (Топ-20, которых все знают)
INSERT INTO publishers ("publisherName", "countryId") VALUES
('Nintendo', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP')),
('Sony Interactive Entertainment', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP')),
('Microsoft / Xbox Game Studios', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US')),
('Sega', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP')),
('Electronic Arts (EA)', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US')),
('Ubisoft', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'FR')),
('Activision Blizzard', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US')),
('Bandai Namco', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP')),
('Capcom', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP')),
('Square Enix', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP')),
('Konami', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP')),
('Take-Two Interactive / Rockstar', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US')),
('CD Projekt', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'PL')),
('Paradox Interactive', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'SE')),
('1C', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'RU')),
('Limited Run Games', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US')),
('Strictly Limited Games', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'DE')),
('Merge Games', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'GB')),
('NIS America', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'US')),
('Idea Factory International', (SELECT "countryId" FROM countries WHERE "isoAlpha2" = 'JP'));

COMMIT;