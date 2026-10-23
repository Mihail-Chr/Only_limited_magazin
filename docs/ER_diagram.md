# ER-диаграмма

Версия: 1.0
Последнее обновление: 2026-10-23

Диаграмма сгенерирована из модели данных (файлы `04`, `041`, `042`, `043`). Рендерится GitHub нативно через Mermaid. Для редактирования удобно использовать VS Code с расширением `Markdown Preview Mermaid Support`.

Документ разбит на 5 секций:
1. Обзор (все таблицы, только связи)
2. Справочники (детально)
3. Товары и склад (детально)
4. Закупка (детально)
5. Продажа (детально)

---

## 1. Обзор

Общая структура связей между всеми 34 таблицами. Для деталей — см. секции ниже.

```mermaid
erDiagram
    %% ===== СПРАВОЧНИКИ =====
    countries
    regions
    platforms
    genres
    languages
    editionTypes
    typeGoods
    currencies
    marketplaces
    statuses
    exchangeRates
    publishers
    purchasePlatforms
    carriers
    sellers

    %% ===== ТОВАРЫ И СКЛАД =====
    goods
    productGenres
    productLanguages
    bundleItems
    warehouses
    stock
    stockWriteOffs

    %% ===== ЗАКУПКА =====
    purchaseOrders
    purchaseOrderItems
    shipments
    shipmentStatusHistory
    shipmentLosses

    %% ===== ПРОДАЖА =====
    buyers
    salesOrders
    salesOrderItems
    salesOrderStatusHistory
    salesReturns
    payouts
    payoutAdjustments

    %% ===== СВЯЗИ СПРАВОЧНИКОВ =====
    countries ||--o{ publishers : ""
    countries ||--o{ purchasePlatforms : ""
    countries ||--o{ sellers : ""
    countries ||--o{ shipments : ""
    currencies ||--o{ exchangeRates : "from"
    currencies ||--o{ exchangeRates : "to"
    purchasePlatforms ||--o{ sellers : ""
    carriers ||--o{ shipments : ""
    marketplaces ||--o{ salesOrders : ""
    marketplaces ||--o{ payouts : ""
    statuses ||--o{ shipmentStatusHistory : ""
    statuses ||--o{ salesOrderStatusHistory : ""

    %% ===== СВЯЗИ ТОВАРОВ И СКЛАДА =====
    typeGoods ||--o{ goods : ""
    platforms ||--o{ goods : ""
    publishers ||--o{ goods : ""
    regions ||--o{ goods : ""
    editionTypes ||--o{ goods : ""
    goods ||--o{ goods : "related game"
    goods ||--o{ productGenres : ""
    genres ||--o{ productGenres : ""
    goods ||--o{ productLanguages : ""
    languages ||--o{ productLanguages : ""
    goods ||--o{ bundleItems : "bundle"
    goods ||--o{ bundleItems : "included in"
    goods ||--o{ stock : ""
    warehouses ||--o{ stock : ""
    goods ||--o{ stockWriteOffs : ""
    warehouses ||--o{ stockWriteOffs : ""

    %% ===== СВЯЗИ ЗАКУПКИ =====
    sellers ||--o{ purchaseOrders : ""
    currencies ||--o{ purchaseOrders : ""
    purchaseOrders ||--o{ purchaseOrderItems : ""
    goods ||--o{ purchaseOrderItems : ""
    shipments o|--o{ purchaseOrders : "consolidates"
    currencies ||--o{ shipments : ""
    shipments ||--o{ shipmentStatusHistory : ""
    shipments ||--o{ shipmentLosses : ""

    %% ===== СВЯЗИ ПРОДАЖИ =====
    buyers ||--o{ salesOrders : ""
    currencies ||--o{ salesOrders : ""
    salesOrders ||--o{ salesOrderItems : ""
    goods ||--o{ salesOrderItems : ""
    warehouses ||--o{ salesOrderItems : ""
    salesOrders ||--o{ salesOrderStatusHistory : ""
    salesOrders ||--o{ salesReturns : ""
    warehouses ||--o{ salesReturns : ""
    payouts o|--o{ salesOrders : "pays"
    payouts ||--o{ payoutAdjustments : ""
    salesOrders ||--o{ payoutAdjustments : ""
```

---

## 2. Справочники (детально)

