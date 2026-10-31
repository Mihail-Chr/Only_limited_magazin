# Рабочий контекст (снимок)

Обновляется перед рискованным шагом и в конце сессии. Не история — только «где мы сейчас».
История решений — в `HISTORY.md`.

## Текущий этап (2026-10-30)

Ветка: `test/parser-target-behavior`
Задача: тест-кейсы на целевое поведение парсера, затем патч парсера под них.

## Что в работе

- `src/parsers/` — вынос чистой логики `parse_name` (в плане)
- `src/parsers/tests/cases.py` — таблица кейсов (в плане)
- `src/parsers/tests/runner.py` — прогон (в плане)

## Решено (актуальное)

См. раздел «Зафиксированные решения» в `HISTORY.md` за 2026-10-30.

## Отложено

- `merge_duplicates.py`
- `check_duplicates_analysis.py`
- `platform_set`
- Переименование карточек в OZON через API
- Регионы `'e'`/`'g'` — обсудить

## Открытые вопросы

- Ревизии платформ: только справочник (решено), но нужно ли добавлять колонку `revision` в `schema.sql` сейчас или отдельной миграцией?

- check_info_list_coverage.py — диагностика: сколько name приходит из info/list, сколько нет.
  Цель: решить, нужны ли заглушки как fallback или можно сразу писать name.
  Сделать после парсера и merge_duplicates.

# Рабочий контекст (снимок)

Обновляется перед рискованным шагом и в конце сессии. Не история — только «где мы сейчас».
История решений — в `HISTORY.md`.

## Текущий этап (2026-10-30)

Ветка: `test/parser-target-behavior` → merge в `main`.
Задача: парсер готов (24/24 тестов), финальный отчёт по дублям для владельца.

## Что в работе

- `src/parsers/tests/cases.py` — 24 кейса, все зелёные.
- `src/parsers/tests/runner.py` — прогон + `--random N`.
- `src/scripts/parse_names.py` — переписан, словари из БД, `media_type`, edition-anchor.

## Решено (актуальное)

См. раздел «Зафиксированные допущения» в `HISTORY.md` за 2026-10-30.

Ключевое:
- Уникальные издания остаются в `base_name` (не угадываем).
- `Edition` остаётся в `base_name`, если издание не распознано.
- Издатель — только в скобках (и в конце — обсудить).
- Регион — только в скобках.
- `platform_set` — на этап `merge_duplicates`.

## Отложено

- `merge_duplicates.py`
- `check_duplicates_analysis.py` (грубый)
- `check_info_list_coverage.py`
- Pipeline: порядок шагов, единый маркер заглушки, `info/list` до заглушки
- `seed_reference_data.py`: портативные платформы, издатели, `KR`
- Переименование карточек в OZON через API

## Открытые вопросы

- Издатель «в конце названия» (не только в скобках) — как отличать от части названия? Обсудить.
- Регион вне скобок (в конце) — нужно ли?
- `K.O.`, `Remastered Edition`, `GOTY` — добавлять ли в `EDITION_MAP` (сейчас нет).

# Рабочий контекст (снимок)

## Текущий этап (2026-10-31)

Ветка: `test/parser-target-behavior`.
Парсер: 27/27 тестов. Сделаны: `SINGLE_WORD_EDITION_MAP` (Platinum/Classic/Black/Tails/Knuckles), «не удалять нераспознанные скобки», `france exclusive` в `EDITION_MAP`, `de cover`/`ntsc-j`/`ntsc-u`/`pal-uk`/`pal-eu` в `REGION_MAP` (ПРОВЕРИТЬ).

## Что в работе

- `src/scripts/parse_names.py` — парсер (27/27).
- `src/parsers/tests/cases.py` — 27 кейсов.
- `scratch/export_duplicates_xlsx.py` — отчёт по дублям (правила: BASE_NAME, PLATFORM, EDITION, REGION_ID, MEDIA_TYPE).

## Решено (актуальное, НЕ переспрашивать)

