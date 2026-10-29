import sqlite3
import re

# Подключаемся к базе (относительный путь, т.к. скрипт запускается из корня)
conn = sqlite3.connect('db/only_limited.sqlite3')
conn.row_factory = sqlite3.Row

# Словарь типов товаров (первое слово в названии OZON -> наш typeGoodName)
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

# Словарь платформ (сокращение в скобках -> полное название)
PLATFORM_MAP = {
    'nsw': 'Nintendo Switch 1',
    'ps4': 'PlayStation 4',
    'ps5': 'PlayStation 5',
    'ps3': 'PlayStation 3',
    'ps2': 'PlayStation 2',
    'ps1': 'PlayStation 1',
    'xb': 'Xbox One',
    'xbs': 'Xbox Series',
    'pc': 'PC',
}

# Словарь известных изданий (то, что мы ожидаем увидеть)
KNOWN_EDITIONS = {
    'deluxe', 'ultimate', 'collector', 'collectors', 'limited', 'steelbook',
    'signature', 'day one', 'gold', 'anniversary', 'special', 'premium',
    'complete', 'definitive', 'remastered', 'goty', 'game of the year'
}

# Слова-маркеры, после которых может идти издание
EDITION_MARKERS = {'edition', 'edition:', 'издание'}

def parse_name(full_name):
    result = {
        'type': None,
        'base_name': full_name,
        'platform': None,
        'edition': None,
    }

    # 1. Тип товара (сначала смотрим в скобки, потом на первое слово)
    lower_name = full_name.lower()
    
    # 1.1. Ищем в скобках (например, "(Steelbook Без Игры)")
    platform_match = re.search(r'\(([^)]+)\)', full_name)
    if platform_match:
        text_in_brackets = platform_match.group(1).lower()
        for key, val in TYPE_MAP.items():
            if key in text_in_brackets:
                result['type'] = val
                # Удаляем скобки с типом из названия
                full_name = re.sub(r'\([^)]+\)', '', full_name).strip()
                break
    
    # 1.2. Если в скобках не нашли, смотрим на первое слово
    if not result['type']:
        words = full_name.split()
        if words:
            first_word = words[0].lower()
            if first_word in TYPE_MAP:
                result['type'] = TYPE_MAP[first_word]
                full_name = ' '.join(words[1:]).strip()

    # 2. Платформа (в скобках в конце) — только если тип ещё не определён
    # (если мы уже удалили скобки с "Steelbook", то платформы там не было)
    if not result['platform']:
        platform_match = re.search(r'\(([^)]+)\)', full_name)
        if platform_match:
            platform_code = platform_match.group(1).strip().lower()
            for key, val in PLATFORM_MAP.items():
                if key in platform_code:
                    result['platform'] = val
                    break
            full_name = re.sub(r'\([^)]+\)', '', full_name).strip()

    # 3. Издание (по слову "Edition" или известным словам)
    words = full_name.split()
    edition_found = False
    
    for i, word in enumerate(words):
        if word.lower() in ('edition', 'edition:'):
            # Берем слово перед "Edition"
            if i > 0:
                prev_word = words[i-1]
                result['edition'] = f"{prev_word} Edition"
                words.pop(i)  # удаляем Edition
                words.pop(i-1)  # удаляем prev_word
                edition_found = True
                break
    
    if not edition_found:
        # Если "Edition" нет, ищем известные слова в конце названия
        if words:
            last_word = words[-1].lower().strip('.,;:')
            if last_word in {'deluxe', 'ultimate', 'collector', 'collectors', 'limited', 'steelbook', 'signature', 'gold', 'anniversary', 'special', 'premium'}:
                result['edition'] = words[-1]
                words.pop()

    # 4. Базовое название (то, что осталось)
    result['base_name'] = ' '.join(words).strip()

    # 5. Определение сборника
    if not result['type']:
        lower_name = result['base_name'].lower()
        if any(word in lower_name for word in ['collection', 'trilogy', 'bundle', 'pack', '1+2', '2 in 1']):
            result['type'] = 'bundle'
        else:
            result['type'] = 'game'
    elif result['type'] == 'game':
        lower_name = result['base_name'].lower()
        if any(word in lower_name for word in ['collection', 'trilogy', 'bundle', 'pack', '1+2', '2 in 1']):
            result['type'] = 'bundle'

    return result

def main():
    rows = conn.execute("SELECT id, name FROM product WHERE name IS NOT NULL").fetchall()
    updated = 0

    for r in rows:
        parsed = parse_name(r['name'])
        
        conn.execute("""
            UPDATE product 
            SET baseGameName = ?,
                product_type = ?,
                platform = ?,
                edition = ?
            WHERE id = ?
        """, (
            parsed['base_name'],
            parsed['type'],
            parsed['platform'],
            parsed['edition'],
            r['id']
        ))
        updated += 1

    conn.commit()
    print(f"Обработано товаров: {updated}")

   # Показываем случайные примеры (чтобы видеть разные товары)
    print("\nСлучайные примеры после разбора:")
    samples = conn.execute("SELECT offer_id, name, baseGameName, product_type, platform, edition FROM product ORDER BY RANDOM() LIMIT 10").fetchall()
    for s in samples:
        print(f"  offer_id: {s['offer_id']}")
        print(f"    name: {s['name']}")
        print(f"    baseGameName: {s['baseGameName']}")
        print(f"    type: {s['product_type']}, platform: {s['platform']}, edition: {s['edition']}")
        print()

if __name__ == "__main__":
    main()