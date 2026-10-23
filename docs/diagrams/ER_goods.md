# ER: Товары

Товары (SKU), M2M с жанрами и языками, состав сборников.

```mermaid
erDiagram
    goods {
        serial goodId PK
        varchar goodName
        varchar baseGameName
        smallint typeGoodId FK
        smallint platformId FK
        smallint publisherId FK
        smallint regionId FK
        smallint editionId FK
        integer relatedGameId FK
        varchar dataQuality
        boolean isActive
    }
    productGenres {
        integer productId FK
        smallint genreId FK
    }
    productLanguages {
        integer productId FK
        smallint languageId FK
    }
    bundleItems {
        integer bundleGoodId FK
        integer includedGoodId FK
        smallint quantity
    }

    typeGoods ||--o{ goods : "type"
    platforms ||--o{ goods : "platform"
    publishers ||--o{ goods : "publisher"
    regions ||--o{ goods : "region"
    editionTypes ||--o{ goods : "edition"
    goods ||--o{ goods : "related game"

    goods ||--o{ productGenres : ""
    genres ||--o{ productGenres : ""
    goods ||--o{ productLanguages : ""
    languages ||--o{ productLanguages : ""

    goods ||--o{ bundleItems : "bundle"
    goods ||--o{ bundleItems : "included"
```

**Ключевые связи:**
- `goods.relatedGameId` → `goods` — self-reference (стилбук → игра)
- `productGenres` — M2M между товаром и жанром
- `productLanguages` — M2M между товаром и языком (English привязывается автоматически)
- `bundleItems` — M2M между сборником (`typeGoodId = 'bundle'`) и входящими играми

**Ключевые поля:**
- `dataQuality`: `full` / `partial` / `minimal`
- `editionId DEFAULT 1` (Standard)
- `firstReleaseYear`, `firstYearEdition`, `remakeYear` — три разных года для аналитики «волн популярности»