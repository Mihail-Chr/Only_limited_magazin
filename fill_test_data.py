import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')

# Типы товаров
conn.execute("INSERT OR IGNORE INTO \"typeGoods\" (\"typeGoodName\", \"sortOrder\") VALUES ('game', 10)")
conn.execute("INSERT OR IGNORE INTO \"typeGoods\" (\"typeGoodName\", \"sortOrder\") VALUES ('steelbook', 20)")

# Платформы
conn.execute("INSERT OR IGNORE INTO platforms (\"platformName\", \"platformVersion\", \"sortOrder\") VALUES ('PlayStation', '4', 10)")
conn.execute("INSERT OR IGNORE INTO platforms (\"platformName\", \"platformVersion\", \"sortOrder\") VALUES ('PlayStation', '5', 20)")

# Издания
conn.execute("INSERT OR IGNORE INTO \"editionTypes\" (\"editionName\", \"sortOrder\") VALUES ('Standard', 10)")
conn.execute("INSERT OR IGNORE INTO \"editionTypes\" (\"editionName\", \"sortOrder\") VALUES ('Deluxe', 20)")

# Регионы
conn.execute("INSERT OR IGNORE INTO regions (\"regionCode\", \"sortOrder\") VALUES ('RU', 10)")
conn.execute("INSERT OR IGNORE INTO regions (\"regionCode\", \"sortOrder\") VALUES ('US', 20)")

# Издатели
conn.execute("INSERT OR IGNORE INTO publishers (\"publisherName\") VALUES ('Sony')")
conn.execute("INSERT OR IGNORE INTO publishers (\"publisherName\") VALUES ('Nintendo')")

conn.commit()
print("Тестовые данные добавлены.")