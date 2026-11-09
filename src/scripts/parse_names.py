"""
parse_names.py — разбор названий товаров (v3.6).

Запуск:
    python -m src.scripts.parse_names

Что делает:
- Читает products.name (сырое из API).
- Разбирает через parse_name(name, conn).
- Обновляет products: typeGoodId, baseGameName, platformId,
  editionId, publisherId, regionId, mediaTypeId, restore.

Источник истины — editionTypes в БД (seed).
Парсер НЕ создаёт издания. Не нашёл → editionId = None.
Нормализация агрессивная: lower, '’'→', убрать ' . - _, схлопнуть пробелы.
"""
import sqlite3
import re
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path (для запуска из src/scripts/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db import get_conn


# =====================================================================
# ГЛОБАЛЬНЫЕ СЛОВАРИ (загружаются из БД)
# =====================================================================

_DICTIONARIES = {
    "platforms": {},
    "editions": {},
    "publishers": {},
    "types": {},
    "mediaTypes": {},
    "regions": {},
}

_DICTIONARIES_LOADED = False


def normalize_edition(s: str) -> str:
    """
    Агрессивная нормализация для сравнения изданий.
    lower, '’'/'‘' → ', убрать ' . - _, схлопнуть пробелы.
    """
    if not s:
        return ""
    s = s.lower()
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("'", "").replace(".", "").replace("-", "").replace("_", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_dictionaries(conn=None):
    """Загружает справочники из БД в глобальные словари."""
    global _DICTIONARIES, _DICTIONARIES_LOADED

    own_conn = False
    if conn is None:
        conn = get_conn()
        own_conn = True

    try:
        _DICTIONARIES["platforms"] = {}
        for row in conn.execute(
            "SELECT platformId, platformName, platformVersion FROM platforms"
        ):
            key = f"{row['platformName']} {row['platformVersion']}".lower().strip()
            _DICTIONARIES["platforms"][key] = row["platformId"]

        _DICTIONARIES["editions"] = {}
        for row in conn.execute("SELECT editionId, editionName FROM editionTypes"):
            key = normalize_edition(row["editionName"])
            _DICTIONARIES["editions"][key] = row["editionId"]

        _DICTIONARIES["publishers"] = {}
        for row in conn.execute("SELECT publisherId, publisherName FROM publishers"):
            key = row["publisherName"].lower().strip()
            _DICTIONARIES["publishers"][key] = row["publisherId"]

        _DICTIONARIES["types"] = {}
        for row in conn.execute("SELECT typeGoodId, typeGoodName FROM typeGoods"):
            key = row["typeGoodName"].lower().strip()
            _DICTIONARIES["types"][key] = row["typeGoodId"]

        _DICTIONARIES["mediaTypes"] = {}
        for row in conn.execute("SELECT mediaTypeId, mediaTypeName FROM mediaTypes"):
            key = row["mediaTypeName"].lower().strip()
            _DICTIONARIES["mediaTypes"][key] = row["mediaTypeId"]

        _DICTIONARIES["regions"] = {}
        for row in conn.execute("SELECT regionId, regionCode FROM regions"):
            key = row["regionCode"].lower().strip()
            _DICTIONARIES["regions"][key] = row["regionId"]

        _DICTIONARIES_LOADED = True
    finally:
        if own_conn:
            conn.close()


def ensure_dictionaries(conn=None):
    """Загружает справочники, если ещё не загружены (или передан conn)."""
    if conn is not None:
        load_dictionaries(conn)
    elif not _DICTIONARIES_LOADED:
        load_dictionaries(None)


# =====================================================================
# ХАРДКОД-СЛОВАРИ (fallback, если в БД нет)
# =====================================================================

TYPE_MAP = {
    "видеоигра": "game",
    "стилбук": "steelbook",
    "геймпад": "gamepad",
    "джойстик": "joystick",
    "фигурка": "figure",
    "карточки": "card",
    "значок": "badge",
    "наклейка": "sticker",
    "игрушка": "toy",
    "set": "bundle",
}

PLATFORM_MAP = {
    "nsw": "Nintendo Switch 1",
    "ps4": "PlayStation 4",
    "ps5": "PlayStation 5",
    "ps3": "PlayStation 3",
    "ps2": "PlayStation 2",
    "ps1": "PlayStation 1",
    "xb": "Xbox One",
    "xbs": "Xbox Series",
    "xbx": "Xbox Series",
    "pc": "PC",
    "xbox 360": "Xbox 360",
    "xbox one": "Xbox One",
    "xbox series": "Xbox Series",
    "xbox original": "Xbox Original",
    "nintendo switch": "Nintendo Switch 1",
    "xo": "Xbox One",
    "xs": "Xbox Series",
    "xo/xs": "Xbox One / Series",
    "ps4/ps5": "PlayStation 4/5",
    "nsw/nsw2": "Nintendo Switch 1 / 2",
    "nds": "Nintendo DS",
    "ds": "Nintendo DS",
    "3ds": "Nintendo 3DS",
    "gba": "Game Boy Advance",
    "gbc": "Game Boy Color",
    "gb": "Game Boy",
    "xbox series x": "Xbox Series X",
    "xbox series s": "Xbox Series S",
    "xsx": "Xbox Series X",
    "xss": "Xbox Series S",
    "sega dreamcast": "Sega Dreamcast",
    "dreamcast": "Sega Dreamcast",
    "dc": "Sega Dreamcast",
    "sega saturn": "Sega Saturn",
    "saturn": "Sega Saturn",
}

PLATFORM_KEYS_SORTED = sorted(PLATFORM_MAP.items(), key=lambda kv: -len(kv[0]))

PUBLISHER_MAP = {
    "limited run games": "Limited Run Games",
    "strictly limited games": "Strictly Limited Games",
    "merge games": "Merge Games",
    "nis america": "NIS America",
    "idea factory": "Idea Factory International",
    "super rare games": "Super Rare Games",
    "special reserve games": "Special Reserve Games",
    "eastasiasoft": "Eastasiasoft",
    "play-asia": "Play-Asia",
    "red art games": "Red Art Games",
    "pix'n love": "Pix'n Love",
    "signature edition games": "Signature Edition Games",
    "fangamer": "Fangamer",
    "iam8bit": "iam8bit",
}

REGION_MAP = {
    "ntsc u/c": "US",
    "ntsc": "US",
    "ntsc-j": "JP",
    "ntsc-u": "US",
    "usa": "US",
    "us": "US",
    "pal": "EU",
    "pal-uk": "EU",
    "pal-eu": "EU",
    "eur": "EU",
    "eu": "EU",
    "japan": "JP",
    "j": "JP",
    "jpn": "JP",
    "jp": "JP",
    "asia": "Asia",
    "ru": "RU",
    "rus": "RU",
    "russia": "RU",
    "cn": "CN",
    "chn": "CN",
    "china": "CN",
    "aus": "AUS",
    "australia": "AUS",
    "sa": "SA",
    "de cover": "EU",
}

MEDIA_MAP = {
    "physical": "physical",
    "physical edition": "physical",
    "digital": "digital",
    "digital edition": "digital",
    "download code": "download_code",
    "code in a box": "code_in_a_box",
    "cartridge": "cartridge",
    "disc": "disc",
}


# =====================================================================
# ХЕЛПЕРЫ
# =====================================================================

def clean_text(text):
    text = text.strip()
    text = re.sub(r"[\-:,;]+$", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _find_platform_id(platform_str):
    if not platform_str:
        return None
    key = platform_str.lower().strip()
    return _DICTIONARIES["platforms"].get(key)


def _find_edition_id(edition_str):
    """Ищет editionId по нормализованному ключу. Не создаёт."""
    if not edition_str:
        return None
    key = normalize_edition(edition_str)
    return _DICTIONARIES["editions"].get(key)


def _find_publisher_id(publisher_str):
    if not publisher_str:
        return None
    key = publisher_str.lower().strip()
    return _DICTIONARIES["publishers"].get(key)


def _find_type_id(type_str):
    if not type_str:
        return None
    key = type_str.lower().strip()
    return _DICTIONARIES["types"].get(key)


def _find_media_type_id(media_str):
    if not media_str:
        return None
    key = media_str.lower().strip()
    return _DICTIONARIES["mediaTypes"].get(key)


def _find_region_id(region_str):
    if not region_str:
        return None
    key = region_str.lower().strip()
    return _DICTIONARIES["regions"].get(key)


# =====================================================================
# РАЗБОР НАЗВАНИЯ
# =====================================================================

def extract_media(full_name):
    lower = full_name.lower()
    for key in sorted(MEDIA_MAP, key=lambda k: -len(k)):
        pattern = r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])"
        if re.search(pattern, lower):
            cleaned = re.sub(pattern, "", full_name, flags=re.IGNORECASE).strip()
            return MEDIA_MAP[key], cleaned
    return None, full_name


def _match_edition_candidate(candidate: str):
    """
    Проверяет candidate в _DICTIONARIES["editions"] (нормализованно).
    Возвращает editionId или None.
    """
    key = normalize_edition(candidate)
    if not key:
        return None
    return _DICTIONARIES["editions"].get(key)


def extract_edition(full_name):
    """
    Ищет edition ТОЛЬКО в _DICTIONARIES["editions"] (seed).
    Возвращает (editionId, очищенное имя).
    """
    # 1. Якорь 'Edition'
    for m in re.finditer(r"(?<![a-zA-Z])Edition(?![a-zA-Z])", full_name, re.IGNORECASE):
        start = m.start()
        end = m.end()

        after = full_name[end:].strip()
        after_words = after.split()
        after_word = after_words[0] if after_words else None

        before = full_name[:start].strip()
        words = before.split()

        for n in (4, 3, 2, 1):
            if len(words) < n:
                continue
            candidate_words = words[-n:]
            candidate_before = " ".join(candidate_words)

            # candidate + " Edition" + after_word
            if after_word:
                full_candidate = f"{candidate_before} Edition {after_word}"
                eid = _match_edition_candidate(full_candidate)
                if eid is not None:
                    cand_start = full_name.rfind(candidate_before, 0, start)
                    if cand_start != -1:
                        after_start = end + full_name[end:].find(after_word)
                        after_end = after_start + len(after_word)
                        cleaned = (full_name[:cand_start].rstrip() + " " + full_name[after_end:].lstrip()).strip()
                        return eid, clean_text(cleaned)

            # candidate + " Edition" (без слова после)
            full_candidate_no_after = f"{candidate_before} Edition"
            eid = _match_edition_candidate(full_candidate_no_after)
            if eid is not None:
                cand_start = full_name.rfind(candidate_before, 0, start)
                if cand_start != -1:
                    cleaned = (full_name[:cand_start].rstrip() + " " + full_name[end:].lstrip()).strip()
                    return eid, clean_text(cleaned)

    # 2. Без якоря 'Edition' — все editionName (длинные приоритетнее)
    sorted_editions = sorted(
        _DICTIONARIES["editions"].items(),
        key=lambda kv: -len(kv[0])
    )
    for norm_key, eid in sorted_editions:
        if not norm_key:
            continue
            
        for row_name, row_id in _DICTIONARIES["editions"].items():
            if row_id == eid:
                pattern = re.compile(re.escape(row_name), re.IGNORECASE)
                match = pattern.search(full_name)
                if match:
                    cleaned = (
                        full_name[:match.start()].rstrip() + " " + full_name[match.end():].lstrip()
                    ).strip()
                    return eid, clean_text(cleaned)

    return None, full_name


def extract_platforms(full_name):
    lower = full_name.lower()
    found = []

    for key, val in PLATFORM_KEYS_SORTED:
        if "/" in key and key in lower:
            for part in val.split(" / "):
                if part not in found:
                    found.append(part)

    matched_keys = []
    for key, val in PLATFORM_KEYS_SORTED:
        if "/" in key:
            continue
        if re.search(r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])", lower):
            is_substring = any(key in mk and key != mk for mk in matched_keys)
            if is_substring:
                continue
            matched_keys.append(key)
            if val not in found:
                found.append(val)

    found.sort()
    return found


