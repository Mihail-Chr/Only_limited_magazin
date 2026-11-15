"""
Тесты для src/parsers/extractor.py (v4.0).

Используют db_conn (тестовая БД с seed).
Проверяют parse_name end-to-end: ID, baseGameName, gameName, parseStatus, parseNote.

Адаптация внешних 29 тестов (строки → ID) + наши кейсы.
"""
import pytest

from src.parsers.extractor import parse_name


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ
# =====================================================================

def get_platform_id(conn, name, version):
    row = conn.execute(
        "SELECT platformId FROM platforms WHERE platformName = ? AND platformVersion = ?",
        (name, version),
    ).fetchone()
    return row["platformId"] if row else None


def get_type_id(conn, name):
    row = conn.execute(
        "SELECT typeGoodId FROM typeGoods WHERE typeGoodName = ?", (name,)
    ).fetchone()
    return row["typeGoodId"] if row else None


def get_edition_id(conn, name):
    row = conn.execute(
        "SELECT editionId FROM editionTypes WHERE editionName = ?", (name,)
    ).fetchone()
    return row["editionId"] if row else None


def get_publisher_id(conn, name):
    row = conn.execute(
        "SELECT publisherId FROM publishers WHERE publisherName = ?", (name,)
    ).fetchone()
    return row["publisherId"] if row else None


def get_region_id(conn, code):
    row = conn.execute(
        "SELECT regionId FROM regions WHERE regionCode = ?", (code,)
    ).fetchone()
    return row["regionId"] if row else None


def get_media_id(conn, name):
    row = conn.execute(
        "SELECT mediaTypeId FROM mediaTypes WHERE mediaTypeName = ?", (name,)
    ).fetchone()
    return row["mediaTypeId"] if row else None

def test_parse_game_without_platform_needs_review(db_conn):
    """Игра без платформы → needs_review."""
    result = parse_name("Видеоигра Game", db_conn)
    assert result["platformId"] is None
    assert result["parseStatus"] == "needs_review"


def test_parse_steelbook_without_platform_ok(db_conn):
    """Steelbook без игры без платформы → ok (платформа не обязательна)."""
    result = parse_name("Стилбук Steelbook Без Игры", db_conn)
    assert result["platformId"] is None
    assert result["parseStatus"] == "ok"


def test_parse_steelbook_without_unknown_bracket(db_conn):
    """(Steelbook Без Игры) → не unknown_bracket."""
    result = parse_name("Видеоигра Game (Steelbook Без Игры)", db_conn)
    assert not any("unknown_bracket" in n for n in result["parseNote"])


def test_parse_sega_dreamcast_is_platform(db_conn):
    """Sega Dreamcast → платформа, не издатель Sega."""
    result = parse_name("Видеоигра Game (Sega Dreamcast)", db_conn)
    assert result["platformId"] == get_platform_id(db_conn, "Sega", "Dreamcast")
    assert result["publisherId"] is None

# =====================================================================
# END-TO-END: ТИП, ПЛАТФОРМА, BASE_NAME
# =====================================================================

def test_parse_end_to_end(db_conn):
    """Видеоигра Test Game (PS5) → game, PlayStation 5, Test Game."""
    result = parse_name("Видеоигра Test Game (PS5)", db_conn)
    assert result["typeGoodId"] == get_type_id(db_conn, "game")
    assert result["platformId"] == get_platform_id(db_conn, "PlayStation", "5")
    assert result["baseGameName"] == "Test Game"
    assert result["gameName"] == "Test Game"
    assert result["parseStatus"] == "ok"


def test_parse_platform_ps4(db_conn):
    """God of War (PS4) → PlayStation 4."""
    result = parse_name("God of War (PS4)", db_conn)
    assert result["platformId"] == get_platform_id(db_conn, "PlayStation", "4")


