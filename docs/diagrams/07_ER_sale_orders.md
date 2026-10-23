# ER: Продажа — заказы

Покупатели, заказы, позиции, история статусов.

```mermaid
erDiagram
    buyers {
        serial buyerId PK
        varchar buyerNickname
        varchar buyerCity
        varchar buyerAgeGroup
    }
    salesOrders {
        serial salesOrderId PK
        integer buyerId FK
        smallint marketplaceId FK
        varchar marketplaceOrderId
        smallint currencyId FK
        date orderDate
        integer payoutId FK
    }
    salesOrderItems {
        serial salesOrderItemId PK
        integer salesOrderId FK
        integer goodId FK
        integer quantity
        numeric salePrice
        numeric costAtSale
        smallint warehouseId FK
    }
    salesOrderStatusHistory {
        serial historyId PK
        integer salesOrderId FK
        smallint statusId FK
        timestamp statusDate
    }

    buyers ||--o{ salesOrders : ""
    marketplaces ||--o{ salesOrders : ""
    currencies ||--o{ salesOrders : ""

    salesOrders ||--o{ salesOrderItems : ""
    goods ||--o{ salesOrderItems : ""
    warehouses ||--o{ salesOrderItems : ""

    salesOrders ||--o{ salesOrderStatusHistory : ""
    statuses ||--o{ salesOrderStatusHistory : ""

    payouts o|--o{ salesOrders : "pays"
```

**Ключевые связи:**
- `salesOrders.buyerId` — **NOT NULL**. Для гостей — автогенерированный `buyerNickname` (`guest_2026_0001`)
- `salesOrders.payoutId` → `payouts` — nullable, заполняется при выплате
- `salesOrderItems.costAtSale` — `stock.avgCostRub` на момент продажи. `NULL` = «себестоимость неизвестна»
- `salesOrderItems.warehouseId` — с какого склада списан товар

**Ключевые поля:**
- `buyers.buyerNickname` — **NOT NULL UNIQUE**. Минимум ПД
- `salesOrders` — **без `commissionRate`/`commissionAmount`**. Комиссия — в `payoutAdjustments`
- `salesOrderStatusHistory`: `paid` → `shipped` → `received` / `refusal`. **Без `collected`**

**3 ключевые даты продажи (заказ):**
1. `orderDate` — оплата
2. `shipped` — отправка
3. `received` / `refusal` — получение / отказ