def parse_name(name, conn=None):
    ensure_dictionaries(conn)

    result = {
        "typeGoodId": None,
        "baseGameName": name or "",
        "platformId": None,
        "editionId": None,
        "publisherId": None,
        "regionId": None,
        "mediaTypeId": None,
        "restore": 0,
    }

    if not name or not isinstance(name, str):
        return result

    full_name = name.replace("’", "'").replace("‘", "'")

    # Хвост описания
    full_name = re.split(r"\s+[—–]\s+", full_name, maxsplit=1)[0].strip()

    # Media
    media_str, full_name = extract_media(full_name)
    if media_str:
        result["mediaTypeId"] = _find_media_type_id(media_str)

    # Платформы
    all_platforms = extract_platforms(full_name)
    if all_platforms:
        platform_str = all_platforms[0] if len(all_platforms) == 1 else " / ".join(all_platforms)
        if "PlayStation 4/5" in platform_str or "ps4/ps5" in full_name.lower():
            platform_str = "PlayStation 4/5"
        if "Xbox One / Series" in platform_str or "xo/xs" in full_name.lower():
            platform_str = "Xbox One / Series"
        if "Nintendo Switch 1 / 2" in platform_str or "nsw/nsw2" in full_name.lower():
            platform_str = "Nintendo Switch 1 / 2"
        result["platformId"] = _find_platform_id(platform_str)

    # Edition
    ed_id, full_name = extract_edition(full_name)
    if ed_id:
        result["editionId"] = ed_id

    # Скобки
    brackets = re.findall(r"\(([^)]+)\)", full_name)
    for bracket_text in brackets:
        lower_bracket = bracket_text.lower()

        # 1. Издатель (сначала!)
        for dict_key, pid in _DICTIONARIES["publishers"].items():
            if dict_key in lower_bracket:
                if result["publisherId"] is None:
                    result["publisherId"] = pid
                # Вырезаем издателя из строки целиком, чтобы не осталось ( Run Games)
                full_name = re.sub(re.escape(bracket_text), "", full_name, flags=re.IGNORECASE)
                full_name = full_name.replace("()", "").strip() # Если скобки опустели
                break

        # 2. Тип
        for key, val in TYPE_MAP.items():
            if re.search(r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])", lower_bracket):
                if result["typeGoodId"] is None:
                    result["typeGoodId"] = _find_type_id(val)
                break

        # 3. Регион
        for key, val in REGION_MAP.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower_bracket):
                if result["regionId"] is None:
                    result["regionId"] = _find_region_id(val)
                break

        # 4. Edition в скобках
        if result["editionId"] is None:
            eid_b = _match_edition_candidate(bracket_text)
            if eid_b is not None:
                result["editionId"] = eid_b

    # Удаляем распознанные скобки
    def _bracket_recognized(bracket_text):
        lb = bracket_text.lower().strip()
        if lb in ("лицензия", "пиратка"):
            result["restore"] = 1
            return True
        if "без игры" in lb or "без диска" in lb:
            return True
        for key in TYPE_MAP:
            if re.search(r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])", lb):
                return True
        if extract_platforms(bracket_text):
            return True
        for key in PUBLISHER_MAP:
            if key in lb:
                return True
        for dict_key in _DICTIONARIES["publishers"]:
            if dict_key in lb:
                return True
        for key in REGION_MAP:
            if re.search(r"\b" + re.escape(key) + r"\b", lb):
                return True
        if _match_edition_candidate(bracket_text) is not None:
            return True
        return False

    def _remove_recognized(match):
        inner = match.group(1)
        if _bracket_recognized(inner):
            return ""
        return match.group(0)

    full_name = re.sub(r"\(([^)]+)\)", _remove_recognized, full_name).strip()
    full_name = re.sub(r"\s+", " ", full_name).strip()

    # Вырезаем платформы
    if result["platformId"] is not None:
        for key, val in PLATFORM_KEYS_SORTED:
            pattern = r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])"
            full_name = re.sub(pattern, "", full_name, flags=re.IGNORECASE)
        full_name = re.sub(r"\s+", " ", full_name).strip()

    # Издатель вне скобок
    lower_name = full_name.lower()
    for key, val in PUBLISHER_MAP.items():
        if key in lower_name:
            if result["publisherId"] is None:
                result["publisherId"] = _find_publisher_id(val)
            full_name = re.sub(re.escape(key), "", full_name, flags=re.IGNORECASE).strip()
            break
    if result["publisherId"] is None:
        for dict_key, pid in _DICTIONARIES["publishers"].items():
            if dict_key in lower_name:
                result["publisherId"] = pid
                full_name = re.sub(re.escape(dict_key), "", full_name, flags=re.IGNORECASE).strip()
                break

    # Тип из первого слова
    if result["typeGoodId"] is None:
        words = full_name.split()
        if words:
            first_word = words[0].lower()
            if first_word in TYPE_MAP:
                result["typeGoodId"] = _find_type_id(TYPE_MAP[first_word])
                full_name = " ".join(words[1:]).strip()

    # Steelbook — только в начале (тип)
    if re.search(r"(?<![a-zA-Z])steelbook(?![a-zA-Z])", full_name, re.IGNORECASE):
        if full_name.lower().strip().startswith("steelbook"):
            if result["typeGoodId"] is None:
                result["typeGoodId"] = _find_type_id("steelbook")
            full_name = re.sub(
                r"(?<![a-zA-Z])steelbook(?![a-zA-Z])", "", full_name, count=1, flags=re.IGNORECASE
            ).strip()
        else:
            has_edition_nearby = re.search(
                r"(?<![a-zA-Z])steelbook\s+edition(?![a-zA-Z])", full_name, re.IGNORECASE
            )
            if not has_edition_nearby:
                if result["editionId"] is None:
                    result["editionId"] = _find_edition_id("Steelbook")
                full_name = re.sub(
                    r"(?<![a-zA-Z])steelbook(?![a-zA-Z])", "", full_name, flags=re.IGNORECASE
                ).strip()

    # Очистка от "Edition" в конце, если не распознали
    full_name = re.sub(r"(?<![a-zA-Z])Edition(?![a-zA-Z])", "", full_name, flags=re.IGNORECASE).strip()
    full_name = re.sub(r"\s+", " ", full_name).strip()

    # Тип по умолчанию (перезаписываем, если есть Bundle/Trilogy)
    lower_clean = full_name.lower()
    if any(word in lower_clean for word in ["trilogy", "bundle", "pack", "1+2", "2 in 1", "combo"]):
        result["typeGoodId"] = _find_type_id("bundle")
    elif result["typeGoodId"] is None:
        result["typeGoodId"] = _find_type_id("game")

    result["baseGameName"] = clean_text(full_name)

    return result