```mermaid
erDiagram
    countries {
        smallserial countryId PK
        char2 isoAlpha2 "UNIQUE"
        char3 isoAlpha3 "UNIQUE"
        varchar countryName
        varchar countryNameRu
        boolean isActive
    }

    regions {
        smallserial regionId PK
        varchar regionCode "UNIQUE"
        varchar regionName
        smallint sortOrder
        boolean isActive
    }

    platforms {
        smallserial platformId PK
        varchar platformName
        varchar platformVersion
        smallint sortOrder
        boolean isActive
    }

    genres {
        smallserial genreId PK
        varchar genreName "UNIQUE"
        smallint sortOrder
        boolean isActive
    }

    languages {
        smallserial languageId PK
        char2 languageCode "UNIQUE"
        varchar languageName
        varchar languageNameRu
        smallint sortOrder
        boolean isActive
    }

    editionTypes {
        smallserial editionId PK
        varchar editionName "UNIQUE"
        smallint sortOrder
        boolean isActive
    }

    typeGoods {
        smallserial typeGoodId PK
        varchar typeGoodName "UNIQUE"
        smallint sortOrder
        boolean isActive
    }

    currencies {
        smallserial currencyId PK
        char3 currencyCode "UNIQUE"
        varchar currencyName
        varchar currencySymbol
        boolean isCrypto
        smallint sortOrder
        boolean isActive
    }

    marketplaces {
        smallserial marketplaceId PK
        varchar marketplaceName "UNIQUE"
        numeric defaultCommissionRate
        smallint sortOrder
        boolean isActive
    }

    statuses {
        smallserial statusId PK
        varchar statusName "UNIQUE with statusType"
        varchar statusType "purchase | sale"
        smallint sortOrder
        boolean isActive
    }

    exchangeRates {
        serial exchangeRateId PK
        date rateDate
        smallint currencyFromId FK
        smallint currencyToId FK
        numeric rate
        varchar source
    }

    publishers {
        smallserial publisherId PK
        varchar publisherName "UNIQUE"
        smallint countryId FK
        smallint sortOrder
        boolean isActive
    }

    purchasePlatforms {
        smallserial purchasePlatformId PK
        varchar purchasePlatformName "UNIQUE"
        smallint countryId FK
        smallint sortOrder
        boolean isActive
    }

    carriers {
        smallserial carrierId PK
        varchar carrierName "UNIQUE"
        varchar trackingUrlTemplate
        smallint sortOrder
        boolean isActive
    }

    sellers {
        smallserial sellerId PK
        varchar sellerName
        smallint purchasePlatformId FK
        varchar marketplaceSellerId "nullable"
        varchar sellerType "shop | private | forwarder"
        smallint countryId FK "nullable"
        varchar contactEmail
        varchar website
        text notes
        smallint sortOrder
        boolean isActive
    }

    countries ||--o{ publishers : "country"
    countries ||--o{ purchasePlatforms : "country"
    countries ||--o{ sellers : "country"
    currencies ||--o{ exchangeRates : "from"
    currencies ||--o{ exchangeRates : "to"
    purchasePlatforms ||--o{ sellers : "platform"
```

---

## 3. Товары и склад (детально)

```mermaid
erDiagram
    typeGoods {
        smallserial typeGoodId PK
        varchar typeGoodName "game | bundle | steelbook | ..."
    }

    platforms {
        smallserial platformId PK
        varchar platformName
        varchar platformVersion
    }

    publishers {
        smallserial publisherId PK
        varchar publisherName
    }

    regions {
        smallserial regionId PK
        varchar regionCode
    }

    editionTypes {
        smallserial editionId PK
        varchar editionName
    }

    goods {
        serial goodId PK
        varchar goodName "UNIQUE"
        varchar baseGameName
        smallint typeGoodId FK
        smallint platformId FK
        integer relatedGameId FK
        smallint publisherId FK
        smallint regionId FK
        smallint editionId FK "default 1=Standard"
        smallint firstReleaseYear "nullable"
        smallint firstYearEdition "nullable"
        smallint remakeYear "nullable"
        smallint audience "nullable: 0,6,12,16,18"
        boolean ageRestricted
        varchar dataQuality "full | partial | minimal"
        varchar barcode "nullable UNIQUE"
        varchar sku "nullable UNIQUE"
        text notes
        boolean isActive
    }

    genres {
        smallserial genreId PK
        varchar genreName
    }

    languages {
        smallserial languageId PK
        varchar languageName
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

    warehouses {
        smallserial warehouseId PK
        varchar warehouseName "main | archive | repair"
        boolean isActive
    }

    stock {
        smallint warehouseId FK
        integer goodId FK
        integer quantity
        integer countOfRepair
        numeric avgCostRub "nullable"
        numeric avgCostUsd "nullable"
        numeric avgCostEur "nullable"
        date avgCostUpdatedAt "2026-09-01 = manual"
        date lastExchangeRateDate
    }

    stockWriteOffs {
        serial writeOffId PK
        integer goodId FK
        smallint warehouseId FK
        integer quantity
        varchar reason "defect_* | lost_* | other"
        varchar sourceType "purchase_receipt | sales_return | ..."
        integer sourceId
        date writeOffDate
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
    goods ||--o{ bundleItems : "included in"

    goods ||--o{ stock : ""
    warehouses ||--o{ stock : ""
    goods ||--o{ stockWriteOffs : ""
    warehouses ||--o{ stockWriteOffs : ""
```

