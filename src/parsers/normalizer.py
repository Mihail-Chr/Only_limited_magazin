"""
normalizer.py — нормализация текста и определение типа товара (v4.0).

Функции:
- clean_text: схлопывание пробелов, \u00a0 → пробел.
- clean_tail: удаление завершающих разделителей (-, –, —, :, ;, ,, /).
- detect_product_type: steelbook → bundle → TYPE_MAP → game.
- normalize_edition: агрессивная нормализация для поиска дублей изданий.
- normalize_for_match: нормализация для сравнения платформ/регионов/издателей.
"""
import re

from .dictionaries import (
    TYPE_MAP,
    DEFAULT_PRODUCT_TYPE,
    BUNDLE_MARKERS,
    STEELBOOK_MARKERS,
)


# =====================================================================
# БАЗОВАЯ ОЧИСТКА
# =====================================================================

def clean_text(value) -> str:
    """Схлопывает пробелы, убирает \u00a0. None → ''."""
    if value is None:
        return ""
    text = str(value).replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_tail(text: str) -> str:
    """Убирает завершающие разделители: - – — : ; , /."""
    text = clean_text(text)
    return re.sub(r"\s*[-\u2013\u2014:;,/]\s*$", "", text).strip()


# =====================================================================
# ТИП ТОВАРА
# =====================================================================

def detect_product_type(text: str) -> str:
    """
    Определяет тип товара.

    Порядок:
    1. STEELBOOK_MARKERS (steelbook без игры) → 'steelbook'.
    2. BUNDLE_MARKERS (bundle, trilogy, double pack, combo, 1+2, 2 in 1) → 'bundle'.
    3. TYPE_MAP по первому вхождению (видеоигра, геймпад, ...).
    4. DEFAULT_PRODUCT_TYPE ('game').
    """
    lowered = clean_text(text).lower()

    for marker in STEELBOOK_MARKERS:
        if marker in lowered:
            return "steelbook"

    for marker in BUNDLE_MARKERS:
        if marker in lowered:
            return "bundle"

    best = None
    for key, value in TYPE_MAP.items():
        position = lowered.find(key)
        if position != -1 and (best is None or position < best[0]):
            best = (position, value)
    return best[1] if best else DEFAULT_PRODUCT_TYPE


# =====================================================================
# НОРМАЛИЗАЦИЯ ДЛЯ ПОИСКА ДУБЛЕЙ / СРАВНЕНИЯ
# =====================================================================

def normalize_edition(s: str) -> str:
    """
    Агрессивная нормализация для поиска дублей изданий.

    - lower
    - ’ / ‘ → '
    - убрать ' . - _
    - схлопнуть пробелы

    Пример: "Collector's" → "collectors", "K.O." → "ko".
    Каноническое имя при создании — как в названии (эта функция — только для сравнения).
    """
    if not s:
        return ""
    s = str(s).lower()
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("'", "").replace(".", "").replace("-", "").replace("_", "")
    s = re.sub(r"\s+", "", s)
    return s


def normalize_for_match(s: str) -> str:
    """
    Нормализация для сравнения платформ/регионов/издателей.

    - lower
    - схлопнуть пробелы
    - strip
    """
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower())