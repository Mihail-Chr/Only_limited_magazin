"""
Нормализация строк для сравнения.
"""
import re

def normalize_edition(s: str) -> str:
    """
    Агрессивная нормализация для сравнения изданий.
    lower, '’'/'‘' → ', убрать ' . - _, схлопнуть пробелы.
    """
    if not s:
        return ""
    s = s.lower()
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("'", "").replace(".", "").replace("-", "").replace("_", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def clean_text(text):
    """Очищает строку от лишних пробелов и знаков в конце."""
    text = text.strip()
    text = re.sub(r"[\-:,;]+$", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text