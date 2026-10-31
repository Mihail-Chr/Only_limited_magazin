"""
Таблица тест-кейсов для parse_name.

Формат каждого кейса:
{
    "id": "короткое_имя",
    "input": "название как пришло из выгрузки",
    "expect": {поле: значение, ...},   # что хотим получить (целевое поведение)
    "note": "пояснение, почему так"    # опционально
}

Проверяемые поля: type, base_name, platform, edition, publisher, region, media_type.
Если поля нет в expect — оно не проверяется.
Если в expect стоит None — значит «должно быть пусто/None».
"""

CASES = [
    # ---------- 385: media + составная платформа ----------
    {
        "id": "385_shakedown_physical",
        "input": "Видеоигра Shakedown: Hawaii Physical Edition (NSW/NSW2)",
        "expect": {
            "type": "game",
            "base_name": "Shakedown: Hawaii",
            "platform": "Nintendo Switch 1 / Nintendo Switch 2",
            "media_type": "physical",
            "edition": None,
            "publisher": None,
        },
        "note": "Physical — это носитель (media), не издание. Вырезать из base_name.",
    },

    # ---------- Broforce: хвост описания + издатель ----------
    {
        "id": "broforce_tail_description",
        "input": "Broforce (Special Reserve Games) — это эксклюзивное коллекционное издание экшен-платформера для Nintendo Switch и Nintendo Switch 2.",
        "expect": {
            "base_name": "Broforce",
            "publisher": "Special Reserve Games",
            "edition": None,
        },
        "note": "Хвост после ' — ' отрезать. Издателя из скобок брать из БД (Special Reserve Games).",
    },

    # ---------- Составные платформы: без дублей ----------
    {
        "id": "nsw_nsw2_no_duplicates",
        "input": "Some Game (NSW/NSW2)",
        "expect": {
            "platform": "Nintendo Switch 1 / Nintendo Switch 2",
        },
        "note": "Не должно быть 'Nintendo Switch 1 / Nintendo Switch 2 / Nintendo Switch 2'.",
    },
    {
        "id": "ps4_ps5",
        "input": "Some Game (PS4/PS5)",
        "expect": {
            "platform": "PlayStation 4 / PlayStation 5",
        },
    },
    {
        "id": "xbox_one_series",
        "input": "Some Game (Xbox One / Xbox Series)",
        "expect": {
            "platform": "Xbox One / Xbox Series",
        },
    },

    # ---------- Платформы вне скобок: собирать все ----------
    {
        "id": "platforms_outside_brackets_all",
        "input": "Some Game PS4 PS5",
        "expect": {
            "platform": "PlayStation 4 / PlayStation 5",
        },
        "note": "Асимметрию убрать: вне скобок тоже собираем все, а не только первую.",
    },

    # ---------- Steelbook: тип vs издание ----------
    {
        "id": "steelbook_as_type",
        "input": "Some Game Steelbook (PS4)",
        "expect": {
            "type": "steelbook",
            "edition": None,
        },
        "note": "Steelbook без 'Edition' — тип товара.",
    },
    {
        "id": "steelbook_as_edition",
        "input": "Some Game Steelbook Edition (PS4)",
        "expect": {
            "type": "game",
            "edition": "Steelbook",
        },
        "note": "Steelbook рядом с 'Edition' — издание.",
    },

    # ---------- Издания ----------
    {
        "id": "collectors_edition",
        "input": "Some Game (Collector's Edition) (PS5)",
        "expect": {
            "edition": "Collector's",
        },
    },
    {
        "id": "deluxe_edition",
        "input": "Some Game Deluxe Edition (PS4)",
        "expect": {
            "edition": "Deluxe",
        },
    },

    # ---------- Регионы ----------
    {
        "id": "region_pal",
        "input": "Some Game (PAL)",
        "expect": {
            "region": "EU",
        },
    },
    {
        "id": "region_ntsc_uc",
        "input": "Some Game (NTSC U/C)",
        "expect": {
            "region": "US",
        },
    },

    # ---------- Заглушка: удалять (не парсить) ----------
    {
        "id": "stub_tovar_offer_id",
        "input": "Товар 12345",
        "expect": {
            "type": "stub",
            "base_name": "Товар 12345",
        },
        "note": "Помечаем type='stub', чтобы clean_stubs мог удалять по этому признаку.",
    },
    {
        "id": "stub_novyi_tovar",
        "input": "Новый товар (ожидает заполнения)",
        "expect": {
            "type": "stub",
            "base_name": "Новый товар (ожидает заполнения)",
        },
    },

    # ---------- Media: digital / cartridge / code in a box ----------
    {
        "id": "media_digital",
        "input": "Some Game Digital Edition (PS5)",
        "expect": {
            "media_type": "digital",
            "base_name": "Some Game",
        },
        "note": "Digital — носитель, не издание.",
    },
    {
        "id": "media_code_in_a_box",
        "input": "Some Game Code in a Box (NSW)",
        "expect": {
            "media_type": "code_in_a_box",
            "base_name": "Some Game",
        },
    },

    # ---------- Комбинированный: media + издание + регион ----------
    {
        "id": "combo_media_edition_region",
        "input": "Some Game Physical Deluxe Edition (PAL) (PS5)",
        "expect": {
            "type": "game",
            "base_name": "Some Game",
            "media_type": "physical",
            "edition": "Deluxe",
            "region": "EU",
            "platform": "PlayStation 5",
        },
    },
 # ---------- Новые издания из реальной базы (2026-10-30) ----------
    {
        "id": "classic_edition",
        "input": "Some Game Classic Edition (PS5)",
        "expect": {
            "type": "game",
            "base_name": "Some Game",
            "edition": "Classic",
            "platform": "PlayStation 5",
        },
    },
    {
        "id": "definitive_edition",
        "input": "Some Game Definitive Edition (PS4/PS5)",
        "expect": {
            "base_name": "Some Game",
            "edition": "Definitive",
            "platform": "PlayStation 4 / PlayStation 5",
        },
    },
    {
        "id": "complete_edition",
        "input": "Some Game Complete Edition (NSW/NSW2)",
        "expect": {
            "base_name": "Some Game",
            "edition": "Complete",
            "platform": "Nintendo Switch 1 / Nintendo Switch 2",
        },
    },
    {
        "id": "enhanced_edition",
        "input": "Some Game Enhanced Edition (XO/XS)",
        "expect": {
            "base_name": "Some Game",
            "edition": "Enhanced",
            "platform": "Xbox One / Xbox Series",
        },
    },
    {
        "id": "extended_edition",
        "input": "Some Game Extended Edition (PS5)",
        "expect": {
            "base_name": "Some Game",
            "edition": "Extended",
        },
    },
    {
        "id": "exclusive_edition",
        "input": "Some Game Exclusive Edition (PS5)",
        "expect": {
            "base_name": "Some Game",
            "edition": "Exclusive",
        },
    },
    {
        "id": "classic_edition_with_videogame",
        "input": "Видеоигра Some Game Classic Edition (Limited Run Games) (PS5)",
        "expect": {
            "type": "game",
            "base_name": "Some Game",
            "edition": "Classic",
            "platform": "PlayStation 5",
            "publisher": "Limited Run Games",
        },
        "note": "Проверяем, что 'Видеоигра' срезается и Classic Edition распознаётся.",
    },
    {
        "id": "single_word_platinum",
        "input": "Some Game (Platinum) (PS1)",
        "expect": {"base_name": "Some Game", "edition": "Platinum", "platform": "PlayStation 1"},
    },
    {
        "id": "single_word_tails",
        "input": "Controller Sonic (Tails)",
        "expect": {"base_name": "Controller Sonic", "edition": "Tails"},
    },
    {
        "id": "unknown_single_word_kept",
        "input": "Some Game (XYZ) (PS1)",
        "expect": {"base_name": "Some Game (XYZ)", "edition": None, "platform": "PlayStation 1"},
    },
]