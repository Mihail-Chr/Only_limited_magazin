"""
Тесты для src/parsers/classifier.py (v4.0).

Без БД. Чистые функции.
"""
from src.parsers.classifier import (
    remove_bundle_phrase,
    extract_generic_edition,
    classify_fragment,
)


# =====================================================================
# remove_bundle_phrase
# =====================================================================

def test_remove_bundle_phrase_with_slash():
    """Another World / Flashback Double Pack → Another World."""
    assert remove_bundle_phrase("Another World / Flashback Double Pack") == "Another World"


def test_remove_bundle_phrase_without_slash():
    """Grand Theft Auto Double Pack → Grand Theft Auto."""
    assert remove_bundle_phrase("Grand Theft Auto Double Pack") == "Grand Theft Auto"


def test_remove_bundle_phrase_trilogy():
    """Gex Trilogy → Gex."""
    assert remove_bundle_phrase("Gex Trilogy") == "Gex"


def test_remove_bundle_phrase_combo():
    """Star Wars Combo → Star Wars."""
    assert remove_bundle_phrase("Star Wars Combo") == "Star Wars"


def test_remove_bundle_phrase_no_marker():
    """Без маркера — не меняет."""
    assert remove_bundle_phrase("God of War") == "God of War"


# =====================================================================
# extract_generic_edition
# =====================================================================

def test_extract_generic_edition_one_word():
    """Baldo: The Guardian Owls - First Edition → First."""
    result = {}
    residual = extract_generic_edition("Baldo: The Guardian Owls - First Edition", result)
    assert result["edition"] == "First"
    assert "Edition" not in residual


def test_extract_generic_edition_two_words():
    """Call of the Sea: Norah's Diary Edition → Norah's Diary."""
    result = {}
    residual = extract_generic_edition("Call of the Sea: Norah's Diary Edition", result)
    assert result["edition"] == "Norah's Diary"


def test_extract_generic_edition_anniversary():
    """Evoland 10th Anniversary Edition → 10th Anniversary."""
    result = {}
    residual = extract_generic_edition("Evoland 10th Anniversary Edition", result)
    assert result["edition"] == "10th Anniversary"


def test_extract_generic_edition_no_edition():
    """Без 'Edition' — не трогает."""
    result = {}
    residual = extract_generic_edition("God of War", result)
    assert "edition" not in result
    assert residual == "God of War"


def test_extract_generic_edition_does_not_overwrite():
    """Если edition уже есть — не перезаписывает."""
    result = {"edition": "Deluxe"}
    extract_generic_edition("Game First Edition", result)
    assert result["edition"] == "Deluxe"


# =====================================================================
# classify_fragment: лицензия
# =====================================================================

def test_classify_license():
    result = {}
    residual = classify_fragment("Black (Лицензия)", result)
    assert result["restore"] == 1
    assert "Лицензия" not in residual


def test_classify_piratka():
    result = {}
    residual = classify_fragment("Black (Пиратка)", result)
    assert result["restore"] == 1


def test_classify_no_license():
    result = {}
    classify_fragment("Black", result)
    assert "restore" not in result


# =====================================================================
# classify_fragment: издатель
# =====================================================================

def test_classify_publisher():
    result = {}
    residual = classify_fragment("Game (Limited Run Games)", result)
    assert result["publisher"] == "Limited Run Games"
    assert "Limited Run Games" not in residual


def test_classify_publisher_not_limited_rare():
    """Limited Rare Games ≠ Limited Run Games."""
    result = {}
    classify_fragment("Game (Limited Rare Games)", result)
    assert result["publisher"] == "Limited Rare Games"


# =====================================================================
# classify_fragment: media
# =====================================================================

def test_classify_media_ekey():
    result = {}
    classify_fragment("Game (e-key)", result)
    assert result["media_type"] == "digital"


def test_classify_media_physical():
    result = {}
    classify_fragment("Game (Physical)", result)
    assert result["media_type"] == "physical"


def test_classify_media_kartridzh():
    result = {}
    classify_fragment("Game (картридж)", result)
    assert result["media_type"] == "cartridge"


# =====================================================================
# classify_fragment: регион
# =====================================================================

def test_classify_region_ntsc():
    result = {}
    classify_fragment("Game (NTSC U/C)", result)
    assert result["region"] == "US"


def test_classify_region_pal():
    result = {}
    classify_fragment("Game (PAL)", result)
    assert result["region"] == "EU"


def test_classify_region_spain_guess():
    """Испания → EU + parseNote region_guess."""
    result = {}
    classify_fragment("Game (Exclusive Испания)", result)
    assert result["region"] == "EU"
    assert any("region_guess" in n for n in result.get("parseNote", []))


# =====================================================================
# classify_fragment: платформа
# =====================================================================

def test_classify_platform_ps4():
    result = {}
    classify_fragment("Game (PS4)", result)
    assert result["platform"] == "PlayStation 4"


def test_classify_platform_xbox_series():
    result = {}
    classify_fragment("Game (Xbox Series)", result)
    assert result["platform"] == "Xbox Series"


def test_classify_platform_sega_mega_drive_not_platform():
    """Sega Mega Drive — часть названия, не платформа."""
    result = {}
    classify_fragment("Sega Mega Drive Game", result)
    assert "platform" not in result


# =====================================================================
# classify_fragment: anniversary
# =====================================================================

def test_classify_anniversary():
    result = {}
    classify_fragment("Evoland 10th Anniversary Edition", result)
    assert result["edition"] == "10th Anniversary"


# =====================================================================
# classify_fragment: edition regex
# =====================================================================

def test_classify_edition_collectors():
    result = {}
    classify_fragment("Game Collector's Edition", result)
    assert result["edition"] == "Collector's"


def test_classify_edition_special():
    result = {}
    classify_fragment("Battle Axe Special Edition", result)
    assert result["edition"] == "Special"


def test_classify_edition_stellar_steelbook():
    result = {}
    classify_fragment("Everspace 2: Stellar Steelbook Edition", result)
    assert result["edition"] == "Stellar Steelbook"


def test_classify_edition_day_one():
    result = {}
    classify_fragment("Gungrave G.O.R.E Day One Edition", result)
    assert result["edition"] == "Day One"


def test_classify_edition_goty():
    result = {}
    classify_fragment("Game GOTY Edition", result)
    assert result["edition"] == "GOTY"


# =====================================================================
# classify_fragment: не перезаписывает
# =====================================================================

def test_classify_does_not_overwrite_edition():
    result = {"edition": "Deluxe"}
    classify_fragment("Game Special Edition", result)
    assert result["edition"] == "Deluxe"