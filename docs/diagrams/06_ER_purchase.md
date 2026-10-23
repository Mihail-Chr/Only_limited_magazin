# ER: Закупка

Заказы на закупку, посылки, статусы посылки, потери.

```mermaid
erDiagram
    purchaseOrders {
        serial purchaseOrderId PK
        smallint sellerId FK
        smallint currencyId FK
        date orderDate
        varchar externalNumber
        integer shipmentId FK
    }
    purchaseOrderItems {
        serial purchaseOrderItemId PK
        integer purchaseOrderId FK
        integer goodId FK
        integer quantityOrdered
        integer quantityReceived
        numeric supplierPrice
    }
    shipments {
        serial shipmentId PK
        varchar trackNumber
        smallint carrierId FK
        smallint originCountryId FK
        smallint currencyId FK
        numeric deliveryCost
        numeric customsDuty
    }
    shipmentStatusHistory {
        serial historyId PK
        integer shipmentId FK
        smallint statusId FK
        timestamp statusDate
    }
    shipmentLosses {
        serial lossId PK
        integer shipmentId FK
        varchar lossType
        varchar reason
        numeric lossAmount
        numeric refundReceived
    }

    sellers ||--o{ purchaseOrders : ""
    currencies ||--o{ purchaseOrders : ""
    purchaseOrders ||--o{ purchaseOrderItems : ""
    goods ||--o{ purchaseOrderItems : ""

    shipments o|--o{ purchaseOrders : "consolidates"
    carriers ||--o{ shipments : ""
    countries ||--o{ shipments : "origin"
    currencies ||--o{ shipments : ""

    shipments ||--o{ shipmentStatusHistory : ""
    statuses ||--o{ shipmentStatusHistory : ""

    shipments ||--o{ shipmentLosses : ""
```

**Ключевые связи:**
- `purchaseOrders.shipmentId` → `shipments` — **1 PO → 1 Shipment** (nullable, пока не привязан). Одна посылка → много заказов (консолидация)
- `shipmentStatusHistory` — история статусов **посылки** (у заказа своей истории нет)
- `shipmentLosses` — потери посылки (полные/частичные, брак, некомплект)

**Ключевые поля:**
- `purchaseOrders.orderDate` — **дата оплаты** (предоплата), 1-я ключевая дата
- `purchaseOrderItems.quantityReceived` — результат приёмки, `NULL` до приёмки
- `shipments.trackNumber` — **не уникален** (разные службы)
- `shipmentStatusHistory.statusDate` — даты для `at_carrier`, `shipped`, `customs`, `received`
- `shipmentLosses.lossType`: `full` / `partial`
- `shipmentLosses.reason`: `customs_rejected` / `destroyed` / `returned_to_seller` / `lost_in_transit` / `defect` / `incomplete`

**4 ключевые даты закупки:**
1. `orderDate` (поле) — оплата
2. `at_carrier` (история) — поступление в СД
3. `shipped` (история) — отправка
4. `received` (история) — получение