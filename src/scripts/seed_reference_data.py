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
# 2. ПЛАТФОРМЫ (с версиями, ревизиями и портативностью)
# =====================================================================
platforms = [
    # PC и Steam
    ('PC', 'Windows', None, 0),
    ('Steam Deck', 'LCD/OLED', None, 0),
    
    # PlayStation
    ('PlayStation', '5', None, 0),
    ('PlayStation', '5', 'Slim', 0),
    ('PlayStation', '5', 'Pro', 0),
    ('PlayStation', '4', None, 0),
    ('PlayStation', '4', 'Slim', 0),
    ('PlayStation', '4', 'Pro', 0),
    ('PlayStation', '3', None, 0),
    ('PlayStation', '3', 'Slim', 0),
    ('PlayStation', '3', 'Super Slim', 0),
    ('PlayStation', '2', None, 0),
    ('PlayStation', '2', 'Slim', 0),
    ('PlayStation', '1', None, 0),
    
    # Xbox
    ('Xbox', 'Series', 'X', 0),
    ('Xbox', 'Series', 'S', 0),
    ('Xbox', 'One', None, 0),
    ('Xbox', 'One', 'S', 0),
    ('Xbox', 'One', 'X', 0),
    ('Xbox', '360', None, 0),
    ('Xbox', '360', 'S', 0),
    ('Xbox', '360', 'E', 0),
    ('Xbox', 'Original', None, 0),
    
    # Nintendo (домашние)
    ('Nintendo Switch', '2', None, 0),
    ('Nintendo Switch', '1', None, 0),
    ('Nintendo Switch', '1', 'OLED', 0),
    ('Nintendo Switch', '1', 'Lite', 1), # Lite портативная
    ('Nintendo', 'Wii U', None, 0),
    ('Nintendo', 'Wii', None, 0),
    ('Nintendo', 'GameCube', None, 0),
    ('Nintendo', '64', None, 0),
    ('Nintendo', 'SNES', None, 0),
    ('Nintendo', 'NES', None, 0),
    
    # Nintendo (портативные)
    ('Nintendo', '3DS', None, 1),
    ('Nintendo', 'DS', None, 1),
    ('Nintendo', 'Game Boy Advance', None, 1),
    ('Nintendo', 'Game Boy Color', None, 1),
    ('Nintendo', 'Game Boy', None, 1),
    
    # Sega
    ('Sega', 'Mega Drive', None, 0),
    ('Sega', 'Dreamcast', None, 0),
    ('Sega', 'Saturn', None, 0),
    ('Sega', 'Game Gear', None, 1),
    
    # Atari
    ('Atari', '2600', None, 0),
]

for i, (name, version, revision, is_portable) in enumerate(platforms):
    conn.execute(
        """INSERT OR IGNORE INTO platforms 
           ("platformName", "platformVersion", "revision", "is_portable", "sortOrder") 
           VALUES (?, ?, ?, ?, ?)""", 
        (name, version, revision, is_portable, (i+1)*10)
    )

# =====================================================================
# 3. ИЗДАНИЯ
# =====================================================================
editions = [
    ('Standard', 10), ('Deluxe', 20), ('Ultimate', 30), ("Collector's", 40),
    ('Limited', 50), ('Steelbook', 60), ('Signature', 70), ('Day One', 80),
    ('Gold', 90), ('Anniversary', 100), ('Special', 110), ('Premium', 120),
    ('K.O.', 130), ('Classic', 140), ('Definitive', 150), ('Complete', 160),
    ('Enhanced', 170), ('Extended', 180), ('Exclusive', 190)
]
for name, sort in editions:
    conn.execute("INSERT OR IGNORE INTO \"editionTypes\" (\"editionName\", \"sortOrder\") VALUES (?, ?)", (name, sort))

# =====================================================================
# 4. РЕГИОНЫ
# =====================================================================
regions = [
    ('RU', 10), ('US', 20), ('EU', 30), ('JP', 40), ('Asia', 50), 
    ('CN', 60), ('AUS', 70), ('SA', 80), ('KR', 90)
]
for code, sort in regions:
    conn.execute("INSERT OR IGNORE INTO regions (\"regionCode\", \"sortOrder\") VALUES (?, ?)", (code, sort))

# =====================================================================
# 5. ИЗДАТЕЛИ (топ-20 + лимитированные)
# =====================================================================
publishers = [
    'Nintendo', 'Sega', 'Sony Interactive Entertainment', 'Microsoft / Xbox Game Studios',
    'Electronic Arts', 'Ubisoft', 'Activision Blizzard', 'Bandai Namco', 'Capcom',
    'Square Enix', 'Konami', 'Take-Two Interactive', 'CD Projekt', 'Paradox Interactive',
    '1C', 'Limited Run Games', 'Strictly Limited Games', 'Merge Games', 'NIS America',
    'Idea Factory International', 'Special Reserve Games', 'Eastasiasoft', 'Play-Asia',
    'Red Art Games', "Pix'n Love", 'Signature Edition Games', 'Fangamer', 'iam8bit', 'Retro-Bit'
]
for name in publishers:
    conn.execute("INSERT OR IGNORE INTO publishers (\"publisherName\") VALUES (?)", (name,))

# =====================================================================
# 6. ПОКУПАТЕЛЬ ПО УМОЛЧАНИЮ (Физлицо)
# =====================================================================
conn.execute("INSERT OR IGNORE INTO buyer (buyerId, buyerNickname) VALUES (1, 'Физлицо')")

conn.commit()
print("Справочники успешно заполнены (v2: платформы, издания, регионы, издатели, покупатель).")