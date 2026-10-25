import sqlite3

c = sqlite3.connect('db/only_limited.sqlite3')

# 1. Создаем таблицу типов товаров
c.execute('''CREATE TABLE IF NOT EXISTS typeGoods (
    typeGoodId INTEGER PRIMARY KEY AUTOINCREMENT,
    typeGoodName TEXT UNIQUE,
    sortOrder INTEGER DEFAULT 100
)''')
# Заполняем
for i, name in enumerate(['game', 'bundle', 'steelbook', 'gamepad', 'figure', 'accessory']):
    c.execute('INSERT OR IGNORE INTO typeGoods (typeGoodName, sortOrder) VALUES (?, ?)', (name, (i+1)*10))

# 2. Создаем таблицу платформ
c.execute('''CREATE TABLE IF NOT EXISTS platforms (
    platformId INTEGER PRIMARY KEY AUTOINCREMENT,
    platformName TEXT,
    platformVersion TEXT,
    sortOrder INTEGER DEFAULT 100
)''')
# Заполняем
platforms = [('PlayStation', '5'), ('PlayStation', '4'), ('Xbox', 'Series'), ('Nintendo Switch', '1'), ('PC', 'Windows')]
for i, (name, version) in enumerate(platforms):
    c.execute('INSERT OR IGNORE INTO platforms (platformName, platformVersion, sortOrder) VALUES (?, ?, ?)', (name, version, (i+1)*10))

# 3. Создаем таблицу изданий
c.execute('''CREATE TABLE IF NOT EXISTS editionTypes (
    editionId INTEGER PRIMARY KEY AUTOINCREMENT,
    editionName TEXT UNIQUE,
    sortOrder INTEGER DEFAULT 100
)''')
for i, name in enumerate(['Standard', 'Deluxe', 'Ultimate', 'Collector\'s']):
    c.execute('INSERT OR IGNORE INTO editionTypes (editionName, sortOrder) VALUES (?, ?)', (name, (i+1)*10))

# 4. Создаем таблицу регионов
c.execute('''CREATE TABLE IF NOT EXISTS regions (
    regionId INTEGER PRIMARY KEY AUTOINCREMENT,
    regionCode TEXT UNIQUE,
    sortOrder INTEGER DEFAULT 100
)''')
for i, code in enumerate(['US', 'EU', 'RU', 'JP', 'Asia']):
    c.execute('INSERT OR IGNORE INTO regions (regionCode, sortOrder) VALUES (?, ?)', (code, (i+1)*10))

# 5. Создаем таблицу издателей
c.execute('''CREATE TABLE IF NOT EXISTS publishers (
    publisherId INTEGER PRIMARY KEY AUTOINCREMENT,
    publisherName TEXT UNIQUE
)''')
publishers = ['Nintendo', 'Sony', 'Microsoft', 'Sega', 'EA', 'Ubisoft', 'Capcom']
for name in publishers:
    c.execute('INSERT OR IGNORE INTO publishers (publisherName) VALUES (?)', (name,))

c.commit()
print("Все недостающие справочники успешно созданы и заполнены!")