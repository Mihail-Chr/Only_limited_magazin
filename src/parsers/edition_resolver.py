"""
edition_resolver.py — поиск/создание издания в editionTypes (v4.0).

Логика:
1. Ищем точное (нормализованное) в editionTypes.
2. Если нет — проверяем порог (>=3 символа, не число, не стоп-слово).
3. Если порог пройден — создаём (editionName — как в названии, createdBy='parser',
   needsReview=1), возвращаем ID + note "edition_created: <name>".
4. Если порог не пройден — не создаём, возвращаем None + note "edition_suspicious: <name>".
5. conn is None — не создаём, возвращаем None + note "edition_no_conn: <name>".

Каноническое имя при создании — КАК В НАЗВАНИИ (с заглавной, как встретилось).
normalize_edition — только для поиска дублей.
"""
import re

from .normalizer import normalize_edition, normalize_for_match

# Стоп-слова: не создаём издание, если имя состоит только из них.
STOP_WORDS = {
    "edition", "the", "a", "an", "and", "of", "for", "in", "on", "to",
    "для", "и", "в", "на", "с", "по",
}

MIN_LENGTH = 3


def _is_suspicious(name: str) -> bool:
    """Проверяет, подозрительное ли имя издания (не создавать)."""
    normalized = normalize_for_match(name)
    compact = normalized.replace(" ", "")
    if len(compact) < MIN_LENGTH:
        return True
    if re.match(r"^\d+$", compact):
        return True
    words = normalized.split()
    if all(w in STOP_WORDS for w in words):
        return True
    return False

def resolve_edition(conn, edition_name: str):
    """
    Ищет или создаёт издание.

    Args:
        conn: соединение с БД (может быть None для тестов без БД).
        edition_name: строка-кандидат (например, "Collector's", "Stellar Steelbook").

    Returns:
        (edition_id, note) — note или None.
    """
    if not edition_name:
        return None, None

    name = edition_name.strip()
    if not name:
        return None, None

    # Без соединения — не создаём (тесты без БД).
    if conn is None:
        return None, f"edition_no_conn: {name}"

    normalized = normalize_edition(name)

    # 1. Поиск точного (нормализованного) в editionTypes.
    for row in conn.execute("SELECT editionId, editionName FROM editionTypes"):
        if normalize_edition(row["editionName"]) == normalized:
            return row["editionId"], None

    # 2. Порог: подозрительное — не создаём.
    if _is_suspicious(name):
        return None, f"edition_suspicious: {name}"

    # 3. Создаём (как в названии, createdBy='parser', needsReview=1).
    cur = conn.execute(
        """INSERT INTO editionTypes (editionName, createdBy, needsReview, sortOrder)
           VALUES (?, 'parser', 1, 999)""",
        (name,),
    )
    return cur.lastrowid, f"edition_created: {name}"