import sqlite3
import re

conn = sqlite3.connect('db/only_limited.sqlite3')
conn.row_factory = sqlite3.Row


# ==================== ЗАГРУЗКА СЛОВАРЕЙ ИЗ БД ====================

def _load_from_db():
    """Читает справочники из БД. Если таблица пуста — возвращает {} (будет fallback)."""
    out = {"types": {}, "platforms": {}, "editions": {}, "regions": {}, "publishers": {}}

    try:
        for row in conn.execute('SELECT "typeGoodName" FROM "typeGoods"'):
            out["types"][row[0].lower()] = row[0]
    except sqlite3.OperationalError:
        pass

    try:
        for row in conn.execute('SELECT "platformName", "platformVersion" FROM platforms'):
            name, ver = row[0], row[1]
            # Ключ — "name version" в нижнем регистре: "playstation 4", "nintendo switch 1"
            key = f"{name} {ver}".lower()
            out["platforms"][key] = f"{name} {ver}"
    except sqlite3.OperationalError:
        pass

    try:
        for row in conn.execute('SELECT "editionName" FROM "editionTypes"'):
            out["editions"][row[0].lower()] = row[0]
    except sqlite3.OperationalError:
        pass

    try:
        for row in conn.execute('SELECT "regionCode" FROM regions'):
            out["regions"][row[0].lower()] = row[0]
    except sqlite3.OperationalError:
        pass

    try:
        for row in conn.execute('SELECT "publisherName" FROM publishers'):
            out["publishers"][row[0].lower()] = row[0]
    except sqlite3.OperationalError:
        pass

    return out


DB_MAPS = _load_from_db()


# ==================== ХАРДКОД-СЛОВАРИ (FALLBACK) ====================

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
if DB_MAPS["types"]:
    TYPE_MAP.update(DB_MAPS["types"])

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
    'nintendo switch': 'Nintendo Switch 1',
    'xo': 'Xbox One',
    'xs': 'Xbox Series',
    'xo/xs': 'Xbox One / Xbox Series',
    'ps4/ps5': 'PlayStation 4 / PlayStation 5',
    'nsw/nsw2': 'Nintendo Switch 1 / Nintendo Switch 2',
    'nds': 'Nintendo DS',
    'ds': 'Nintendo DS',
    '3ds': 'Nintendo 3DS',
    'gba': 'Game Boy Advance',
    'gbc': 'Game Boy Color',
    'gb': 'Game Boy',
    'xbox series x': 'Xbox Series X',
    'xbox series s': 'Xbox Series S',
    'xsx': 'Xbox Series X',
    'xss': 'Xbox Series S',
}

if DB_MAPS["platforms"]:
    # Добавляем из БД, но хардкод-сокращения (nsw, ps4) остаются
    for k, v in DB_MAPS["platforms"].items():
        PLATFORM_MAP.setdefault(k, v)

# Сортируем по убыванию длины ключа — чтобы "xbox one" проверялся раньше "xbox"
PLATFORM_KEYS_SORTED = sorted(PLATFORM_MAP.items(), key=lambda kv: -len(kv[0]))

PUBLISHER_MAP = {
    'limited run games': 'Limited Run Games',
    'strictly limited games': 'Strictly Limited Games',
    'merge games': 'Merge Games',
    'nis america': 'NIS America',
    'idea factory': 'Idea Factory International',
    'super rare games': 'Super Rare Games',
    'special reserve games': 'Special Reserve Games',
    'eastasiasoft': 'Eastasiasoft',
    'play-asia': 'Play-Asia',
    'red art games': 'Red Art Games',
    "pix'n love": "Pix'n Love",
    'signature edition games': 'Signature Edition Games',
    'fangamer': 'Fangamer',
    'iam8bit': 'iam8bit',
}
if DB_MAPS["publishers"]:
    for k, v in DB_MAPS["publishers"].items():
        PUBLISHER_MAP.setdefault(k, v)

