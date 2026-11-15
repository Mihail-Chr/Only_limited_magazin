"""
Тесты для src/parsers/validator.py (v4.0).

Без БД. Чистая функция.
"""
from src.parsers.validator import validate_row


# =====================================================================
# OK
# =====================================================================

def test_valid_row():
    row = {
        "game_name": "God of War",
        "product_type": "game",
        "platformId": 1,
    }
    assert validate_row(row) == "ok"


def test_valid_with_base_name():
    row = {
        "game_name": "God of War",
        "product_type": "game",
        "platformId": 1,
        "baseGameName": "God of War (Sony)",
    }
    assert validate_row(row) == "ok"

def test_valid_with_empty_parse_note():
    row = {
        "game_name": "God of War",
        "product_type": "game",
        "platformId": 1,
        "parseNote": [],
    }
    assert validate_row(row) == "ok"


# =====================================================================
# NEEDS_REVIEW: обязательные поля
# =====================================================================

def test_missing_game_name():
    row = {"game_name": "", "product_type": "game", "platform": "PlayStation 5"}
    assert validate_row(row) == "needs_review"


def test_missing_product_type():
    row = {"game_name": "Game", "product_type": "", "platform": "PlayStation 5"}
    assert validate_row(row) == "needs_review"


def test_missing_platform():
    row = {"game_name": "Game", "product_type": "game", "platform": ""}
    assert validate_row(row) == "needs_review"


def test_none_game_name():
    row = {"game_name": None, "product_type": "game", "platform": "PlayStation 5"}
    assert validate_row(row) == "needs_review"


# =====================================================================
# NEEDS_REVIEW: запрещённые слова
# =====================================================================

def test_game_name_with_videoigra():
    row = {
        "game_name": "Видеоигра Game",
        "product_type": "game",
        "platform": "PlayStation 5",
    }
    assert validate_row(row) == "needs_review"


def test_game_name_case_insensitive():
    row = {
        "game_name": "видеоигра Game",
        "product_type": "game",
        "platform": "PlayStation 5",
    }
    assert validate_row(row) == "needs_review"


# =====================================================================
# NEEDS_REVIEW: baseGameName
# =====================================================================

def test_empty_base_game_name():
    row = {
        "game_name": "Game",
        "product_type": "game",
        "platform": "PlayStation 5",
        "baseGameName": "",
    }
    assert validate_row(row) == "needs_review"


def test_base_game_name_not_present_is_ok():
    row = {
        "game_name": "Game",
        "product_type": "game",
        "platformId": 1,
    }
    assert validate_row(row) == "ok"


# =====================================================================
# NEEDS_REVIEW: parseNote
# =====================================================================

def test_unknown_bracket_needs_review():
    row = {
        "game_name": "Game",
        "product_type": "game",
        "platform": "PlayStation 5",
        "parseNote": ["unknown_bracket: APEX Predator Pack"],
    }
    assert validate_row(row) == "needs_review"


def test_edition_suspicious_needs_review():
    row = {
        "game_name": "Game",
        "product_type": "game",
        "platform": "PlayStation 5",
        "parseNote": ["edition_suspicious: the"],
    }
    assert validate_row(row) == "needs_review"


def test_region_guess_is_ok():
    row = {
        "game_name": "Game",
        "product_type": "game",
        "platformId": 1,
        "parseNote": ["region_guess: Испания→EU"],
    }
    assert validate_row(row) == "ok"


def test_parse_note_as_string():
    """parseNote может быть строкой — гибкость."""
    row = {
        "game_name": "Game",
        "product_type": "game",
        "platform": "PlayStation 5",
        "parseNote": "unknown_bracket: X",
    }
    assert validate_row(row) == "needs_review"

def test_steelbook_without_platform_is_ok():
    row = {
        "game_name": "Steelbook",
        "product_type": "steelbook",
        "platformId": None,
    }
    assert validate_row(row) == "ok"


def test_game_without_platform_needs_review():
    row = {
        "game_name": "Game",
        "product_type": "game",
        "platformId": None,
    }
    assert validate_row(row) == "needs_review"