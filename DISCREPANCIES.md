# Расхождения: OpenAPI / DreamCRM_Contracts.md ↔ реальный стенд

Зафиксировано по итогам happy-path прогона (curl) от 2026-07-01 против dev-стендов:
- CRM: `crmstage-external-integrations-di-dev.dreamisland.ru`
- Accounting: `crmstage-accounting-external-api-di-dev.dreamisland.ru`

Легенда: 🔴 баг стенда · 🟠 расхождение контракта/спеки · 🟡 ограничение тестовых данных

---

## Happy-path матрица (что реально даёт 2xx)

### CRM Integrations — 10/11 методов 2xx ✅
| Метод | Путь | Статус | Заметка |
|-------|------|--------|---------|
| GET | /health | 200 | |
| GET | /api/v1/customers/ping | 200 | |
| POST | /customers | 200 | |
| PATCH | /customers | 200 | |
| POST | /customers/search | 200 | ⚠ см. 🔴-1 |
| POST | /customer-actions | 201 | |
| POST | /customer-actions/bulk | 200 | |
| POST | /devices | 201 | |
| POST | /devices/assign | 200 | |
| DELETE | /devices/assign | 200 | |
| POST | /campaigns/automatic/send | — | нет `DREAMCRM_CRM_CAMPAIGN_ID` |

### Accounting — 22/27 методов 2xx ✅ (5 заблокированы)
| Метод | Путь | Статус | Заметка |
|-------|------|--------|---------|
| GET | /health, /accounting/ping | 200 | |
| GET | /product, /product/{id} | 200 | |
| POST | /product, /product/bulk | 201/200 | 🟠-3 (bulk resp shape) |
| GET | /product_category, /{id} | 200 | |
| POST | /orders | 201 | 🟠-2 (нужен `ECOM` заглавными) |
| GET | /orders, /orders/{id} | 200 | |
| PATCH | /orders/{id}, /items/{lineId} | 200 | |
| POST | /orders/calculate | 200 | |
| GET | /bonuses/balance | 200 | 🟠-4 (customer_id/website_id, не как в спеке) |
| GET | /bonuses/customer-points-balance | 200 | |
| GET | /bonuses/customer-points-history | 200 | |
| POST | /bonuses/accrue-customer-points | 201 | |
| POST | /bonuses/hold + PATCH /hold/{id} | 201/200 | |
| POST | /bonuses/activate-customer-points | **500** 🔴-5 | |
| POST | /gift-certificates/validate | 200 | 🟠-6 (нужен `certificate_number`) |
| POST | /gift-certificates/{debit,credit,refund} | **422** 🟡-7 | сертификат не активирован |
| POST | /gift-certificates/activate | **404** 🟡-7 | нельзя активировать произвольный номер |
| POST | /promocodes/assign | **422** 🟠-8 | `pool_id` требует integer |

---

## 🔴 Баги стенда

### 🔴-1 `POST /customers/search` игнорирует неизвестные ключи фильтра
Нераспознанный ключ (`id` скаляром, любой мусор) или пустой `filter` → возвращается **вся база** (`total≈555k`, статус 200) вместо 400/422. По `DreamCRM_Contracts.md` filter — строго `website_id`/`email`/`mobile_phone`/`discount_card_number`.
**Тест:** `test_search_customer_rejects_undocumented_id_scalar_filter` → `xfail(strict=False)`.

### 🔴-5 `POST /bonuses/activate-customer-points` → 500
На корректном `bonus_id` (полученном из `accrue-customer-points` 201) стенд отдаёт:
`Database error: greenlet_spawn has not been called; can't call await_only()...` (SQLAlchemy async).
**Тест:** `test_activate_customer_points` → `xfail(strict=False)`.

---

## 🟠 Расхождения контракта / OpenAPI

### 🟠-2 `external_system` в заказах — только ЗАГЛАВНЫМИ
`DreamCRM_Contracts.md` показывает `external_system: "ecom"` / `"TICKET_SYSTEM"`. Стенд принимает **только** enum заглавными: `FOR_MAILINGS, TICKET_SYSTEM, MERCH, NPS_PRODUCT, OFFLINE, ECOM, GIFT_CARDS, RETAIL`. `"ecom"` → 422.
**Фикс:** фабрики используют `ECOM`. (Примечание: `POST /product` со `"Ecom"` проходит 201 — товарный эндпойнт лоялен к регистру, заказы — нет.)

### 🟠-3 `POST /product/bulk` — форма ответа
Спека и стенд отдают `{results, total, created, updated, errors}`, НЕ `success_count`/`error_count` (последнее — только у CRM bulk). Исходный тест ждал неверные ключи.
**Фикс:** ассерт `created + updated + errors == total`.

