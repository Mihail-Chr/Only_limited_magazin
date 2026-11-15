"""
dictionaries.py — объединённые словари парсера (v4.0).

Источники:
- Наши: TYPE_MAP (первые 3 слова), PLATFORM_MAP, PUBLISHER_MAP, REGION_MAP,
  EDITION_MAP, BASE_EDITIONS.
- Внешние: TYPE_MAP, BUNDLE_MARKERS, STEELBOOK_MARKERS, PLATFORM_ALIASES,
  PUBLISHERS, REGIONS, MEDIA_MAP, EDITION_RULES, LICENSE_RE.

Принципы:
- Канонические имена изданий — БЕЗ слова "edition" (Collector's, Deluxe, GOTY).
- Издатели — точное совпадение, не по подстроке (Limited Run Games ≠ Limited Rare Games).
- Платформы: Sega Mega Drive / Genesis — НЕ платформа (часть названия).
- Xbox Series (без X/S) → "Xbox Series X|S".
- Регион "Испания" → EU (с parseNote region_guess).
- Media: объединены наши и внешние (e-key, цифровой ключ, картридж и т.д.).
"""
import re

# =====================================================================
# ТИПЫ ТОВАРОВ
# =====================================================================

TYPE_MAP = {
    "видеоигра": "game",
    "стилбук": "steelbook",
    "геймпад": "gamepad",
    "джойстик": "joystick",
    "фигурка": "figure",
    "карточки": "card",
    "значок": "badge",
    "наклейка": "sticker",
    "игрушка": "toy",
}
DEFAULT_PRODUCT_TYPE = "game"

# Маркеры bundle (наборов). Если найдены — тип = bundle.
BUNDLE_MARKERS = [
    "bundle",
    "trilogy",
    "double pack",
    "combo",
    "1+2",
    "2 in 1",
    "set",
]

# Маркеры steelbook без игры. Если найдены — тип = steelbook.
STEELBOOK_MARKERS = [
    "steelbook без игры",
    "стилбук без игры",
]

# =====================================================================
# ПЛАТФОРМЫ
# =====================================================================
# Ключ — то, что ищем в названии (lowercase).
# Значение — каноническое имя (как в platforms.platformName + platformVersion).
# ВАЖНО: Sega Mega Drive / Genesis — НЕ платформа (часть названия).
# =====================================================================

PLATFORM_ALIASES = {
    # PC
    "pc": "PC Windows",
    "steam": "PC Windows",
    "windows": "PC Windows",
    "steam deck": "Steam Deck LCD/OLED",

    # PlayStation
    "ps1": "PlayStation 1",
    "psx": "PlayStation 1",
    "ps2": "PlayStation 2",
    "ps3": "PlayStation 3",
    "ps4": "PlayStation 4",
    "ps5": "PlayStation 5",
    "ps4/ps5": "PlayStation 4",

    # Xbox
    "xbox original": "Xbox Original",
    "xbox 360": "Xbox 360",
    "xbox one": "Xbox One",
    "xo": "Xbox One",
    "xbox series": "Xbox Series",
    "xbox series x": "Xbox Series",
    "xbox series s": "Xbox Series",
    "xs": "Xbox Series",
    "xsx": "Xbox Series",
    "xss": "Xbox Series",
    "xbx": "Xbox Series",
    "xo/xs": "Xbox One",

    # Nintendo
    "nsw": "Nintendo Switch 1",
    "nsw2": "Nintendo Switch 2",
    "nsw/nsw2": "Nintendo Switch 1",
    "nintendo switch": "Nintendo Switch 1",
    "nds": "Nintendo DS",
    "ds": "Nintendo DS",
    "nintendo ds": "Nintendo DS",
    "3ds": "Nintendo 3DS",
    "gba": "Nintendo Game Boy Advance",
    "gbc": "Nintendo Game Boy Color",
    "gb": "Nintendo Game Boy",
    "game boy": "Nintendo Game Boy",
    "gamecube": "Nintendo GameCube",
    "wii": "Nintendo Wii",
    "wii u": "Nintendo Wii U",
    "snes": "Nintendo SNES",
    "nes": "Nintendo NES",
    "n64": "Nintendo 64",

    # Sega (без Mega Drive / Genesis — часть названия)
    "sega dreamcast": "Sega Dreamcast",
    "dreamcast": "Sega Dreamcast",
    "dc": "Sega Dreamcast",
    "sega saturn": "Sega Saturn",
    "saturn": "Sega Saturn",
    "sega game gear": "Sega Game Gear",

    # Atari
    "atari 2600": "Atari 2600",
}

