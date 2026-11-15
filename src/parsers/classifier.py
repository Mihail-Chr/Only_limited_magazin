"""
classifier.py — классификация фрагментов названия (v4.0).

Функции:
- classify_fragment: лицензия → издатель → media → регион → платформа →
  anniversary → edition regex → generic edition.
- extract_generic_edition: эвристика издания (якорь "Edition").
- remove_bundle_phrase: удаление маркера bundle (с /-альтернативой).

Принципы:
- Пишем в result только если поле пустое (первое совпадение важнее).
- НЕ создаём издания: result["edition"] — строка-кандидат (ID — в edition_resolver).
- region_guess (Испания → EU) и unknown_bracket пишем в result["parseNote"].
"""
import re


from .dictionaries import (
    LICENSE_RE,
    MEDIA_MAP,
    MEDIA_RE,
    PLATFORM_ALIASES,
    PLATFORM_RE,
    PUBLISHER_RES,
    REGIONS,
    REGION_RE,
    EDITION_RES,
    BUNDLE_MARKERS,
)
from .normalizer import clean_text


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ
# =====================================================================

def find_spans(regex, text):
    """Возвращает список (start, end) для всех совпадений regex."""
    return [(m.start(), m.end()) for m in regex.finditer(text)]


def remove_spans(text, spans):
    """Удаляет указанные спаны (с конца, чтобы не сбить индексы)."""
    for start, end in sorted(spans, reverse=True):
        text = text[:start] + " " + text[end:]
    return clean_text(text)


def add_note(result, note):
    """Добавляет заметку в result['parseNote'] (список)."""
    notes = result.setdefault("parseNote", [])
    if note not in notes:
        notes.append(note)


# =====================================================================
# BUNDLE
# =====================================================================

def remove_bundle_phrase(text):
    """
    Удаляет маркер bundle.

    Если перед маркером есть альтернатива через '/', удаляет и её:
    "Another World / Flashback Double Pack" → "Another World".
    """
    slash_pattern = re.compile(
        r"\s*/\s*[^/\n]*\s*(?:bundle|trilogy|double pack|combo|1\+2|2 in 1)\b",
        re.IGNORECASE,
    )
    slash_match = slash_pattern.search(text)
    if slash_match:
        return clean_text(text[:slash_match.start()] + " " + text[slash_match.end():])

    for marker in BUNDLE_MARKERS:
        pattern = re.compile(r"\b" + re.escape(marker) + r"\b", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return clean_text(text[:match.start()] + " " + text[match.end():])
    return clean_text(text)


# =====================================================================
# ЭВРИСТИКА ИЗДАНИЯ (ЯКОРЬ "EDITION")
# =====================================================================

ANNIVERSARY_EDITION_RE = re.compile(
    r"\b(\d+(?:st|nd|rd|th)?\s+anniversary)\s+edition\b",
    re.IGNORECASE,
)


def extract_generic_edition(work, result):
    """
    Эвристика издания по последнему "Edition".

    - Без разделителя: 1 слово до "Edition".
    - После ':' / '-' / '–' / '—': до 3 слов.
    - Если перед "Edition" число + слово (10th Anniversary, 30th): 2 слова.

    Пишет result["edition"] (если пусто) и вырезает фразу.
    НЕ создаёт издание (ID — в edition_resolver).
    """
    matches = list(re.finditer(r"\s+edition\b", work, re.IGNORECASE))
    if not matches:
        return work

    match = matches[-1]
    prefix = work[:match.start()]
    separator_positions = [
        prefix.rfind(separator)
        for separator in (":", "-", "\u2013", "\u2014")
    ]
    separator_position = max(separator_positions)

    if separator_position != -1:
        segment = prefix[separator_position + 1:].strip()
        words = segment.split()
        qualifier = " ".join(words[-3:]) if len(words) >= 3 else segment
    else:
        words = prefix.split()
        qualifier = words[-1] if words else ""
        if len(words) >= 2 and re.match(r"^\d+(?:st|nd|rd|th)?$", words[-2], re.IGNORECASE):
            qualifier = " ".join(words[-2:])

    if qualifier:
        if not result.get("edition"):
            result["edition"] = clean_text(qualifier)
        start = work.rfind(qualifier, 0, match.start())
        if start != -1:
            work = work[:start] + " " + work[match.end():]

    return clean_text(work)


# =====================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# =====================================================================

def classify_fragment(text, result):
    """
    Классифицирует фрагмент названия.

    Порядок: лицензия → издатель → media → регион → платформа →
    anniversary → edition regex → generic edition.

    Пишет в result (только если поле пустое).
    Возвращает остаток (нераспознанное).
    """
    work = clean_text(text)
    work = remove_bundle_phrase(work)

    # 1. Лицензия / Пиратка
    license_spans = find_spans(LICENSE_RE, work)
    if license_spans:
        result["restore"] = 1
        work = remove_spans(work, license_spans)

    # 2. Media
    media_spans = find_spans(MEDIA_RE, work)
    if media_spans:
        first = work[media_spans[0][0]:media_spans[0][1]].lower()
        if not result.get("media_type"):
            result["media_type"] = MEDIA_MAP[first]
        work = remove_spans(work, media_spans)

    # 3. Регион (ищем везде; Испания → EU + parseNote)
    region_spans = find_spans(REGION_RE, work)
    if region_spans:
        first = work[region_spans[0][0]:region_spans[0][1]]
        first_low = first.lower()
        if not result.get("region"):
            result["region"] = REGIONS[first_low]
            if first_low == "испания":
                add_note(result, f"region_guess: {first}→{REGIONS[first_low]}")
        work = remove_spans(work, region_spans)

    # 4. Платформа (ищем везде; PLATFORM_EXCLUDE уже исключён в PLATFORM_RE)
    platform_spans = find_spans(PLATFORM_RE, work)
    if platform_spans:
        first = work[platform_spans[0][0]:platform_spans[0][1]].lower()
        if not result.get("platform"):
            result["platform"] = PLATFORM_ALIASES[first]
        work = remove_spans(work, platform_spans)

    # 5. Издатель (точное совпадение, границы слов)
    for publisher, regex in PUBLISHER_RES:
        spans = find_spans(regex, work)
        if spans:
            if not result.get("publisher"):
                result["publisher"] = publisher
            work = remove_spans(work, spans)

    # 6. Anniversary (10th Anniversary Edition)
    anniversary = ANNIVERSARY_EDITION_RE.search(work)
    if anniversary:
        if not result.get("edition"):
            result["edition"] = clean_text(anniversary.group(1))
        work = remove_spans(work, [anniversary.span()])

    # 7. Edition regex (EDITION_RULES)
    for regex, canonical in EDITION_RES:
        spans = find_spans(regex, work)
        if spans:
            if not result.get("edition"):
                result["edition"] = canonical
            work = remove_spans(work, spans)

    # 8. Generic edition (эвристика, якорь "Edition")
    work = extract_generic_edition(work, result)

    return work