### 🟠-4 `GET /bonuses/balance` — идентификатор
Работает с query `customer_id` ИЛИ `website_id` (+ `include_holds`). Ответ: `{balance:{total,available,held}}` (поддерживается и плоский формат). Прежний код инжектил `customer_id` во все GET вслепую.

### 🟠-6 `POST /gift-certificates/validate` — обязателен идентификатор карты
Требует `certificate_id` ИЛИ `certificate_number` (+ `transaction_id`). Только `transaction_id` → 422 `certificate_id or certificate_number is required`.

### 🟠-8 `POST /promocodes/assign` — `pool_id` строго integer
Спека: `pool_id: integer`. Стенд: `int_parsing` 422 на строке. Пул system_name (`dlyaSaytaPokupkaBiletov`) **не** принимается — нужен числовой id пула.
**Статус:** нет валидного числового `pool_id` → тест skip.

---

## 🟡 Ограничения тестовых данных (не баги)

### 🟡-7 Подарочные сертификаты — нужен активированный сертификат
Тестовый `KT4567892346` в статусе `not_activated` (validate: `is_valid:true, status:not_activated`).
- `debit/credit/refund` → 422 `Certificate status is not activated / does not allow` — **корректное поведение**.
- `activate` привязана к предзаведённой карте пула; произвольный номер → 404 `Gift certificate not found`.
**Нужно:** данные сертификата в статусе `activated` (номер + пул). Тесты помечены `xfail`/`skip` до появления.

### Прочее
- `campaigns/automatic/send` — нужен реальный `DREAMCRM_CRM_CAMPAIGN_ID`.
- `contact_point_id` — **обязательный HTTP-заголовок для всех Accounting-запросов** (не только тела). Без него часть GET → 400. Реализовано в `APISettings.default_headers`.

---

# Воспроизведение: реальные запросы и ответы

> Захвачено с dev-стенда 2026-07-01. `$API_KEY` замаскирован; подставить `DREAMCRM_API_KEY` / `DREAMCRM_ACCOUNTING_API_KEY`.

## 🔴-1 `customers/search` игнорирует неизвестный ключ фильтра

Ожидался 400/422 (ключ `id` скаляром не в контракте фильтра) — получаем 200 и всю базу.

```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'Content-Type: application/json' \
  'https://crmstage-external-integrations-di-dev.dreamisland.ru/api/v1/crm-external-integrations/customers/search' \
  -d '{"filter": {"id": 555113}, "page": 1, "page_size": 2}'
```
Ответ `200`:
```json
{
  "total": 555106,
  "page": 1,
  "page_size": 2,
  "total_pages": 277553,
  "customers": [ { "id": 1, "website_id": "525205", "...": "..." }, { "id": 2, "...": "..." } ]
}
```
> `total: 555106` — фильтр молча проигнорирован, вернулась вся база.

---

## 🔴-5 `bonuses/activate-customer-points` → 500

Шаг 1 — создаём бонус (корректный 201):
```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/bonuses/accrue-customer-points' \
  -d '{"customer_id": 555113, "amount": 1, "description": "capture", "valid_from": "2026-07-01T13:23:19Z"}'
```
Ответ `201`:
```json
{ "id": "a976b9e5-662e-4a6f-b7d3-f91bee1262ac", "amount": 1, "type": "accrual", "status": "active", "...": "..." }
```

Шаг 2 — активируем этот бонус:
```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/bonuses/activate-customer-points' \
  -d '{"bonus_id": "a976b9e5-662e-4a6f-b7d3-f91bee1262ac"}'
```
Ответ `500`:
```json
{ "detail": "Database error: greenlet_spawn has not been called; can't call await_only() here. Was IO attempted in an unexpected place? (Background on this error at: https://sqlalche.me/e/20/xd2s)" }
```

---

## 🟠-2 `orders` — `external_system` только ЗАГЛАВНЫМИ

Строчными `ecom` (как в DreamCRM_Contracts.md):
```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/orders' \
  -d '{"external_order_id": "disc-ccc5b8f9", "external_system": "ecom", "contact_point_id": "ecom_web", "website_id": "autotest-123", "email": "auto.test.api@mail.test", "status": "cart", "items": [{"external_line_id": "line-1", "position_number": 1, "external_product_id": "p", "product_name": "L", "unit_price": 100.0, "quantity": 1}], "totals": {"subtotal": 100.0, "total": 100.0}}'
```
Ответ `422`:
```json
{ "detail": [ { "type": "literal_error", "loc": ["body", "external_system"],
  "msg": "Input should be 'FOR_MAILINGS', 'TICKET_SYSTEM', 'MERCH', 'NPS_PRODUCT', 'OFFLINE', 'ECOM', 'GIFT_CARDS' or 'RETAIL'",
  "input": "ecom" } ] }
```