# Ключи, которые НЕ являются платформой (часть названия).
PLATFORM_EXCLUDE = {
    "sega mega drive",
    "sega genesis",
    "mega drive",
    "genesis",
}

# =====================================================================
# РЕГИОНЫ
# =====================================================================
# Ищем везде (в скобках и вне). "Испания" → EU (с parseNote).
# =====================================================================

REGIONS = {
    "ntsc u/c": "US",
    "ntsc-u/c": "US",
    "ntsc": "US",
    "ntsc-j": "JP",
    "ntsc-u": "US",
    "usa": "US",
    "us": "US",
    "pal": "EU",
    "pal-uk": "EU",
    "pal-eu": "EU",
    "eur": "EU",
    "eu": "EU",
    "japan": "JP",
    "jpn": "JP",
    "jp": "JP",
    "j": "JP",
    "asia": "Asia",
    "ru": "RU",
    "rus": "RU",
    "russia": "RU",
    "cn": "CN",
    "chn": "CN",
    "china": "CN",
    "aus": "AUS",
    "australia": "AUS",
    "sa": "SA",
    "de cover": "EU",
    "france": "EU",
    "испания": "EU",   # с parseNote region_guess
}

# =====================================================================
# ИЗДАТЕЛИ
# =====================================================================
# Точное совпадение (regex с границами слов). Не по подстроке:
# Limited Run Games ≠ Limited Rare Games.
# =====================================================================

PUBLISHERS = [
    # Наши (30)
    "Nintendo",
    "Sega",
    "Sony Interactive Entertainment",
    "Microsoft / Xbox Game Studios",
    "Electronic Arts",
    "Ubisoft",
    "Activision Blizzard",
    "Bandai Namco",
    "Capcom",
    "Square Enix",
    "Konami",
    "Take-Two Interactive",
    "CD Projekt",
    "Paradox Interactive",
    "1C",
    "Limited Run Games",
    "Strictly Limited Games",
    "Merge Games",
    "NIS America",
    "Idea Factory International",
    "Special Reserve Games",
    "Super Rare Games",
    "Eastasiasoft",
    "Play-Asia",
    "Red Art Games",
    "Pix'n Love",
    "Signature Edition Games",
    "Fangamer",
    "iam8bit",
    "Retro-Bit",
    "Limited Rare Games",
]

# =====================================================================
# MEDIA (типы носителей)
# =====================================================================
# Ключ — то, что ищем (lowercase). Значение — каноническое имя (mediaTypeName).
# =====================================================================

MEDIA_MAP = {
    # Наши
    "physical": "physical",
    "digital": "digital",
    "cartridge": "cartridge",
    "disc": "disc",
    "code in a box": "code_in_a_box",
    "download code": "download_code",
    # Внешние
    "e-key": "digital",
    "ekey": "digital",
    "digital key": "digital",
    "цифровой ключ": "digital",
    "цифровая версия": "digital",
    "физическая версия": "physical",
    "картридж": "cartridge",
}

# =====================================================================
# ИЗДАНИЯ (EDITION_RULES)
# =====================================================================
# Regex (lowercase, с \b) → каноническое имя БЕЗ "edition".
# Порядок важен: длинные/специфичные — раньше.
# =====================================================================