---

## 4. Закупка (детально)

```mermaid
erDiagram
    sellers {
        smallserial sellerId PK
        varchar sellerName
    }

    currencies {
        smallserial currencyId PK
        char3 currencyCode
    }

    carriers {
        smallserial carrierId PK
        varchar carrierName
    }

    countries {
        smallserial countryId PK
        char2 isoAlpha2
    }

    statuses {
        smallserial statusId PK
        varchar statusName
        varchar statusType
    }

    purchaseOrders {
        serial purchaseOrderId PK
        smallint sellerId FK
        smallint currencyId FK
        date orderDate "дата оплаты"
        varchar externalNumber
        integer shipmentId FK "nullable"
        text notes
    }

    purchaseOrderItems {
        serial purchaseOrderItemId PK
        integer purchaseOrderId FK
        integer goodId FK
        integer quantityOrdered
        integer quantityReceived "nullable"
        numeric supplierPrice
        text notes
    }

    shipments {
        serial shipmentId PK
        varchar trackNumber "nullable, NOT unique"
        smallint carrierId FK "nullable"
        smallint originCountryId FK "nullable"
        smallint currencyId FK
        numeric deliveryCost "nullable"
        numeric customsDuty "nullable"
        text notes
    }

    shipmentStatusHistory {
        serial historyId PK
        integer shipmentId FK
        smallint statusId FK
        timestamp statusDate
        text comment
    }

    shipmentLosses {
        serial lossId PK
        integer shipmentId FK
        varchar lossType "full | partial"
        date lossDate
        varchar reason "customs_rejected | ... | defect | incomplete"
        numeric lossAmount
        numeric refundReceived
        text notes
    }

    sellers ||--o{ purchaseOrders : ""
    currencies ||--o{ purchaseOrders : ""
    purchaseOrders ||--o{ purchaseOrderItems : ""
    goods ||--o{ purchaseOrderItems : ""

    shipments o|--o{ purchaseOrders : "consolidates"
    currencies ||--o{ shipments : ""
    carriers ||--o{ shipments : ""
    countries ||--o{ shipments : "origin"

    shipments ||--o{ shipmentStatusHistory : ""
    statuses ||--o{ shipmentStatusHistory : ""
    shipments ||--o{ shipmentLosses : ""
```

---

## 5. Продажа (детально)

```mermaid
erDiagram
    buyers {
        serial buyerId PK
        varchar buyerNickname "NOT NULL, UNIQUE"
        varchar buyerCity "nullable"
        varchar buyerAgeGroup "nullable"
    }

    marketplaces {
        smallserial marketplaceId PK
        varchar marketplaceName
        numeric defaultCommissionRate
    }

    currencies {
        smallserial currencyId PK
        char3 currencyCode
    }

    statuses {
        smallserial statusId PK
        varchar statusName
        varchar statusType
    }

    salesOrders {
        serial salesOrderId PK
        integer buyerId FK "NOT NULL"
        smallint marketplaceId FK
        varchar marketplaceOrderId "nullable"
        smallint currencyId FK
        date orderDate
        integer payoutId FK "nullable"
        text notes
    }

    salesOrderItems {
        serial salesOrderItemId PK
        integer salesOrderId FK
        integer goodId FK
        integer quantity
        numeric salePrice
        numeric costAtSale "nullable"
        smallint warehouseId FK
        text notes
    }

    salesOrderStatusHistory {
        serial historyId PK
        integer salesOrderId FK
        smallint statusId FK
        timestamp statusDate
        text comment
    }

    salesReturns {
        serial returnId PK
        integer salesOrderId FK
        date returnDate
        varchar reason "customer_refusal | damaged | ..."
        numeric refundAmount
        numeric returnShippingCost
        varchar returnCondition "new | used | damaged"
        smallint warehouseId FK
        text notes
    }

    payouts {
        serial payoutId PK
        smallint marketplaceId FK
        date periodStart
        date periodEnd
        date paidAt "NOT NULL"
        numeric totalAmount "NOT NULL"
        varchar reportNumber "nullable"
        text notes
    }

    payoutAdjustments {
        serial adjustmentId PK
        integer payoutId FK
        integer salesOrderId FK
        varchar adjustmentType "order_amount | commission | refund | lost_in_delivery | lost_in_return | commission_correction | other"
        numeric amount "+нам | −удержание"
        text notes
    }

    buyers ||--o{ salesOrders : ""
    marketplaces ||--o{ salesOrders : ""
    currencies ||--o{ salesOrders : ""
    salesOrders ||--o{ salesOrderItems : ""
    goods ||--o{ salesOrderItems : ""
    warehouses ||--o{ salesOrderItems : ""

    salesOrders ||--o{ salesOrderStatusHistory : ""
    statuses ||--o{ salesOrderStatusHistory : ""
    salesOrders ||--o{ salesReturns : ""
    warehouses ||--o{ salesReturns : "returned to"

    payouts o|--o{ salesOrders : "pays"
    marketplaces ||--o{ payouts : ""
    payouts ||--o{ payoutAdjustments : ""
    salesOrders ||--o{ payoutAdjustments : ""
```

