import sqlite3
import re

conn = sqlite3.connect('db/only_limited.sqlite3')
conn.row_factory = sqlite3.Row

# ==================== СЛОВАРИ ====================

TYPE_MAP = {
    'видеоигра': 'game',
    'стилбук': 'steelbook',
    'геймпад': 'gamepad',
    'джойстик': 'joystick',
    'фигурка': 'figure',
    'карточки': 'card',
    'значок': 'badge',
    'наклейка': 'sticker',
    'игрушка': 'toy',
}

PLATFORM_MAP = {
    'nsw': 'Nintendo Switch 1',
    'ps4': 'PlayStation 4',
    'ps5': 'PlayStation 5',
    'ps3': 'PlayStation 3',
    'ps2': 'PlayStation 2',
    'ps1': 'PlayStation 1',
    'xb': 'Xbox One',
    'xbs': 'Xbox Series',
    'xbx': 'Xbox Series',
    'pc': 'PC',
    'xbox 360': 'Xbox 360',
    'xbox one': 'Xbox One',
    'xbox series': 'Xbox Series',
    'xbox original': 'Xbox Original',
    'xbox': 'Xbox Original',
    'nintendo switch': 'Nintendo Switch 1',
    'xo': 'Xbox One',
    'xs': 'Xbox Series',
    'xo/xs': 'Xbox One / Xbox Series',
    'ps4/ps5': 'PlayStation 4 / PlayStation 5',
    'nsw/nsw2': 'Nintendo Switch 1 / Nintendo Switch 2',
}

PUBLISHER_MAP = {
    'limited run games': 'Limited Run Games',
    'strictly limited games': 'Strictly Limited Games',
    'merge games': 'Merge Games',
    'nis america': 'NIS America',
    'idea factory': 'Idea Factory International',
    'super rare games': 'Super Rare Games',
}

REGION_MAP = {
    'ntsc u/c': 'US',
    'ntsc': 'US',
    'usa': 'US',
    'us': 'US',
    'pal': 'EU',
    'eur': 'EU',
    'eu': 'EU',
    'e': 'EU',
    'g': 'EU',
    'j': 'JP',
    'jpn': 'JP',
    'jp': 'JP',
    'asia': 'Asia',
    'ru': 'RU',
    'rus': 'RU',
    'cn': 'CN',
    'chn': 'CN',
    'aus': 'AUS',
    'sa': 'SA',
}

EDITION_MAP = {
    'deluxe': 'Deluxe',
    'ultimate': 'Ultimate',
    "collector's": "Collector's",
    'collectors': "Collector's",
    'limited': 'Limited',
    'steelbook': 'Steelbook',
    'signature': 'Signature',
    'day one': 'Day One',
    'gold': 'Gold',
    'anniversary': 'Anniversary',
    'special': 'Special',
    'premium': 'Premium',
}


def clean_text(text):
    """Убирает лишние символы в конце и двойные пробелы."""
    text = text.strip()
    text = re.sub(r'[\-:,;]+$', '', text).strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*-?\s*Edition$', '', text, flags=re.IGNORECASE).strip()
    return text


def parse_name(full_name):
    result = {
        'type': None,
        'base_name': full_name,
        'platform': None,
        'edition': None,
        'publisher': None,
        'region': None,
    }

    if "Новый товар" in full_name or full_name.startswith("Товар "):
        result['type'] = 'unknown'
        result['base_name'] = full_name
        return result

    brackets = re.findall(r'\(([^)]+)\)', full_name)
    for bracket_text in brackets:
        lower_bracket = bracket_text.lower()

        for key, val in TYPE_MAP.items():
            if key in lower_bracket:
                result['type'] = val
                break

        # Платформа (ищем точные совпадения, без дублей)
        found_platforms = []
        # Сначала проверяем составные (с "/")
        for key, val in PLATFORM_MAP.items():
            if '/' in key and key in lower_bracket:
                if val not in found_platforms:
                    found_platforms.append(val)
        # Если составных нет — проверяем одиночные (с границами слова)
        if not found_platforms:
            for key, val in PLATFORM_MAP.items():
                if '/' not in key and re.search(r'\b' + re.escape(key) + r'\b', lower_bracket):
                    if val not in found_platforms:
                        found_platforms.append(val)
        if found_platforms:
            result['platform'] = ' / '.join(found_platforms)


        for key, val in PUBLISHER_MAP.items():
            if key in lower_bracket:
                result['publisher'] = val
                break

        for key, val in REGION_MAP.items():
            if re.search(r'\b' + re.escape(key) + r'\b', lower_bracket):
                result['region'] = val
                break

    full_name = re.sub(r'\([^)]+\)', '', full_name).strip()

    lower_name = full_name.lower()
    for key, val in PUBLISHER_MAP.items():
        if key in lower_name:
            result['publisher'] = val
            full_name = re.sub(re.escape(key), '', full_name, flags=re.IGNORECASE).strip()
            break

    if not result['type']:
        words = full_name.split()
        if words:
            first_word = words[0].lower()
            if first_word in TYPE_MAP:
                result['type'] = TYPE_MAP[first_word]
                full_name = ' '.join(words[1:]).strip()

    if not result['platform']:
        for key, val in PLATFORM_MAP.items():
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, full_name, re.IGNORECASE):
                result['platform'] = val
                full_name = re.sub(pattern, '', full_name, flags=re.IGNORECASE).strip()
                break

    for key, val in EDITION_MAP.items():
        if re.search(r'\b' + re.escape(key) + r'\b', full_name, re.IGNORECASE):
            result['edition'] = val
            full_name = re.sub(r'\b' + re.escape(key) + r'\b', '', full_name, flags=re.IGNORECASE).strip()
            break

    if not result['type']:
        lower_clean = full_name.lower()
        if any(word in lower_clean for word in ['collection', 'trilogy', 'bundle', 'pack', '1+2', '2 in 1']):
            result['type'] = 'bundle'
        else:
            result['type'] = 'game'

    result['base_name'] = clean_text(full_name)

    return result


def main():
    rows = conn.execute("SELECT id, name FROM product WHERE name IS NOT NULL").fetchall()
    updated = 0

    for r in rows:
        parsed = parse_name(r['name'])

        region_id = None
        if parsed['region']:
            row = conn.execute(
                "SELECT regionId FROM regions WHERE regionCode = ?",
                (parsed['region'],)
            ).fetchone()
            if row:
                region_id = row['regionId']

        conn.execute("""
            UPDATE product
            SET baseGameName = ?,
                product_type = ?,
                platform = ?,
                edition = ?,
                publisher = ?,
                regionId = ?
            WHERE id = ?
        """, (
            parsed['base_name'],
            parsed['type'],
            parsed['platform'],
            parsed['edition'],
            parsed['publisher'],
            region_id,
            r['id']
        ))
        updated += 1

    conn.commit()
    print(f"Обработано товаров: {updated}")

    print("\nСлучайные примеры после разбора:")
    samples = conn.execute("""
        SELECT offer_id, name, baseGameName, product_type, platform, edition, publisher, regionId
        FROM product
        ORDER BY RANDOM()
        LIMIT 10
    """).fetchall()
    for s in samples:
        print(f"  offer_id: {s['offer_id']}")
        print(f"    name: {s['name']}")
        print(f"    baseGameName: {s['baseGameName']}")
        print(f"    type: {s['product_type']}, platform: {s['platform']}, edition: {s['edition']}")
        print(f"    publisher: {s['publisher']}, regionId: {s['regionId']}")
        print()


if __name__ == "__main__":
    main()