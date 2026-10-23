# ER: Справочники — игровые

Платформы, жанры, языки, типы изданий, типы товаров, издатели.

```mermaid
erDiagram
    platforms {
        smallserial platformId PK
        varchar platformName
        varchar platformVersion
        boolean isActive
    }
    genres {
        smallserial genreId PK
        varchar genreName
        boolean isActive
    }
    languages {
        smallserial languageId PK
        char2 languageCode
        varchar languageName
        boolean isActive
    }
    editionTypes {
        smallserial editionId PK
        varchar editionName
        boolean isActive
    }
    typeGoods {
        smallserial typeGoodId PK
        varchar typeGoodName
        boolean isActive
    }
    publishers {
        smallserial publisherId PK
        varchar publisherName
        smallint countryId FK
        boolean isActive
    }

    countries ||--o{ publishers : "country"
```

**Связи:**
- `publishers.countryId` → `countries` — страна базирования
- `platforms`, `genres`, `languages`, `editionTypes`, `typeGoods` — самостоятельные справочники

**Ключевые значения:**
- `platforms`: PC, PlayStation 4/5, Xbox One/Series, Switch 1/2, Sega Mega Drive...
- `genres`: Action, Horror, Strategy, RPG...
- `languages`: en, ru, ja, ...
- `editionTypes`: Standard (id=1), Deluxe, Collector's, Steelbook...
- `typeGoods`: **game**, **bundle**, steelbook, gamepad, figure...