---

## Как читать диаграмму

**Кардинальность (символы Mermaid):**

| Символ | Значение |
|---|---|
| `\|\|` | Ровно один (1) |
| `\|o` | Ноль или один (0..1) — nullable FK |
| `}\|` | Один или более (1..N) |
| `}o` | Ноль или более (0..N) |
| `\|\|--o{` | Один-ко-многим (1:N) |
| `o\|--o{` | Ноль-или-один-ко-многим (0..1 : 0..N) |

**Обозначения полей:**

| Обозначение | Значение |
|---|---|
| `PK` | Первичный ключ |
| `FK` | Внешний ключ |
| `nullable` | Может быть `NULL` |
| `UNIQUE` | Уникальное значение |

**Группы таблиц:**

- **Справочники** — `countries`, `regions`, `platforms`, `genres`, `languages`, `editionTypes`, `typeGoods`, `currencies`, `marketplaces`, `statuses`, `exchangeRates`, `publishers`, `purchasePlatforms`, `carriers`, `sellers`.
- **Товары и склад** — `goods`, `productGenres`, `productLanguages`, `bundleItems`, `warehouses`, `stock`, `stockWriteOffs`.
- **Закупка** — `purchaseOrders`, `purchaseOrderItems`, `shipments`, `shipmentStatusHistory`, `shipmentLosses`.
- **Продажа** — `buyers`, `salesOrders`, `salesOrderItems`, `salesOrderStatusHistory`, `salesReturns`, `payouts`, `payoutAdjustments`.

**Ключевые связи между контурами (закупка ↔ продажа):**

Закупка и продажа **не связаны напрямую**. Пересечение — только через `stock` (закупка увеличивает `quantity`, продажа уменьшает). Это позволяет независимо развивать оба контура.

**Особые связи:**

- `goods ↔ goods` — self-reference (`relatedGameId`). Например, стилбук к игре Doom Eternal.
- `goods ↔ bundleItems ↔ goods` — сборник (`bundleGoodId`) содержит игры (`includedGoodId`).
- `purchaseOrders ↔ shipments` — 1 PO → 0..1 shipment (nullable `shipmentId`). 1 shipment → 0..N PO (консолидация).
- `payouts ↔ salesOrders` — 1 sale order → 0..1 payout (nullable `payoutId`). 1 payout → 0..N sale orders.

---

## Как редактировать

1. **VS Code** + расширение `Markdown Preview Mermaid Support` (ID: `bierner.markdown-mermaid`) — live-предпросмотр в редакторе.
2. **GitHub** — рендерит автоматически при просмотре файла. Ничего дополнительно не нужно.
3. **Mermaid Live Editor** (`mermaid.live`) — вставить код, посмотреть, поправить, скопировать обратно.

При изменении схемы:
- Правите `04_модель_данных.md` (или `041`/`042`/`043`) — источник истины.
- Синхронизируете `ER_diagram.md`.
- Коммитите оба файла. GitHub покажет обновлённую диаграмму и дифф изменений.

---

## История изменений

**v1.0** (2026-10-23): первая версия. 34 таблицы, 5 секций (обзор + 4 домена). Mermaid `erDiagram`, рендерится GitHub нативно.