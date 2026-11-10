"""
Функции извлечения (платформы, издания, медиа).
"""
import re
from .dictionaries import PLATFORM_MAP, PLATFORM_KEYS_SORTED, MEDIA_MAP
from .normalizer import normalize_edition, clean_text

_DICTIONARIES = {
    "platforms": {},
    "editions": {},
    "publishers": {},
    "types": {},
    "mediaTypes": {},
    "regions": {},
}

def set_dictionaries(dicts):
    """Устанавливает глобальные словари из БД."""
    global _DICTIONARIES
    _DICTIONARIES = dicts

def _match_edition_candidate(candidate: str):
    """Проверяет candidate в словаре изданий (нормализованно)."""
    key = normalize_edition(candidate)
    if not key:
        return None
    return _DICTIONARIES["editions"].get(key)

def extract_media(full_name):
    lower = full_name.lower()
    for key in sorted(MEDIA_MAP, key=lambda k: -len(k)):
        pattern = r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])"
        if re.search(pattern, lower):
            cleaned = re.sub(pattern, "", full_name, flags=re.IGNORECASE).strip()
            return MEDIA_MAP[key], cleaned
    return None, full_name

def extract_edition(full_name):
    """
    Ищет edition ТОЛЬКО в _DICTIONARIES["editions"] (seed).
    Возвращает (editionId, очищенное имя).
    """
    # 1. Якорь 'Edition'
    for m in re.finditer(r"(?<![a-zA-Z])Edition(?![a-zA-Z])", full_name, re.IGNORECASE):
        start = m.start()
        end = m.end()

        after = full_name[end:].strip()
        after_words = after.split()
        after_word = after_words[0] if after_words else None

        before = full_name[:start].strip()
        words = before.split()

        for n in (4, 3, 2, 1):
            if len(words) < n:
                continue
            candidate_words = words[-n:]
            candidate_before = " ".join(candidate_words)

            if after_word:
                full_candidate = f"{candidate_before} Edition {after_word}"
                eid = _match_edition_candidate(full_candidate)
                if eid is not None:
                    cand_start = full_name.rfind(candidate_before, 0, start)
                    if cand_start != -1:
                        after_start = end + full_name[end:].find(after_word)
                        after_end = after_start + len(after_word)
                        cleaned = (full_name[:cand_start].rstrip() + " " + full_name[after_end:].lstrip()).strip()
                        return eid, clean_text(cleaned)

            full_candidate_no_after = f"{candidate_before} Edition"
            eid = _match_edition_candidate(full_candidate_no_after)
            if eid is not None:
                cand_start = full_name.rfind(candidate_before, 0, start)
                if cand_start != -1:
                    cleaned = (full_name[:cand_start].rstrip() + " " + full_name[end:].lstrip()).strip()
                    return eid, clean_text(cleaned)

    # 2. Без якоря 'Edition' — ищем по нормализованному ключу
    norm_full = normalize_edition(full_name)
    for norm_key, eid in sorted(_DICTIONARIES["editions"].items(), key=lambda kv: -len(kv[0])):
        if not norm_key:
            continue
        if norm_key in norm_full:
            # Нам нужно вырезать оригинальное название.
            # Так как нормализация меняет строку, найдем оригинал по ID.
            # Но у нас нет оригинала в словаре. Поэтому мы просто удалим
            # все вхождения ключа (без учета регистра) из full_name.
            # Это сработает для "Deluxe", "Collector's" и т.д.
            pattern = re.compile(re.escape(norm_key), re.IGNORECASE)
            cleaned = pattern.sub("", full_name)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            return eid, clean_text(cleaned)

    return None, full_name

def extract_platforms(full_name):
    """Ищет все платформы в названии."""
    lower = full_name.lower()
    found = []

    for key, val in PLATFORM_KEYS_SORTED:
        if "/" in key and key in lower:
            if val not in found:
                found.append(val)

    matched_keys = []
    for key, val in PLATFORM_KEYS_SORTED:
        if "/" in key:
            continue
        if re.search(r"(?<![a-zA-Z])" + re.escape(key) + r"(?![a-zA-Z])", lower):
            is_substring = any(key in mk and key != mk for mk in matched_keys)
            if is_substring:
                continue
            matched_keys.append(key)
            if val not in found:
                found.append(val)

    found.sort()
    return found