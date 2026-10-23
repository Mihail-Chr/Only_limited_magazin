# ER: Справочники — базовые

Страны, регионы, валюты, курсы.

```mermaid
erDiagram
    countries {
        smallserial countryId PK
        char2 isoAlpha2
        varchar countryName
        varchar countryNameRu
    }
    regions {
        smallserial regionId PK
        varchar regionCode
        varchar regionName
    }
    currencies {
        smallserial currencyId PK
        char3 currencyCode
        varchar currencyName
        boolean isCrypto
    }
    exchangeRates {
        serial exchangeRateId PK
        date rateDate
        smallint currencyFromId FK
        smallint currencyToId FK
        numeric rate
    }

    currencies ||--o{ exchangeRates : "from"
    currencies ||--o{ exchangeRates : "to"
```

**Связи:**
- `exchangeRates.currencyFromId` → `currencies.currencyId` — из какой валюты
- `exchangeRates.currencyToId` → `currencies.currencyId` — в какую валюту
- `countries`, `regions` — самостоятельные справочники, связей между собой нет