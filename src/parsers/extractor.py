"""
extractor.py — главная функция разбора названия (v4.0).

Два прохода:
1. Скобки (изолированно, через classify_fragment).
2. Остаток (classify_fragment на текст без скобок).

Результат — dict с ID (platformId, editionId, publisherId, regionId,
mediaTypeId, typeGoodId), baseGameName, gameName (чистое), restore, parseNote.

НЕ пишет в БД. Запись — в src/scripts/parse_names.py.
НЕ создаёт издания напрямую — через edition_resolver (с дублями).
"""
import re

from .dictionaries import TYPE_MAP
from .dictionaries import STEELBOOK_MARKERS
from .normalizer import clean_text, clean_tail, detect_product_type, normalize_for_match
from .classifier import classify_fragment, add_note
from .edition_resolver import resolve_edition
from .validator import validate_row


# =====================================================================
# СЛОВАРИ (загружаются из БД)
# =====================================================================

_DICTIONARIES = {
    "platforms": {},   # "playstation 4" → platformId
    "types": {},       # "game" → typeGoodId
    "publishers": {},  # "limited run games" → publisherId
    "regions": {},     # "us" → regionId
    "mediaTypes": {},  # "physical" → mediaTypeId
}


def load_dictionaries(conn):
    """Загружает справочники из БД в _DICTIONARIES."""
    global _DICTIONARIES
    _DICTIONARIES = {
        "platforms": {},
        "types": {},
        "publishers": {},
        "regions": {},
        "mediaTypes": {},
    }

    for row in conn.execute(
        "SELECT platformId, platformName, platformVersion FROM platforms"
    ):
        key = normalize_for_match(f"{row['platformName']} {row['platformVersion']}")
        _DICTIONARIES["platforms"][key] = row["platformId"]

    for row in conn.execute("SELECT typeGoodId, typeGoodName FROM typeGoods"):
        key = normalize_for_match(row["typeGoodName"])
        _DICTIONARIES["types"][key] = row["typeGoodId"]

    for row in conn.execute("SELECT publisherId, publisherName FROM publishers"):
        key = normalize_for_match(row["publisherName"])
        _DICTIONARIES["publishers"][key] = row["publisherId"]

    for row in conn.execute("SELECT regionId, regionCode FROM regions"):
        key = normalize_for_match(row["regionCode"])
        _DICTIONARIES["regions"][key] = row["regionId"]

    for row in conn.execute("SELECT mediaTypeId, mediaTypeName FROM mediaTypes"):
        key = normalize_for_match(row["mediaTypeName"])
        _DICTIONARIES["mediaTypes"][key] = row["mediaTypeId"]


def _find_platform_id(s):
    return _DICTIONARIES["platforms"].get(normalize_for_match(s)) if s else None


def _find_type_id(s):
    return _DICTIONARIES["types"].get(normalize_for_match(s)) if s else None


def _find_publisher_id(s):
    return _DICTIONARIES["publishers"].get(normalize_for_match(s)) if s else None


def _find_region_id(s):
    return _DICTIONARIES["regions"].get(normalize_for_match(s)) if s else None


def _find_media_type_id(s):
    return _DICTIONARIES["mediaTypes"].get(normalize_for_match(s)) if s else None


# =====================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# =====================================================================

def parse_name(name, conn=None):
    """
    Разбирает название товара.

    Args:
        name: строка названия.
        conn: соединение с БД (для справочников и edition_resolver).
              Если None — справочники должны быть загружены заранее
              (через load_dictionaries).

    Returns:
        dict: {
            typeGoodId, baseGameName, platformId, editionId, publisherId,
            regionId, mediaTypeId, restore, parseStatus, parseNote
        }
    """
    if conn is not None:
        load_dictionaries(conn)

    result = {
        "typeGoodId": None,
        "baseGameName": name or "",
        "gameName": name or "",
        "platformId": None,
        "editionId": None,
        "publisherId": None,
        "regionId": None,
        "mediaTypeId": None,
        "restore": 0,
        "parseStatus": "ok",
        "parseNote": [],
    }
    if not name or not isinstance(name, str):
        return result

    # Нормализация входа
    full_name = name.replace("’", "'").replace("‘", "'")
    full_name = re.split(r"\s+[—–]\s+", full_name, maxsplit=1)[0].strip()

    # Тип товара (до разбора)
    product_type = detect_product_type(full_name)
    result["typeGoodId"] = _find_type_id(product_type)

    # =================================================================
    # ПРОХОД 1: СКОБКИ (изолированно)
    # =================================================================
    placeholders = {}

    def replace_group(match):
        content = match.group(1)
        lowered = content.lower()
        # Steelbook Без Игры — тип уже steelbook (detect_product_type), не unknown_bracket
        if any(m in lowered for m in STEELBOOK_MARKERS):
            return " "
        fragment_result = {}
        residual = classify_fragment(content, fragment_result)

        # Переносим найденное в основной result (только если пусто)
        for key, value in fragment_result.items():
            if key == "parseNote":
                for note in value:
                    add_note(result, note)
                continue
            if value and not result.get(key):
                result[key] = value

        # Нераспознанное → placeholder (вернётся в baseGameName)
        if clean_text(residual):
            add_note(result, f"unknown_bracket: {clean_text(residual)}")
            key = f"UNK{len(placeholders)}END"
            placeholders[key] = match.group(0)
            return f" {key} "
        return " "

    text = re.sub(r"\(([^()]*)\)", replace_group, full_name)

    # =================================================================
    # ПРОХОД 2: ОСТАТОК
    # =================================================================
    residual = classify_fragment(text, result)

    # Убираем префикс типа (Видеоигра, Геймпад, ...)
    residual = _remove_type_prefix(residual)

    # baseGameName: остаток + восстановленные placeholder'ы (мусор остаётся)
    base_name = residual
    for key, value in placeholders.items():
        base_name = base_name.replace(key, value)
    base_name = clean_tail(clean_text(base_name))

    # gameName: остаток без placeholder'ов (чистое)
    game_name = residual
    for key in placeholders:
        game_name = game_name.replace(key, " ")
    game_name = clean_tail(clean_text(game_name))

    # =================================================================
    # ID ИЗ СТРОК
    # =================================================================
    if result.get("platform"):
        result["platformId"] = _find_platform_id(result["platform"])
    if result.get("publisher"):
        result["publisherId"] = _find_publisher_id(result["publisher"])
    if result.get("region"):
        result["regionId"] = _find_region_id(result["region"])
    if result.get("media_type"):
        result["mediaTypeId"] = _find_media_type_id(result["media_type"])

    # Издание: поиск/создание через resolver (с дублями)
    if result.get("edition"):
        edition_id, edition_note = resolve_edition(conn, result["edition"])
        result["editionId"] = edition_id
        if edition_note:
            add_note(result, edition_note)

    # =================================================================
    # ЗАВЕРШЕНИЕ
    # =================================================================
    result["baseGameName"] = base_name
    result["gameName"] = game_name

    # Валидация
    row = {
        "game_name": game_name,
        "product_type": product_type,
        "platformId": result["platformId"],
        "typeGoodId": result["typeGoodId"],
        "baseGameName": base_name,
        "parseNote": result["parseNote"],
    }
    result["parseStatus"] = validate_row(row)

    return result


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ
# =====================================================================

def _remove_type_prefix(text):
    """Убирает префикс типа (Видеоигра, Геймпад, ...) из начала строки."""
    lowered = text.lower()
    best = None
    for key in TYPE_MAP:
        if lowered.startswith(key + " "):
            if best is None or len(key) > len(best):
                best = key
    if best:
        return text[len(best):].strip()
    return text