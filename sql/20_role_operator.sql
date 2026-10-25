-- =====================================================================
-- Only_limited_magazin
-- Роль: Оператор (кладовщик + продавец) для этапа наполнения и MVP
-- ВНИМАНИЕ: этот скрипт выполняется ТОЛЬКО в PostgreSQL.
--           В SQLite роли пользователей не поддерживаются.
-- =====================================================================

BEGIN;

-- 1. Создаем пользователя (пароль обязательно поменять в реальной среде!)
DROP ROLE IF EXISTS operator;
CREATE ROLE operator WITH LOGIN PASSWORD 'Operator_2026_Secure!';

GRANT CONNECT ON DATABASE only_limited_magazin TO operator;
GRANT USAGE ON SCHEMA public TO operator;

-- 2. ЧТЕНИЕ ВСЕХ ТАБЛИЦ (без этого он даже списки не увидит)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO operator;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO operator;

-- 3. ПРАВА НА СПРАВОЧНИКИ (наполнение "выпадающих" списков)
GRANT INSERT, UPDATE ON platforms TO operator;
GRANT INSERT, UPDATE ON "typeGoods" TO operator;
GRANT INSERT, UPDATE ON genres TO operator;
GRANT INSERT, UPDATE ON publishers TO operator;
GRANT INSERT, UPDATE ON regions TO operator;
GRANT INSERT, UPDATE ON "editionTypes" TO operator;

-- 4. ПРАВА НА ТОВАРЫ И СКЛАД
GRANT INSERT, UPDATE ON goods TO operator;
GRANT INSERT, UPDATE ON "productGenres" TO operator;
GRANT INSERT, UPDATE ON "productLanguages" TO operator;
GRANT INSERT, UPDATE ON "bundleItems" TO operator;
GRANT INSERT, UPDATE ON stock TO operator;
GRANT INSERT, UPDATE ON "stockWriteOffs" TO operator;

-- 5. ПРАВА НА ПРОДАЖИ
GRANT INSERT, UPDATE ON buyers TO operator;
GRANT INSERT, UPDATE ON "salesOrders" TO operator;
GRANT INSERT, UPDATE ON "salesOrderItems" TO operator;
GRANT INSERT, UPDATE ON "salesOrderStatusHistory" TO operator;
GRANT INSERT, UPDATE ON "salesReturns" TO operator;

-- 6. ЖЕСТКИЕ ЗАПРЕТЫ
REVOKE CREATE ON SCHEMA public FROM operator;
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM operator;

-- 7. Лимит подключений
ALTER ROLE operator CONNECTION LIMIT 5;

COMMIT;

-- =====================================================================
-- Проверка (подключившись как operator):
--   SELECT * FROM countries;           -- работает
--   DROP TABLE countries;              -- ошибка: permission denied
--   DELETE FROM goods;                 -- ошибка: permission denied
-- =====================================================================