REGION_MAP = {
    'ntsc u/c': 'US',
    'ntsc': 'US',
    'ntsc-j': 'JP',
    'ntsc-u': 'US',
    'usa': 'US',
    'us': 'US',
    'pal': 'EU',
    'pal-uk': 'EU',
    'pal-eu': 'EU',
    'eur': 'EU',
    'eu': 'EU',
    'japan': 'JP',
    'j': 'JP',
    'jpn': 'JP',
    'jp': 'JP',
    'asia': 'Asia',
    'ru': 'RU',
    'rus': 'RU',
    'russia': 'RU',
    'cn': 'CN',
    'chn': 'CN',
    'china': 'CN',
    'aus': 'AUS',
    'australia': 'AUS',
    'sa': 'SA',
    'de cover': 'EU',
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
    'standard': 'Standard',
    # Новые издания из реальной базы (2026-10-30)
    'classic': 'Classic',
    'definitive': 'Definitive',
    'complete': 'Complete',
    'enhanced': 'Enhanced',
    'extended': 'Extended',
    'exclusive': 'Exclusive',
    'slip case gold': 'Slip Case Gold',
    'france exclusive': 'France Exclusive',
    'картонный бокс': 'Картонный бокс',
    'ultimate 30th anniversary': 'Ultimate 30th Anniversary',
    'essence of art': 'Essence of Art',
    'mirror': 'Mirror',
    "collector's k.o.": "Collector's K.O.",
    'vengeance': 'Vengeance',
    'steelbook premium': 'Steelbook Premium',
    'ultimate steelbook': 'Ultimate Steelbook',
}

# Одиночные слова в скобках, которые считаем вариантом издания (Edition).
# Если слово в этом словаре — вырезаем из base_name, пишем в edition.
# Если нет — оставляем в base_name.
SINGLE_WORD_EDITION_MAP = {
    'platinum': 'Platinum',
    'classic': 'Classic',
    'black': 'Black',
    'tails': 'Tails',
    'knuckles': 'Knuckles',
}

if DB_MAPS["editions"]:
    for k, v in DB_MAPS["editions"].items():
        EDITION_MAP.setdefault(k, v)

MEDIA_MAP = {
    'physical': 'physical',
    'physical edition': 'physical',
    'digital': 'digital',
    'digital edition': 'digital',
    'download code': 'download_code',
    'code in a box': 'code_in_a_box',
    'cartridge': 'cartridge',
    'disc': 'disc',
}


def clean_text(text):
    text = text.strip()
    text = re.sub(r'[\-:,;]+$', '', text).strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_media(full_name):
    """Ищет media-маркеры. Возвращает (media_type, очищенное имя)."""
    lower = full_name.lower()
    # Сначала длинные (code in a box, physical edition), потом короткие
    for key in sorted(MEDIA_MAP, key=lambda k: -len(k)):
        pattern = r'(?<![a-zA-Z])' + re.escape(key) + r'(?![a-zA-Z])'
        if re.search(pattern, lower):
            cleaned = re.sub(pattern, '', full_name, flags=re.IGNORECASE).strip()
            return MEDIA_MAP[key], cleaned
    return None, full_name


def extract_edition(full_name):
    """
    Ищет edition по якорю 'Edition': 1-3 слова до, проверка в EDITION_MAP.
    Возвращает (edition_value, очищенное имя).
    Без fallback по '100%-ным' (цена ошибки высока).
    """
    for m in re.finditer(r'(?<![a-zA-Z])Edition(?![a-zA-Z])', full_name, re.IGNORECASE):
        start = m.start()
        before = full_name[:start].strip()
        words = before.split()
        # Проверяем 1, 2, 3 слова до
        for n in (3, 2, 1):
            if len(words) < n:
                continue
            candidate_words = words[-n:]
            candidate = ' '.join(candidate_words).lower()
            candidate_norm = candidate.replace("’", "'")
            for key, val in EDITION_MAP.items():
                if key.lower().replace("’", "'") == candidate_norm:
                    # Находим НАЧАЛО candidate в full_name (не считаем вручную!)
                    candidate_str = ' '.join(candidate_words)
                    cand_start = full_name.rfind(candidate_str, 0, start)
                    if cand_start == -1:
                        continue
                    cleaned = (full_name[:cand_start].rstrip()
                               + ' ' + full_name[m.end():].lstrip()).strip()
                    return val, clean_text(cleaned)
    return None, full_name