EDITION_RULES = [
    # Составные / специфичные
    (r"collector'?s\s+edition", "Collector's"),
    (r"special\s+limited\s+edition", "Special Limited"),
    (r"limited\s+special\s+edition", "Limited Special"),
    (r"signature\s+edition", "Signature"),
    (r"stellar\s+steelbook\s+edition", "Stellar Steelbook"),
    (r"legendary\s+edition\s+steelbook", "Legendary Edition Steelbook"),
    (r"legendary\s+edition", "Legendary Edition"),
    (r"first\s+year", "First Year"),
    (r"new\s+year", "New Year"),
    (r"ultimate\s+30th\s+anniversary", "Ultimate 30th Anniversary"),
    (r"origins\s+collection", "Origins Collection"),
    (r"anniversary\s+collection", "Anniversary Collection"),
    (r"three\s+fairies\s+edition", "Three Fairies Edition"),
    (r"steelbook\s+premium", "Steelbook Premium"),
    (r"ultimate\s+steelbook", "Ultimate Steelbook"),
    (r"slip\s+case\s+gold\s+edition", "Slip Case Gold"),
    (r"iam8bit\s+exclusive\s+edition", "iam8bit Exclusive"),
    (r"france\s+exclusive", "France Exclusive"),
    (r"event\s+exclusive", "Event Exclusive"),
    (r"game\s+of\s+the\s+year\s+edition", "Game of the Year"),
    (r"\bgoty\b", "GOTY"),
    (r"day\s+one\s+edition", "Day One"),
    (r"day\s+one", "Day One"),
    (r"gold\s+steelbook\s+edition", "Gold Steelbook"),
    (r"gold\s+steelbook", "Gold Steelbook"),
    (r"steelbook\s+edition", "Steelbook"),
    (r"physical\s+edition", "Physical"),
    (r"definitive\s+edition", "Definitive"),
    (r"ultimate\s+edition", "Ultimate"),
    (r"complete\s+edition", "Complete"),
    (r"enhanced\s+edition", "Enhanced"),
    (r"anniversary\s+edition", "Anniversary"),
    (r"classic\s+edition", "Classic"),
    (r"platinum\s+edition", "Platinum"),
    (r"extended\s+edition", "Extended"),
    (r"gold\s+edition", "Gold"),
    (r"premium\s+edition", "Premium"),
    (r"exclusive\s+edition", "Exclusive"),
    (r"special\s+edition", "Special"),
    (r"deluxe\s+edition", "Deluxe"),
    (r"limited\s+edition", "Limited"),
    # Без "edition" (одиночные слова)
    (r"\bdeluxe\b", "Deluxe"),
    (r"\bsteelbook\b", "Steelbook"),
    (r"\bspecial\b", "Special"),
    (r"\benhanced\b", "Enhanced"),
    (r"\banniversary\b", "Anniversary"),
    (r"\bclassic\b", "Classic"),
    (r"\bexclusive\b", "Exclusive"),
    (r"\bultimate\b", "Ultimate"),
    (r"\bdefinitive\b", "Definitive"),
    (r"\bsignature\b", "Signature"),
    (r"\bcomplete\b", "Complete"),
    (r"\bplatinum\b", "Platinum"),
    (r"\bextended\b", "Extended"),
    (r"\bgold\b", "Gold"),
    (r"\bpremium\b", "Premium"),
    (r"\bcollection\b", "Collection"),
    (r"\blimited\b", "Limited"),
    (r"\bphysical\b", "Physical"),
]

# =====================================================================
# ЛИЦЕНЗИЯ
# =====================================================================
# Лицензия + Пиратка → restore = 1.
# =====================================================================

LICENSE_RE = re.compile(r"(лицензия|пиратка)", re.IGNORECASE)

# =====================================================================
# СКОМПИЛИРОВАННЫЕ REGEX
# =====================================================================

def _alternation(values):
    """Собирает альтернацию из значений (длинные — раньше)."""
    return "|".join(sorted((re.escape(v) for v in values), key=len, reverse=True))

# Платформы: \b(ключ)\b, case-insensitive.
# Исключаем PLATFORM_EXCLUDE.
_PLATFORM_KEYS = [k for k in PLATFORM_ALIASES if k not in PLATFORM_EXCLUDE]
PLATFORM_RE = re.compile(r"\b(" + _alternation(_PLATFORM_KEYS) + r")\b", re.IGNORECASE)

# Регионы: \b(ключ)\b. Без IGNORECASE для NTSC/PAL (регистр важен),
# но с IGNORECASE для остальных — проще один regex с IGNORECASE.
REGION_RE = re.compile(r"\b(" + _alternation(REGIONS) + r")\b", re.IGNORECASE)

# Media: \b(ключ)\b, case-insensitive.
MEDIA_RE = re.compile(r"\b(" + _alternation(MEDIA_MAP) + r")\b", re.IGNORECASE)

# Издатели: отдельный regex на каждого (границы слов).
PUBLISHER_RES = [
    (name, re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE))
    for name in PUBLISHERS
]

# Издания: regex + каноническое имя.
EDITION_RES = [
    (re.compile(r"\b" + pattern + r"\b", re.IGNORECASE), canonical)
    for pattern, canonical in EDITION_RULES
]