def test_parse_platform_ps45_chooses_ps4(db_conn):
    """PS4/PS5 → меньшая (PlayStation 4)."""
    result = parse_name("God of War (PS4/PS5)", db_conn)
    assert result["platformId"] == get_platform_id(db_conn, "PlayStation", "4")


def test_parse_platform_xbox_series(db_conn):
    """Xbox Series → Xbox Series (platformName='Xbox', platformVersion='Series')."""
    result = parse_name("Game (Xbox Series)", db_conn)
    assert result["platformId"] == get_platform_id(db_conn, "Xbox", "Series")


def test_parse_platform_1_2_switch_not_platform(db_conn):
    """1-2-Switch — не платформа."""
    result = parse_name("Видеоигра 1-2-Switch (NSW/NSW2)", db_conn)
    assert result["platformId"] == get_platform_id(db_conn, "Nintendo Switch", "1")
    assert "1-2-Switch" in result["baseGameName"]


# =====================================================================
# END-TO-END: ЛИЦЕНЗИЯ / ПИРАТКА
# =====================================================================

def test_parse_license(db_conn):
    """(Лицензия) → restore=1."""
    result = parse_name("Видеоигра Black PS2 (Лицензия)", db_conn)
    assert result["restore"] == 1
    assert result["platformId"] == get_platform_id(db_conn, "PlayStation", "2")


def test_parse_piratka(db_conn):
    """(Пиратка) → restore=1."""
    result = parse_name("Видеоигра Black (Пиратка) (PS4)", db_conn)
    assert result["restore"] == 1


def test_parse_no_license(db_conn):
    """Без лицензии → restore=0."""
    result = parse_name("God of War (PS4)", db_conn)
    assert result["restore"] == 0


# =====================================================================
# END-TO-END: ИЗДАТЕЛЬ
# =====================================================================

def test_parse_publisher(db_conn):
    """(Limited Run Games) → publisherId."""
    result = parse_name(
        "Видеоигра 2064: Read Only Memories Integral (Limited Run Games) (NSW/NSW2)",
        db_conn,
    )
    assert result["publisherId"] == get_publisher_id(db_conn, "Limited Run Games")
    assert result["platformId"] == get_platform_id(db_conn, "Nintendo Switch", "1")


def test_parse_publisher_not_limited_rare(db_conn):
    """Limited Rare Games ≠ Limited Run Games."""
    result = parse_name("Game (Limited Rare Games) (PS4)", db_conn)
    assert result["publisherId"] == get_publisher_id(db_conn, "Limited Rare Games")


# =====================================================================
# END-TO-END: ИЗДАНИЕ
# =====================================================================

def test_parse_edition_collectors(db_conn):
    """Collector's Edition → Collector's."""
    result = parse_name("Видеоигра Yuppie Psycho Collector's Edition (NSW/NSW2)", db_conn)
    assert result["editionId"] == get_edition_id(db_conn, "Collector's")


def test_parse_edition_generic_first(db_conn):
    """First Edition → First (создаётся, т.к. нет в seed)."""
    result = parse_name("Видеоигра Baldo: The Guardian Owls - First Edition", db_conn)
    # First — нет в seed, создастся (порог пройден: 5 символов)
    assert result["editionId"] is not None
    assert any("edition_created" in n for n in result["parseNote"])


def test_parse_edition_generic_crewmate(db_conn):
    """Crewmate Edition → Crewmate (создаётся)."""
    result = parse_name("Видеоигра Among Us: Crewmate Edition (PS5)", db_conn)
    assert result["editionId"] is not None
    assert any("edition_created" in n for n in result["parseNote"])


def test_parse_edition_suspicious_not_created(db_conn):
    """Подозрительное издание (короткое) — не создаётся."""
    result = parse_name("Видеоигра Game Ab Edition (PS5)", db_conn)
    # "Ab" — 2 символа, подозрительное
    assert any("edition_suspicious" in n for n in result["parseNote"])
    assert result["parseStatus"] == "needs_review"


