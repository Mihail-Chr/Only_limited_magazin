"""
Главная функция разбора названия.
"""
import re
from .dictionaries import TYPE_MAP, PLATFORM_KEYS_SORTED, PUBLISHER_MAP, REGION_MAP
from .normalizer import clean_text
from .extractors import extract_media, extract_edition, extract_platforms, set_dictionaries

# Мы будем обращаться к этим словарям через extractors._DICTIONARIES
from src.parsers import extractors

def load_dictionaries(conn):
    """Загружает справочники из БД в глобальные словари."""
    dicts = {
        "platforms": {},
        "editions": {},
        "publishers": {},
        "types": {},
        "mediaTypes": {},
        "regions": {},
    }
    for row in conn.execute("SELECT platformId, platformName, platformVersion FROM platforms"):
        key = f"{row['platformName']} {row['platformVersion']}".lower().strip()
        dicts["platforms"][key] = row["platformId"]

    for row in conn.execute("SELECT editionId, editionName FROM editionTypes"):
        from .normalizer import normalize_edition
        key = normalize_edition(row["editionName"])
        dicts["editions"][key] = row["editionId"]

    for row in conn.execute("SELECT publisherId, publisherName FROM publishers"):
        key = row["publisherName"].lower().strip()
        dicts["publishers"][key] = row["publisherId"]

    for row in conn.execute("SELECT typeGoodId, typeGoodName FROM typeGoods"):
        key = row["typeGoodName"].lower().strip()
        dicts["types"][key] = row["typeGoodId"]

    for row in conn.execute("SELECT mediaTypeId, mediaTypeName FROM mediaTypes"):
        key = row["mediaTypeName"].lower().strip()
        dicts["mediaTypes"][key] = row["mediaTypeId"]

    for row in conn.execute("SELECT regionId, regionCode FROM regions"):
        key = row["regionCode"].lower().strip()
        dicts["regions"][key] = row["regionId"]

    set_dictionaries(dicts)

def parse_name(name, conn=None):
    if conn is not None:
        load_dictionaries(conn)

    if not name or not isinstance(name, str):
        return {
            "typeGoodId": None, "baseGameName": name or "", "platformId": None,
            "editionId": None, "publisherId": None, "regionId": None,
            "mediaTypeId": None, "restore": 0,
        }

    full_name = name.replace("’", "'").replace("‘", "'")
    full_name = re.split(r"\s+[—–]\s+", full_name, maxsplit=1)[0].strip()

    result = {
        "typeGoodId": None, "baseGameName": full_name, "platformId": None,
        "editionId": None, "publisherId": None, "regionId": None,
        "mediaTypeId": None, "restore": 0,
    }

    # Media
    media_str, full_name = extract_media(full_name)
    if media_str:
        result["mediaTypeId"] = extractors._DICTIONARIES["mediaTypes"].get(media_str.lower())

    # Платформы
    all_platforms = extract_platforms(full_name)
    if all_platforms:
        platform_str = all_platforms[0]
        result["platformId"] = extractors._DICTIONARIES["platforms"].get(platform_str.lower())

    # Edition
    ed_id, full_name = extract_edition(full_name)
    if ed_id:
        result["editionId"] = ed_id

    # Скобки
    brackets = re.findall(r"\(([^)]+)\)", full_name)
    for bracket_text in brackets:
        lower_bracket = bracket_text.lower()

        # Издатель
        for dict_key, pid in extractors._DICTIONARIES["publishers"].items():
            if dict_key in lower_bracket:
                if result["publisherId"] is None:
                    result["publisherId"] = pid
                full_name = re.sub(r"\(" + re.escape(bracket_text) + r"\)", "", full_name, flags=re.IGNORECASE).strip()
                break

        # Тип
        for key, val in TYPE_MAP.items():
            if re.search(r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])", lower_bracket):
                if result["typeGoodId"] is None:
                    result["typeGoodId"] = extractors._DICTIONARIES["types"].get(val.lower())
                break

        # Регион
        for key, val in REGION_MAP.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower_bracket):
                if result["regionId"] is None:
                    result["regionId"] = extractors._DICTIONARIES["regions"].get(val.lower())
                break

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
        for dict_key in extractors._DICTIONARIES["publishers"]:
            if dict_key in lb:
                return True
        for key in REGION_MAP:
            if re.search(r"\b" + re.escape(key) + r"\b", lb):
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
                result["publisherId"] = extractors._DICTIONARIES["publishers"].get(val.lower())
            full_name = re.sub(re.escape(key), "", full_name, flags=re.IGNORECASE).strip()
            break

    # Тип из первого слова (например, "Видеоигра")
    if result["typeGoodId"] is None:
        words = full_name.split()
        if words:
            first_word = words[0].lower()
            if first_word in TYPE_MAP:
                result["typeGoodId"] = extractors._DICTIONARIES["types"].get(TYPE_MAP[first_word].lower())
                full_name = " ".join(words[1:]).strip()

    # Steelbook
    if re.search(r"(?<![a-zA-Z])steelbook(?![a-zA-Z])", full_name, re.IGNORECASE):
        if full_name.lower().strip().startswith("steelbook"):
            if result["typeGoodId"] is None:
                result["typeGoodId"] = extractors._DICTIONARIES["types"].get("steelbook")
            full_name = re.sub(r"(?<![a-zA-Z])steelbook(?![a-zA-Z])", "", full_name, count=1, flags=re.IGNORECASE).strip()
        else:
            if result["editionId"] is None:
                result["editionId"] = extractors._DICTIONARIES["editions"].get("steelbook")
            full_name = re.sub(r"(?<![a-zA-Z])steelbook(?![a-zA-Z])", "", full_name, flags=re.IGNORECASE).strip()

    # Очистка от "Edition" в конце
    full_name = re.sub(r"(?<![a-zA-Z])Edition(?![a-zA-Z])", "", full_name, flags=re.IGNORECASE).strip()
    full_name = re.sub(r"\s+", " ", full_name).strip()

    # Тип по умолчанию (Bundle/Trilogy)
    lower_clean = full_name.lower()
    if any(word in lower_clean for word in ["trilogy", "bundle", "pack", "1+2", "2 in 1", "combo"]):
        result["typeGoodId"] = extractors._DICTIONARIES["types"].get("bundle")
    elif result["typeGoodId"] is None:
        result["typeGoodId"] = extractors._DICTIONARIES["types"].get("game")

    result["baseGameName"] = clean_text(full_name)
    return result