def extract_platforms(full_name):
    """Собирает все платформы (и составные, и одиночные), без дублей."""
    lower = full_name.lower()
    found = []

    # 1. Составные (с "/") — разбиваем на части и добавляем по одной.
    #    Например, 'ps4/ps5' -> ['PlayStation 4', 'PlayStation 5'].
    for key, val in PLATFORM_KEYS_SORTED:
        if '/' in key and key in lower:
            for part in val.split(' / '):
                if part not in found:
                    found.append(part)

    # 2. Одиночные — только если такой платформы ещё нет в found.
    matched_keys = []  # какие ключи уже сработали (для проверки подстрок)
    for key, val in PLATFORM_KEYS_SORTED:
        if '/' in key:
            continue
        if re.search(r'(?<![a-zA-Z])' + re.escape(key) + r'(?![a-zA-Z])', lower):
            # Проверяем: не является ли key подстрокой уже сработавшего ключа
            is_substring = any(key in mk and key != mk for mk in matched_keys)
            if is_substring:
                continue
            matched_keys.append(key)
            if val not in found:
                found.append(val)

    # 3. Сортируем по алфавиту — стабильно и предсказуемо (тест ждёт такой порядок).
    found.sort()

    return found

def parse_name(full_name):
    result = {
        'type': None,
        'base_name': full_name,
        'platform': None,
        'edition': None,
        'publisher': None,
        'region': None,
        'media_type': None,
        'restore': 0,
    }

    # 0. Нормализация апострофов
    full_name = full_name.replace("’", "'").replace("‘", "'")

    # 1. Заглушки
    if "Новый товар" in full_name or full_name.startswith("Товар "):
        result['type'] = 'stub'
        result['base_name'] = full_name
        return result

    # 2. Отрезаем хвост описания после " — " (тире с пробелами)
    #    ВАЖНО: до разбора, чтобы платформа из хвоста не попадала в base_name
    full_name = re.split(r'\s+[—–]\s+', full_name, maxsplit=1)[0].strip()

    # 3. Media (носитель) — до всего остального
    media_type, full_name = extract_media(full_name)
    result['media_type'] = media_type

    # 4. Платформы — собираем ОДИН раз по полному имени (скобки + вне)
    all_platforms = extract_platforms(full_name)
    if all_platforms:
        result['platform'] = ' / '.join(all_platforms)

    # 4b. Скобки — разбираем содержимое (кроме платформы — уже собрана)
    brackets = re.findall(r'\(([^)]+)\)', full_name)
    for bracket_text in brackets:
        lower_bracket = bracket_text.lower()

        # Тип (по границам слова — чтобы 'game' не матчился в 'games')
        for key, val in TYPE_MAP.items():
            if re.search(r'(?<![a-zA-Z])' + re.escape(key) + r'(?![a-zA-Z])', lower_bracket):
                result['type'] = val
                break

        # Издатель
        for key, val in PUBLISHER_MAP.items():
            if key in lower_bracket:
                result['publisher'] = val
                break

        # Регион
        for key, val in REGION_MAP.items():
            if re.search(r'\b' + re.escape(key) + r'\b', lower_bracket):
                result['region'] = val
                break

        # Edition (внутри скобок)
        ed_val, _ = extract_edition(bracket_text)
        if ed_val and not result['edition']:
            result['edition'] = ed_val

        # Одиночное слово в скобках — вариант издания (Platinum, Classic, Black, Tails, Knuckles)
        # Если в SINGLE_WORD_EDITION_MAP — вырезаем (пишем в edition). Если нет — оставляем в base_name.
        if lower_bracket.strip() in SINGLE_WORD_EDITION_MAP and not result['edition']:
            result['edition'] = SINGLE_WORD_EDITION_MAP[lower_bracket.strip()]


    # 5. Удаляем ТОЛЬКО распознанные скобки.
    #    Распознанные: те, где содержимое сработало как тип/платформа/издатель/регион/edition/media
    #    или одиночное слово из SINGLE_WORD_EDITION_MAP.
    #    Нераспознанные — оставляем в base_name.
    def _bracket_recognized(bracket_text):
        lb = bracket_text.lower().strip()

        # Служебные скобки — удаляем всегда: (Лицензия), (Пиратка)
        if lb in ('лицензия', 'пиратка'):
            if lb == 'лицензия':
                result['restore'] = 1
            return True

        # одиночное слово из словаря вариантов
        if lb in SINGLE_WORD_EDITION_MAP:
            return True
        # тип
        for key in TYPE_MAP:
            if re.search(r'(?<![a-zA-Z])' + re.escape(key) + r'(?![a-zA-Z])', lb):
                return True
        # платформа
        if extract_platforms(bracket_text):
            return True
        # издатель
        for key in PUBLISHER_MAP:
            if key in lb:
                return True
        # регион
        for key in REGION_MAP:
            if re.search(r'\b' + re.escape(key) + r'\b', lb):
                return True
        # edition
        ed_val, _ = extract_edition(bracket_text)
        if ed_val:
            return True
        # media (на всякий случай)
        return False

    # Удаляем только распознанные скобки
    def _remove_recognized(match):
        inner = match.group(1)
        if _bracket_recognized(inner):
            return ''
        return match.group(0)  # оставляем как есть

    full_name = re.sub(r'\(([^)]+)\)', _remove_recognized, full_name).strip()
    full_name = re.sub(r'\s+', ' ', full_name).strip()
    # 5b. Вырезаем найденные платформы из текста вне скобок
    if result['platform']:
        for key, val in PLATFORM_KEYS_SORTED:
            pattern = r'(?<![a-zA-Z])' + re.escape(key) + r'(?![a-zA-Z])'
            full_name = re.sub(pattern, '', full_name, flags=re.IGNORECASE)
        full_name = re.sub(r'\s+', ' ', full_name).strip()

    # 6. Издатель вне скобок
    lower_name = full_name.lower()
    for key, val in PUBLISHER_MAP.items():
        if key in lower_name:
            result['publisher'] = val
            full_name = re.sub(re.escape(key), '', full_name, flags=re.IGNORECASE).strip()
            break

    # 7. Тип из первого слова (видеоигра, стилбук, ...)
    if not result['type']:
        words = full_name.split()
        if words:
            first_word = words[0].lower()
            if first_word in TYPE_MAP:
                result['type'] = TYPE_MAP[first_word]
                full_name = ' '.join(words[1:]).strip()

    # 8. Steelbook: тип vs издание
    #    Если "steelbook" есть, но рядом нет "Edition" — это тип
    if re.search(r'(?<![a-zA-Z])steelbook(?![a-zA-Z])', full_name, re.IGNORECASE):
        has_edition_nearby = re.search(
            r'(?<![a-zA-Z])steelbook\s+edition(?![a-zA-Z])', full_name, re.IGNORECASE
        )
        if not has_edition_nearby and not result['type']:
            result['type'] = 'steelbook'
            full_name = re.sub(r'(?<![a-zA-Z])steelbook(?![a-zA-Z])', '', full_name,
                               flags=re.IGNORECASE).strip()
   
    # 10. Edition вне скобок (якорь "Edition")
    if not result['edition']:
        ed_val, full_name = extract_edition(full_name)
        if ed_val:
            result['edition'] = ed_val

    # 11. Тип по умолчанию
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
                regionId = ?,
                media_type = ?,
                restore = ?
            WHERE id = ?
        """, (
            parsed['base_name'],
            parsed['type'],
            parsed['platform'],
            parsed['edition'],
            parsed['publisher'],
            region_id,
            parsed['media_type'],
            parsed['restore'],
            r['id']
        ))
        updated += 1

    conn.commit()
    print(f"Обработано товаров: {updated}")

    print("\nСлучайные примеры после разбора:")
    samples = conn.execute("""
        SELECT offer_id, name, baseGameName, product_type, platform, edition, publisher, regionId, media_type
        FROM product
        ORDER BY RANDOM()
        LIMIT 10
    """).fetchall()
    for s in samples:
        print(f"  offer_id: {s['offer_id']}")
        print(f"    name: {s['name']}")
        print(f"    baseGameName: {s['baseGameName']}")
        print(f"    type: {s['product_type']}, platform: {s['platform']}, edition: {s['edition']}")
        print(f"    publisher: {s['publisher']}, regionId: {s['regionId']}, media: {s['media_type']}")
        print()


if __name__ == "__main__":
    main()