# =====================================================================
# MAIN
# =====================================================================

def main():
    with get_conn() as conn:
        load_dictionaries(conn)

        rows = conn.execute(
            "SELECT productId, name FROM products WHERE name IS NOT NULL"
        ).fetchall()

        updated = 0

        for r in rows:
            parsed = parse_name(r["name"], conn)

            conn.execute(
                """
                UPDATE products SET
                    typeGoodId = ?,
                    baseGameName = ?,
                    platformId = ?,
                    editionId = ?,
                    publisherId = ?,
                    regionId = ?,
                    mediaTypeId = ?,
                    restore = ?,
                    updatedAt = datetime('now')
                WHERE productId = ?
                """,
                (
                    parsed["typeGoodId"],
                    parsed["baseGameName"],
                    parsed["platformId"],
                    parsed["editionId"],
                    parsed["publisherId"],
                    parsed["regionId"],
                    parsed["mediaTypeId"],
                    parsed["restore"],
                    r["productId"],
                ),
            )
            updated += 1

        conn.commit()

    print(f"Обработано товаров: {updated}")

    with get_conn() as conn:
        print("\nСлучайные примеры после разбора:")
        samples = conn.execute("""
            SELECT productId, offerId, name, baseGameName, typeGoodId,
                   platformId, editionId, publisherId, regionId, mediaTypeId, restore
            FROM products
            ORDER BY RANDOM()
            LIMIT 10
        """).fetchall()
        for s in samples:
            print(f"  productId: {s['productId']}, offerId: {s['offerId']}")
            print(f"    name: {s['name']}")
            print(f"    baseGameName: {s['baseGameName']}")
            print(f"    typeGoodId: {s['typeGoodId']}, platformId: {s['platformId']}, editionId: {s['editionId']}")
            print(f"    publisherId: {s['publisherId']}, regionId: {s['regionId']}, mediaTypeId: {s['mediaTypeId']}")
            print(f"    restore: {s['restore']}")
            print()


if __name__ == "__main__":
    main()