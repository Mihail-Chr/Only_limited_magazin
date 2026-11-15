"""
Тесты для src/parsers/edition_resolver.py (v4.0).

Используют db_conn (тестовая БД с seed).
"""
import pytest

from src.parsers.edition_resolver import resolve_edition


# =====================================================================
# ПОИСК СУЩЕСТВУЮЩЕГО
# =====================================================================

def test_resolve_existing(db_conn):
    """Deluxe есть в seed → находит, не создаёт."""
    edition_id, note = resolve_edition(db_conn, "Deluxe")
    assert edition_id is not None
    assert note is None


def test_resolve_existing_normalized(db_conn):
    """Collectors (без апострофа) находит Collector's."""
    edition_id, note = resolve_edition(db_conn, "Collectors")
    assert edition_id is not None
    assert note is None


def test_resolve_existing_k_o(db_conn):
    """K.O. (с точками) находит K.O."""
    edition_id, note = resolve_edition(db_conn, "K.O.")
    assert edition_id is not None
    assert note is None


def test_resolve_existing_goty(db_conn):
    """GOTY есть в seed."""
    edition_id, note = resolve_edition(db_conn, "GOTY")
    assert edition_id is not None
    assert note is None


# =====================================================================
# СОЗДАНИЕ НОВОГО
# =====================================================================

def test_resolve_creates_new(db_conn):
    """Stellar Steelbook нет в seed → создаёт."""
    edition_id, note = resolve_edition(db_conn, "Stellar Steelbook")
    assert edition_id is not None
    assert note == "edition_created: Stellar Steelbook"

    row = db_conn.execute(
        "SELECT editionName, createdBy, needsReview FROM editionTypes WHERE editionId = ?",
        (edition_id,),
    ).fetchone()
    assert row["editionName"] == "Stellar Steelbook"
    assert row["createdBy"] == "parser"
    assert row["needsReview"] == 1


def test_resolve_creates_as_in_name(db_conn):
    """Имя сохраняется КАК В НАЗВАНИИ (с заглавной)."""
    edition_id, note = resolve_edition(db_conn, "Journey")
    assert edition_id is not None
    row = db_conn.execute(
        "SELECT editionName FROM editionTypes WHERE editionId = ?",
        (edition_id,),
    ).fetchone()
    assert row["editionName"] == "Journey"


def test_resolve_no_duplicate_after_create(db_conn):
    """Повторный вызов — находит созданное, не создаёт дубль."""
    id1, note1 = resolve_edition(db_conn, "Stellar Steelbook")
    id2, note2 = resolve_edition(db_conn, "Stellar Steelbook")
    assert id1 == id2
    assert note1 == "edition_created: Stellar Steelbook"
    assert note2 is None


def test_resolve_duplicate_normalized(db_conn):
    """Stellar-Steelbook (с дефисом) находит созданное Stellar Steelbook."""
    id1, _ = resolve_edition(db_conn, "Stellar Steelbook")
    id2, note2 = resolve_edition(db_conn, "Stellar-Steelbook")
    assert id1 == id2
    assert note2 is None


# =====================================================================
# ПОРОГ (подозрительное — не создаём)
# =====================================================================

def test_resolve_too_short(db_conn):
    """'Xy' (2 символа, нет в seed) — не создаём."""
    edition_id, note = resolve_edition(db_conn, "Xy")
    assert edition_id is None
    assert note == "edition_suspicious: Xy"

def test_resolve_number(db_conn):
    """'123' — число, не создаём."""
    edition_id, note = resolve_edition(db_conn, "123")
    assert edition_id is None
    assert note == "edition_suspicious: 123"


def test_resolve_stop_word(db_conn):
    """'the' — стоп-слово, не создаём."""
    edition_id, note = resolve_edition(db_conn, "the")
    assert edition_id is None
    assert note == "edition_suspicious: the"


def test_resolve_stop_words_only(db_conn):
    """'the and of' — только стоп-слова, не создаём."""
    edition_id, note = resolve_edition(db_conn, "the and of")
    assert edition_id is None
    assert note == "edition_suspicious: the and of"


# =====================================================================
# БЕЗ CONN
# =====================================================================

def test_resolve_no_conn():
    """conn is None → не создаём, note edition_no_conn."""
    edition_id, note = resolve_edition(None, "Stellar Steelbook")
    assert edition_id is None
    assert note == "edition_no_conn: Stellar Steelbook"


# =====================================================================
# ПУСТОЕ ИМЯ
# =====================================================================

def test_resolve_empty(db_conn):
    """Пустое имя → None, None."""
    edition_id, note = resolve_edition(db_conn, "")
    assert edition_id is None
    assert note is None


def test_resolve_none(db_conn):
    """None → None, None."""
    edition_id, note = resolve_edition(db_conn, None)
    assert edition_id is None
    assert note is None