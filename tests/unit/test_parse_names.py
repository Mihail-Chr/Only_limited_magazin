"""
Тесты для src/scripts/parse_names.py (v3.5).

Запуск: pytest tests/unit/test_parse_names.py -v

TDD: тесты описывают ЖЕЛАЕМОЕ поведение.

Справочники — из тестовой БД (seed).
Парсер НЕ создаёт издания. Не нашёл → editionId = None.
"""
import sqlite3
import pytest


TEST_DB_PATH = "db/test_only_limited.sqlite3"


def get_test_conn():
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def get_id(conn, table, code_column, code_value, id_column):
    row = conn.execute(
        f"SELECT {id_column} FROM {table} WHERE {code_column} = ?",
        (code_value,)
    ).fetchone()
    return row[id_column] if row else None


# =====================================================================
# END-TO-END (парсер работает целиком, с conn)
# =====================================================================

def test_parse_name_end_to_end():
    """
    parse_name("Видеоигра Test Game (PS5)") — end-to-end.

    Проверяет: тип (game), платформу (PlayStation 5), baseGameName ("Test Game").
    """
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_type_id = get_id(conn, "typeGoods", "typeGoodName", "game", "typeGoodId")
        row = conn.execute(
            "SELECT platformId FROM platforms WHERE platformName = 'PlayStation' AND platformVersion = '5'"
        ).fetchone()
        expected_platform_id = row["platformId"] if row else None

        result = parse_name("Видеоигра Test Game (PS5)", conn)
    finally:
        conn.close()

    assert result["typeGoodId"] == expected_type_id, \
        f"typeGoodId: ожидалось game ({expected_type_id}), получено {result['typeGoodId']!r}"
    assert result["platformId"] == expected_platform_id, \
        f"platformId: ожидалось PS5 ({expected_platform_id}), получено {result['platformId']!r}"
    assert result["baseGameName"] == "Test Game", \
        f"baseGameName: ожидалось 'Test Game', получено {result['baseGameName']!r}"


# =====================================================================
# ПОЗИТИВНЫЕ — ПОИСК (не создание)
# =====================================================================

def test_parse_name_returns_platform_id_ps4():
    """parse_name("God of War (PS4)") → platformId = ID PlayStation 4."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        row = conn.execute(
            "SELECT platformId FROM platforms WHERE platformName = 'PlayStation' AND platformVersion = '4'"
        ).fetchone()
        expected_id = row["platformId"] if row else None

        result = parse_name("God of War (PS4)", conn)
    finally:
        conn.close()

    assert result["platformId"] == expected_id, \
        f"platformId: ожидалось {expected_id}, получено {result['platformId']!r}"


def test_parse_name_returns_platform_id_ps45():
    """parse_name("God of War (PS4/PS5)") → platformId = ID PlayStation 4/5."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        row = conn.execute(
            "SELECT platformId FROM platforms WHERE platformName = 'PlayStation' AND platformVersion = '4/5'"
        ).fetchone()
        expected_id = row["platformId"] if row else None

        result = parse_name("God of War (PS4/PS5)", conn)
    finally:
        conn.close()

    assert result["platformId"] == expected_id


