import sqlite3

conn = sqlite3.connect('db/only_limited.sqlite3')

# =====================================================================
# 1. ТИПЫ ТОВАРОВ
# =====================================================================
types = [
    ('game', 10), ('bundle', 20), ('steelbook', 30), ('gamepad', 40),
    ('joystick', 50), ('collectorBox', 60), ('accessory', 70),
    ('card', 80), ('toy', 90), ('figure', 100), ('badge', 110), ('sticker', 120)
]
for name, sort in types:
    conn.execute("INSERT OR IGNORE INTO \"typeGoods\" (\"typeGoodName\", \"sortOrder\") VALUES (?, ?)", (name, sort))

# =====================================================================
# 2. ПЛАТФОРМЫ (основные поколения)
# =====================================================================
platforms = [
    ('PC', 'Windows'), ('PlayStation', '5'), ('PlayStation', '4'), ('PlayStation', '3'),
    ('PlayStation', '2'), ('PlayStation', '1'), ('Xbox', 'Series'), ('Xbox', 'One'),
    ('Xbox', '360'), ('Xbox', 'Original'), ('Nintendo Switch', '2'), ('Nintendo Switch', '1'),
    ('Nintendo', 'Wii U'), ('Nintendo', 'Wii'), ('Nintendo', 'GameCube'), ('Nintendo', '64'),
    ('Nintendo', 'SNES'), ('Nintendo', 'NES'), ('Sega', 'Mega Drive'), ('Sega', 'Dreamcast'),
    ('Sega', 'Saturn'), ('Atari', '2600'), ('Steam Deck', 'LCD/OLED')
]
for i, (name, version) in enumerate(platforms):
    conn.execute("INSERT OR IGNORE INTO platforms (\"platformName\", \"platformVersion\", \"sortOrder\") VALUES (?, ?, ?)", (name, version, (i+1)*10))

# =====================================================================
# 3. ИЗДАНИЯ
# =====================================================================
editions = [
    ('Standard', 10), ('Deluxe', 20), ('Ultimate', 30), ("Collector's", 40),
    ('Limited', 50), ('Steelbook', 60), ('Signature', 70), ('Day One', 80),
    ('Gold', 90), ('Anniversary', 100), ('Special', 110), ('Premium', 120),
    ('K.O.', 130)
]
for name, sort in editions:
    conn.execute("INSERT OR IGNORE INTO \"editionTypes\" (\"editionName\", \"sortOrder\") VALUES (?, ?)", (name, sort))

# =====================================================================
# 4. РЕГИОНЫ
# =====================================================================
regions = [
    ('RU', 10), ('US', 20), ('EU', 30), ('JP', 40), ('Asia', 50), ('CN', 60), ('AUS', 70), ('SA', 80)
]
for code, sort in regions:
    conn.execute("INSERT OR IGNORE INTO regions (\"regionCode\", \"sortOrder\") VALUES (?, ?)", (code, sort))

# =====================================================================
# 5. ИЗДАТЕЛИ (топ-20)
# =====================================================================
publishers = [
    'Nintendo', 'Sega', 'Sony Interactive Entertainment', 'Microsoft / Xbox Game Studios',
    'Electronic Arts', 'Ubisoft', 'Activision Blizzard', 'Bandai Namco', 'Capcom',
    'Square Enix', 'Konami', 'Take-Two Interactive', 'CD Projekt', 'Paradox Interactive',
    '1C', 'Limited Run Games', 'Strictly Limited Games', 'Merge Games', 'NIS America',
    'Idea Factory International'
]
for name in publishers:
    conn.execute("INSERT OR IGNORE INTO publishers (\"publisherName\") VALUES (?)", (name,))

conn.commit()
print("Справочники успешно заполнены (types, platforms, editions, regions, publishers).")