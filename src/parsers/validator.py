"""
validator.py — валидация разобранной строки (v4.0).

Возвращает 'ok' или 'needs_review'.

Критерии needs_review:
- game_name пустой или содержит "видеоигра" (регистр не важен).
- platform пустой (для игр — обязательно).
- product_type пустой.
- baseGameName пустой.
- В parseNote есть unknown_bracket или edition_suspicious.
"""
FORBIDDEN_NAME_WORDS = ("видеоигра",)

REQUIRED_FIELDS = ("game_name", "product_type")

PLATFORM_REQUIRED_TYPES = ("game", "bundle")

SUSPICIOUS_NOTES = ("unknown_bracket:", "edition_suspicious:")


def validate_row(row) -> str:
    # 1. Обязательные поля
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            return "needs_review"

    # 2. Платформа обязательна для game/bundle
    product_type = row.get("product_type")
    if product_type in PLATFORM_REQUIRED_TYPES:
        if not row.get("platformId"):
            return "needs_review"

    # 3. baseGameName не пустой
    base = row.get("baseGameName")
    if base is not None and not base:
        return "needs_review"

    # 4. game_name без запрещённых слов
    game_name = str(row.get("game_name") or "").lower()
    if any(word in game_name for word in FORBIDDEN_NAME_WORDS):
        return "needs_review"

    # 5. Подозрительные заметки
    notes = row.get("parseNote") or []
    if isinstance(notes, str):
        notes = [notes]
    for note in notes:
        if any(note.startswith(prefix) for prefix in SUSPICIOUS_NOTES):
            return "needs_review"

    return "ok"