def test_parse_edition_existing_deluxe(db_conn):
    """Deluxe Edition → Deluxe (из seed)."""
    result = parse_name("God of War Deluxe Edition (PS4)", db_conn)
    assert result["editionId"] == get_edition_id(db_conn, "Deluxe")


def test_parse_edition_anniversary(db_conn):
    """10th Anniversary Edition → 10th Anniversary (есть в seed)."""
    result = parse_name("Видеоигра Evoland 10th Anniversary Edition (PS4/PS5)", db_conn)
    assert result["editionId"] is not None

# =====================================================================
# END-TO-END: РЕГИОН / MEDIA
# =====================================================================

def test_parse_region_ntsc(db_conn):
    """(NTSC U/C) → US."""
    result = parse_name("Видеоигра Game (NTSC U/C) (PS4)", db_conn)
    assert result["regionId"] == get_region_id(db_conn, "US")


def test_parse_region_spain_guess(db_conn):
    """Испания → EU + region_guess."""
    result = parse_name(
        "Blasphemous Collectors Edition (Exclusive Испания) (NSW/NSW2)", db_conn
    )
    assert result["regionId"] == get_region_id(db_conn, "EU")
    assert any("region_guess" in n for n in result["parseNote"])


def test_parse_media_ekey(db_conn):
    """(e-key) → digital."""
    result = parse_name("Видеоигра Game (e-key)", db_conn)
    assert result["mediaTypeId"] == get_media_id(db_conn, "digital")


# =====================================================================
# END-TO-END: BUNDLE
# =====================================================================

def test_parse_bundle_double_pack(db_conn):
    """Double Pack → bundle."""
    result = parse_name(
        "Видеоигра Another World / Flashback Double Pack (NSW/NSW2)", db_conn
    )
    assert result["typeGoodId"] == get_type_id(db_conn, "bundle")


def test_parse_bundle_trilogy(db_conn):
    """Trilogy → bundle."""
    result = parse_name("Видеоигра Gex Trilogy Event Exclusive (Limited Run Games) (XBX)", db_conn)
    assert result["typeGoodId"] == get_type_id(db_conn, "bundle")


# =====================================================================
# END-TO-END: UNKNOWN BRACKET
# =====================================================================

def test_parse_unknown_bracket(db_conn):
    """(APEX Predator Pack) → unknown_bracket в parseNote, в baseGameName остаётся."""
    result = parse_name("Видеоигра Game (APEX Predator Pack) (PS5)", db_conn)
    assert result["platformId"] == get_platform_id(db_conn, "PlayStation", "5")
    assert any("unknown_bracket" in n for n in result["parseNote"])
    assert "APEX Predator Pack" in result["baseGameName"]
    assert result["parseStatus"] == "needs_review"


# =====================================================================
# END-TO-END: БЕЗ CONN
# =====================================================================

def test_parse_without_conn_no_edition_create():
    """conn is None → издание не создаётся, note edition_no_conn."""
    result = parse_name("Game Stellar Steelbook Edition (PS5)", None)
    assert result["editionId"] is None
    assert any("edition_no_conn" in n for n in result["parseNote"])


# =====================================================================
# НЕГАТИВНЫЕ: УСТОЙЧИВОСТЬ
# =====================================================================

def test_parse_empty_string(db_conn):
    """Пустая строка — не падает."""
    result = parse_name("", db_conn)
    assert isinstance(result, dict)
    assert "baseGameName" in result


def test_parse_none(db_conn):
    """None — не падает."""
    result = parse_name(None, db_conn)
    assert isinstance(result, dict)


def test_parse_garbage(db_conn):
    """«Мусор» — не падает."""
    result = parse_name("ку-ку товарищ (майор), кто здесь?", db_conn)
    assert isinstance(result, dict)
    assert "baseGameName" in result


def test_parse_only_brackets(db_conn):
    """Только скобки — не падает."""
    result = parse_name("(PS4)", db_conn)
    assert isinstance(result, dict)