"""
Тесты для src/parsers/normalizer.py (v4.0).

Без БД. Чистые функции.
"""
import pytest

from src.parsers.normalizer import (
    clean_text,
    clean_tail,
    detect_product_type,
    normalize_edition,
    normalize_for_match,
)


# =====================================================================
# clean_text
# =====================================================================

def test_clean_text_removes_extra_spaces():
    assert clean_text("  Видеоигра   Black  ") == "Видеоигра Black"


def test_clean_text_nbsp():
    assert clean_text("Game\u00a0Name") == "Game Name"


def test_clean_text_none():
    assert clean_text(None) == ""


# =====================================================================
# clean_tail
# =====================================================================

def test_clean_tail_removes_trailing_dash():
    assert clean_tail("Baldo: The Guardian Owls -") == "Baldo: The Guardian Owls"


def test_clean_tail_removes_trailing_colon():
    assert clean_tail("Game:") == "Game"


def test_clean_tail_removes_trailing_slash():
    assert clean_tail("Game /") == "Game"


def test_clean_tail_keeps_inner_dash():
    assert clean_tail("Spider-Man") == "Spider-Man"


# =====================================================================
# detect_product_type
# =====================================================================

def test_detect_product_type_game():
    assert detect_product_type("Видеоигра Black") == "game"


def test_detect_product_type_gamepad():
    assert detect_product_type("Nintendo Геймпад Switch Pro Controller") == "gamepad"


def test_detect_product_type_bundle():
    assert detect_product_type("Видеоигра Game Trilogy") == "bundle"


def test_detect_product_type_steelbook():
    assert detect_product_type("Видеоигра Game (Steelbook Без Игры)") == "steelbook"


def test_detect_product_type_default():
    assert detect_product_type("Неизвестный товар") == "game"


# =====================================================================
# normalize_edition (для дублей)
# =====================================================================

def test_normalize_edition_apostrophe():
    assert normalize_edition("Collector's") == "collectors"


def test_normalize_edition_without_apostrophe():
    assert normalize_edition("Collectors") == "collectors"


def test_normalize_edition_dots():
    assert normalize_edition("K.O.") == "ko"


def test_normalize_edition_dashes():
    assert normalize_edition("Stellar-Steelbook") == "stellarsteelbook"


def test_normalize_edition_double_spaces():
    assert normalize_edition("Deluxe  Edition") == "deluxeedition"

def test_normalize_edition_empty():
    assert normalize_edition("") == ""


# =====================================================================
# normalize_for_match (для платформ/регионов/издателей)
# =====================================================================

def test_normalize_for_match_lower():
    assert normalize_for_match("PlayStation 4") == "playstation 4"


def test_normalize_for_match_spaces():
    assert normalize_for_match("  Limited   Run  Games ") == "limited run games"


def test_normalize_for_match_empty():
    assert normalize_for_match("") == ""