def test_parse_name_returns_edition_id_deluxe():
    """parse_name("God of War Deluxe Edition (PS4)") → editionId = Deluxe (из seed)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "Deluxe", "editionId")
        result = parse_name("God of War Deluxe Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id


def test_parse_name_returns_edition_id_goty():
    """parse_name("... GOTY Edition") → editionId = GOTY (из seed)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "GOTY", "editionId")
        result = parse_name("God of War GOTY Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id, \
        f"editionId: ожидалось GOTY ({expected_id}), получено {result['editionId']!r}"


def test_parse_name_returns_edition_id_game_of_the_year():
    """parse_name("... Game of the Year Edition") → editionId = Game of the Year (из seed)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "Game of the Year", "editionId")
        result = parse_name("God of War Game of the Year Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id


def test_parse_name_returns_edition_id_first_year():
    """parse_name("... First Year Edition") → editionId = First Year (из seed)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "First Year", "editionId")
        result = parse_name("Game First Year Edition (PS5)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id


def test_parse_name_returns_publisher_id():
    """parse_name("... (Sony Interactive Entertainment)") → publisherId."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(
            conn, "publishers", "publisherName",
            "Sony Interactive Entertainment", "publisherId"
        )
        result = parse_name("God of War (PS4) (Sony Interactive Entertainment)", conn)
    finally:
        conn.close()

    assert result["publisherId"] == expected_id


def test_parse_name_returns_type_good_id():
    """parse_name("God of War (PS4)") → typeGoodId = ID game."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "typeGoods", "typeGoodName", "game", "typeGoodId")
        result = parse_name("God of War (PS4)", conn)
    finally:
        conn.close()

    assert result["typeGoodId"] == expected_id


def test_parse_name_returns_media_type_id():
    """parse_name("... (Physical)") → mediaTypeId = ID physical."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "mediaTypes", "mediaTypeName", "physical", "mediaTypeId")
        result = parse_name("God of War (PS4) (Physical)", conn)
    finally:
        conn.close()

    assert result["mediaTypeId"] == expected_id


def test_parse_name_returns_region_id():
    """parse_name("... (US)") → regionId = ID US."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "regions", "regionCode", "US", "regionId")
        result = parse_name("God of War (PS4) (US)", conn)
    finally:
        conn.close()

    assert result["regionId"] == expected_id


def test_parse_name_returns_base_game_name():
    """parse_name("God of War Deluxe Edition (PS4)") → baseGameName = "God of War"."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        result = parse_name("God of War Deluxe Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["baseGameName"] == "God of War"


def test_parse_name_returns_restore():
    """parse_name("God of War (Лицензия) (PS4)") → restore = 1."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        result = parse_name("God of War (Лицензия) (PS4)", conn)
    finally:
        conn.close()

    assert result["restore"] == 1


def test_parse_name_keeps_unreal():
    """parse_name("Unreal Tournament (PS4)") → baseGameName = "Unreal Tournament"."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        result = parse_name("Unreal Tournament (PS4)", conn)
    finally:
        conn.close()

    assert result["baseGameName"] == "Unreal Tournament"


def test_parse_name_spain_not_region():
    """parse_name("... (Exclusive Испания)") → regionId = None (Испания — страна)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        result = parse_name("Blasphemous Collectors Edition (Exclusive Испания) (NSW/NSW2)", conn)
    finally:
        conn.close()

    assert result["regionId"] is None, \
        f"Испания — не регион, regionId должен быть None, получено {result['regionId']!r}"


def test_parse_name_collection():
    """parse_name("... Anniversary Collection") → editionId = Anniversary Collection."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "Anniversary Collection", "editionId")
        result = parse_name("Street Fighter Anniversary Collection (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id


def test_parse_name_combo_is_bundle():
    """parse_name("... Combo") → typeGoodId = bundle."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "typeGoods", "typeGoodName", "bundle", "typeGoodId")
        result = parse_name("Star Wars: Racer and Commando Combo (PS4/PS5)", conn)
    finally:
        conn.close()

    assert result["typeGoodId"] == expected_id


# =====================================================================
# НЕГАТИВНЫЕ — УСТОЙЧИВОСТЬ
# =====================================================================

def test_parse_name_unknown_edition_returns_none():
    """parse_name("Unknown Edition (PS4)") → editionId = None (не создаём)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        result = parse_name("Unknown Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] is None, \
        f"Неизвестное издание → None, получено {result['editionId']!r}"


def test_parse_name_garbage_does_not_crash():
    """parse_name не падает на «мусоре»."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        result = parse_name("ку-ку товарищ (майор), кто здесь?", conn)
    finally:
        conn.close()

    assert isinstance(result, dict)
    assert "baseGameName" in result
    assert isinstance(result["baseGameName"], str)


def test_parse_name_empty_string_does_not_crash():
    """parse_name не падает на пустой строке."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        result = parse_name("", conn)
    finally:
        conn.close()

    assert isinstance(result, dict)
    assert "baseGameName" in result


def test_parse_name_only_brackets_does_not_crash():
    """parse_name не падает на строке только из скобок."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        result = parse_name("(PS4)", conn)
    finally:
        conn.close()

    assert isinstance(result, dict)
    assert "baseGameName" in result


# =====================================================================
# НОРМАЛИЗАЦИЯ
# =====================================================================

def test_parse_name_edition_with_apostrophe():
    """parse_name("... Collector's Edition") → editionId = Collector's (нормализация)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "Collector's", "editionId")
        result = parse_name("Game Collector's Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id


def test_parse_name_edition_without_apostrophe():
    """parse_name("... Collectors Edition") → editionId = Collector's (нормализация: collectors)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "Collector's", "editionId")
        result = parse_name("Game Collectors Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id, \
        "collectors (без апострофа) должен нормализоваться в collector's"


def test_parse_name_edition_with_dots():
    """parse_name("... K.O. Edition") → editionId = K.O. (нормализация: ko)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "K.O.", "editionId")
        result = parse_name("Game K.O. Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id


def test_parse_name_edition_with_double_spaces():
    """parse_name("... Deluxe  Edition") → editionId = Deluxe (схлопывание пробелов)."""
    from src.scripts.parse_names import parse_name

    conn = get_test_conn()
    try:
        expected_id = get_id(conn, "editionTypes", "editionName", "Deluxe", "editionId")
        result = parse_name("God of War Deluxe  Edition (PS4)", conn)
    finally:
        conn.close()

    assert result["editionId"] == expected_id