Тот же запрос с `ECOM`:
```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/orders' \
  -d '{"external_order_id": "disc-813f5b9a", "external_system": "ECOM", "contact_point_id": "ecom_web", "website_id": "autotest-123", "email": "auto.test.api@mail.test", "status": "cart", "items": [{"external_line_id": "line-1", "position_number": 1, "external_product_id": "p", "product_name": "L", "unit_price": 100.0, "quantity": 1}], "totals": {"subtotal": 100.0, "total": 100.0}}'
```
Ответ `201`:
```json
{ "success": true, "external_order_id": "disc-813f5b9a", "status": "cart", "gift_certificate": null, "errors": [] }
```

---

## 🟠-3 `product/bulk` — форма ответа (created/updated/errors)

```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/product/bulk' \
  -d '{"items": [{"external_id": "disc-b-49cc717a", "external_system": "ECOM", "name": "B", "price": 1.0, "category": {"external_id": "disc-cat", "name": "c"}}]}'
```
Ответ `200`:
```json
{
  "results": [ { "index": 0, "status": "created", "product": { "id": 7324, "external_id": "disc-b-49cc717a", "...": "..." }, "error": null } ],
  "total": 1, "created": 1, "updated": 0, "errors": 0
}
```
> Нет `success_count`/`error_count` — только `created`/`updated`/`errors`/`results`/`total`.

---

## 🟠-4 `bonuses/balance` — по customer_id (или website_id)

```bash
curl -X GET -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/bonuses/balance?customer_id=555113&include_holds=true'
```
Ответ `200`:
```json
{
  "success": true, "customer_id": 555113,
  "customer": { "id": 555113, "full_name": "Updated AutoTest", "email": "auto.test.api@mail.test", "website_id": "autotest-123" },
  "balance": { "total": 16.0, "available": 13.0, "held": 3.0, "pending_accrual": 0.0 },
  "holds": [], "expiring": [], "errors": []
}
```

---

## 🟠-6 `gift-certificates/validate` — нужен certificate_number

Только `transaction_id`:
```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/gift-certificates/validate' \
  -d '{"transaction_id": "KT4567892346"}'
```
Ответ `422`:
```json
{ "detail": [ { "type": "value_error", "loc": ["body"],
  "msg": "Value error, certificate_id or certificate_number is required",
  "input": { "transaction_id": "KT4567892346" } } ] }
```

С `certificate_number`:
```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/gift-certificates/validate' \
  -d '{"certificate_number": "KT4567892346", "transaction_id": "cap-7e6e3c6c"}'
```
Ответ `200`:
```json
{ "operation_id": 509, "certificate_id": 326, "certificate_number": "KT4567892346",
  "transaction_id": "cap-7e6e3c6c", "is_valid": true, "status": "not_activated", "current_balance": null }
```

---

## 🟠-8 `promocodes/assign` — pool_id строго integer

```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/promocodes/assign' \
  -d '{"pool_id": "dlyaSaytaPokupkaBiletov", "customer_id": 555113}'
```
Ответ `422`:
```json
{ "detail": [ { "type": "int_parsing", "loc": ["body", "pool_id"],
  "msg": "Input should be a valid integer, unable to parse string as an integer",
  "input": "dlyaSaytaPokupkaBiletov" } ] }
```

---

## 🟡-7 Подарочные сертификаты — статус не позволяет операцию

Debit неактивированного сертификата:
```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/gift-certificates/debit' \
  -d '{"amount": 1, "transaction_id": "cap-4710e55b", "certificate_number": "KT4567892346"}'
```
Ответ `422`:
```json
{ "detail": "Certificate status is not activated" }
```

Activate с несуществующим `external_order_id` (карту тоже нельзя завести на лету):
```bash
curl -X POST -H 'X-API-Key: $API_KEY' -H 'contact_point_id: ecom_web' -H 'Content-Type: application/json' \
  'https://crmstage-accounting-external-api-di-dev.dreamisland.ru/api/v1/accounting-external-api/gift-certificates/activate' \
  -d '{"nominal_value": 10000, "transaction_id": "cap-45696b62", "external_order_id": "cap-o-c7053cef", "certificate_number": "NEW8223A8EE", "customer_id": 555113, "activated_at": "2026-07-01T13:23:23Z"}'
```
Ответ `404`:
```json
{ "detail": "Order not found: cap-o-c7053cef" }
```
> Для happy-path activate нужен и предзаведённый заказ (`GIFT_CARDS`), и карта из пула.
