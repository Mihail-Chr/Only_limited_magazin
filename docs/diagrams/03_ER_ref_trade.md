# ER: Справочники — торговые

Маркетплейсы (продажа), статусы, площадки закупки, службы доставки, поставщики.

```mermaid
erDiagram
    marketplaces {
        smallserial marketplaceId PK
        varchar marketplaceName
        numeric defaultCommissionRate
        boolean isActive
    }
    statuses {
        smallserial statusId PK
        varchar statusName
        varchar statusType
        boolean isActive
    }
    purchasePlatforms {
        smallserial purchasePlatformId PK
        varchar purchasePlatformName
        smallint countryId FK
        boolean isActive
    }
    carriers {
        smallserial carrierId PK
        varchar carrierName
        varchar trackingUrlTemplate
        boolean isActive
    }
    sellers {
        smallserial sellerId PK
        varchar sellerName
        smallint purchasePlatformId FK
        varchar marketplaceSellerId
        varchar sellerType
        smallint countryId FK
        boolean isActive
    }

    countries ||--o{ purchasePlatforms : "country"
    countries ||--o{ sellers : "country"
    purchasePlatforms ||--o{ sellers : "platform"
```

**Связи:**
- `purchasePlatforms.countryId` → `countries` — страна площадки
- `sellers.purchasePlatformId` → `purchasePlatforms` — где зарегистрирован
- `sellers.countryId` → `countries` — страна регистрации (опционально)

**Ключевые значения:**
- `marketplaces` (продажа): OZON, Avito, WB, YM, VK, SelfSite
- `statuses`: `statusType IN ('purchase','sale')`, `UNIQUE (statusName, statusType)`
- `purchasePlatforms` (закупка): eBay US, eBay EU, Amazon JP, Play-Asia, CDJapan...
- `carriers`: DHL, FedEx, USPS, EMS, Почта России, СДЭК...
- `sellers`: `sellerType IN ('shop','private','forwarder')`. Физлица группируем — одна запись на площадку/регион