- `SINGLE_WORD_EDITION_MAP` (5 ключей): `platinum`, `classic`, `black`, `tails`, `knuckles`. Одиночное слово в скобках из этого словаря → `edition`. Не из словаря → остаётся в `base_name`.
- `EDITION_MAP` (22 ключа): базовые — `deluxe`, `ultimate`, `collector's`, `collectors`, `limited`, `steelbook`, `signature`, `day one`, `gold`, `anniversary`, `special`, `premium`, `standard`. Добавлены — `classic`, `definitive`, `complete`, `enhanced`, `extended`, `exclusive`, `slip case gold`, `france exclusive`, `картонный бокс`.
- `REGION_MAP`: `ntsc u/c` (US), `ntsc` (US), `ntsc-j` (JP), `ntsc-u` (US), `usa` (US), `us` (US), `pal` (EU), `pal-uk` (EU), `pal-eu` (EU), `eur` (EU), `eu` (EU), `japan` (JP), `j` (JP), `jpn` (JP), `jp` (JP), `asia` (Asia), `ru` (RU), `rus` (RU), `russia` (RU), `cn` (CN), `chn` (CN), `china` (CN), `aus` (AUS), `australia` (AUS), `sa` (SA), `de cover` (EU). Убраны `e`, `g`.
- `variant` — НЕ делаем.
- `package_type` — оставить (для «Покупки»), в парсере не трогать.
- Неизвестные скобки **2+ слова** — оставлять в `base_name` (Вариант A).
- Правила дублей: `BASE_NAME` (точно) → `PLATFORM` (пересечение) → `EDITION` (точно, NULL≠значение) → `REGION_ID` (точно, NULL≠значение) → `MEDIA_TYPE` (точно, NULL≠значение).
- `Tails`/`Knuckles`/`Platinum`/`Black` — **в `SINGLE_WORD_EDITION_MAP`**, не в `base_name`.
- `Capcom` в `SNK vs. Capcom` — **не** издатель. Издатель — только в скобках (и в конце — обсудить).
- `pipeline0` (отладка) / `base_pipeline` (реальная работа) — разделить.


## Отложено

- `merge_duplicates.py` (правила готовы, код — нет).
- UI-проверка дублей при вводе.
- `check_info_list_coverage.py`.
- `pipeline0` / `base_pipeline` — разделить.
- Неизвестные скобки 2+ слова — оставлять в `base_name` (Вариант A).
- `seed_reference_data.py`: портативные платформы, издатели, `KR`.
- Переименование карточек в OZON через API.

## Решено (актуальное, НЕ переспрашивать)

- Удалять из base_name **только** `(Лицензия)` (служебная скобка). Всё остальное (Товар уцененный, Frank Herbert's Dune, неизвестные скобки) — **оставлять** в base_name.
- `PLATFORM_MAP`: добавить `xbox series x`, `xbox series s`, `xsx`, `xss` → `Xbox Series`.
- (остальное — как в предыдущем CONTEXT.md)

- EDITION_MAP: добавить 'ultimate 30th anniversary', 'essence of art', 'mirror', "collector's k.o.", 'ultimate steelbook'.
- Double Pack — оставить в base_name (не трогать).
- extract_edition: порядок (3,2,1) — длинная фраза приоритетнее короткой.

- PLATFORM_MAP: 'xbox series x' → 'Xbox Series X', 'xbox series s' → 'Xbox Series S', 'xsx' → 'Xbox Series X', 'xss' → 'Xbox Series S'. (Series X/S — отдельные платформы, не сводить к Series.)
- export_duplicates_xlsx.py: PUBLISHER в правилах (6-я очередь, точное, NULL≠значение).
- Порядок: BASE_NAME → PLATFORM → EDITION → REGION_ID → MEDIA_TYPE → PUBLISHER.

- EDITION_MAP += 'vengeance': 'Vengeance'.
- PLATFORM_MAP: 'xbox series x' → 'Xbox Series X', 'xbox series s' → 'Xbox Series S', 'xsx' → 'Xbox Series X', 'xss' → 'Xbox Series S'. (ПРОВЕРИТЬ, что значения именно с X/S.)

- EDITION_MAP += 'steelbook premium': 'Steelbook Premium'.
- extract_platforms: добавить matched_keys (проверка подстроки), чтобы 'xbox series' не матчился внутри 'xbox series x'.
- parse_names ОБЯЗАТЕЛЬНО перезапускать после правок PLATFORM_MAP/EDITION_MAP — иначе в БД старое значение.