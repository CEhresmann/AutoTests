# DREAMCRM API Tests

Регрессионные тесты для двух API-сервисов DreamIsland: **CRM External Integrations** и **Accounting External API**. 
## Сервисы

| Сервис | Base URL | Схема |
|--------|----------|-------|
| CRM | `crmstage-external-integrations-di-dev.dreamisland.ru` | `OpenAPI/crm-openapi.json` |
| Accounting | `crmstage-accounting-external-api-di-dev.dreamisland.ru` | `OpenAPI/accounting-openapi.json` |

---

## Быстрый старт (Linux / macOS)

```bash
python3.12 -m venv .venv       
.venv/bin/pip install -e .
cp .env.example .env
# заполните .env (см. раздел «Переменные окружения»)
.venv/bin/pytest -m smoke
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -e .
Copy-Item .env.example .env
# заполните .env
.\.venv\Scripts\pytest -m smoke
```

---

## Переменные окружения

Скопируйте `.env.example` → `.env` и заполните значения.

### Обязательные для полного прогона

| Переменная | Зачем |
|-----------|-------|
| `DREAMCRM_API_KEY` | API-ключ CRM (заголовок `X-API-Key`) |
| `DREAMCRM_BASE_URL` | Base URL CRM |
| `DREAMCRM_ACCOUNTING_API_KEY` | API-ключ Accounting |
| `DREAMCRM_ACCOUNTING_BASE_URL` | Base URL Accounting |
| `DREAMCRM_EMAIL` | Email тестового клиента |
| `DREAMCRM_CUSTOMER_ID` | ID клиента в CRM/Accounting |
| `DREAMCRM_WEBSITE_ID` | website_id клиента (заказы, calculate) |
| `DREAMCRM_MOBILE_PHONE` | телефон клиента (заказы) |
| `DREAMCRM_ACTION_TEMPLATE_SYSTEM_NAME` | system_name шаблона действия (customer-actions) |
| `DREAMCRM_RUN_FULL_OPENAPI_TESTS=1` | **Включает live-прогон** по всем операциям (иначе `full_api` пропускается) |
| `DREAMCRM_RUN_MUTATING_OPENAPI_TESTS=1` | Разрешает POST/PATCH/DELETE в live-прогоне |

### Для тестов конкретных ресурсов (иначе skip или 4xx)

| Переменная | Зачем |
|-----------|-------|
| `DREAMCRM_CONTACT_POINT_ID` | `PATCH /orders/{external_order_id}` |
| `DREAMCRM_ACCOUNTING_PROMOCODE_POOL_ID` | `POST /promocodes/assign` |
| `DREAMCRM_CRM_CAMPAIGN_ID` | `POST /campaigns/automatic/send` |


## Маркеры pytest

```bash
pytest -m smoke               # health/ping — быстрая проверка доступности
pytest -m contract            # валидация OpenAPI-схем (без вызова API)
pytest -m crm                 # только CRM
pytest -m accounting          # только Accounting
pytest -m negative            # негативные сценарии (400/401/422)
pytest -m "crm and negative"  # комбинация
pytest -m full_api            # полный live-прогон всех OpenAPI-операций
pytest -m "smoke or contract" # smoke + contract (используется кроном)
```

| Маркер | Описание |
|--------|----------|
| `smoke` | Проверка `/health` и `/ping` |
| `contract` | Валидация форм OpenAPI-схем |
| `negative` | Проверки на 400/401/403/422 |
| `crm` | CRM external integrations |
| `accounting` | Accounting external API |
| `full_api` | Генерированные live-запросы по всем операциям OpenAPI |
| `integration` | Сценарные тесты с побочными эффектами |
| `bulk` | Массовые операции |
| `regression` | Регрессия |

---

## Артефакты и отчёты

После запуска pytest или скриптов мониторинга создаются:

```
artifacts/
  observed_responses.jsonl    # все request/response текущей сессии (JSONL)
  coverage_matrix.json        # declared vs observed статус-коды
  coverage_matrix.csv         # то же в CSV
  failed_tests.json           # упавшие/skipped кейсы
  availability_history.jsonl  # накопительная история health-зондов

reports/
  index.html          # покрытие, endpoint passports, contract mismatches
  availability.html   # uptime-дашборд по сервисам
```

### Пересборка отчётов без запуска тестов

```bash
python scripts/build_observation_report.py   # покрытие / observation report
python scripts/build_availability_report.py  # uptime-дашборд
```

---

## Мониторинг доступности

```bash
python scripts/availability_monitor.py
```

Зондирует `/health` и `/ping` для CRM и Accounting, пишет в `artifacts/availability_history.jsonl`, пересобирает `reports/availability.html`. Код выхода `1`, если хоть один сервис упал.

### Крон (Linux)

```bash
bash scripts/setup_cron.sh           # установить
bash scripts/setup_cron.sh --remove  # удалить
```

Расписание:
- **Каждые 4 часа** — `availability_monitor.py` → `logs/availability.log`
- **Каждые 6 часов** — `pytest -m "smoke or contract"` → `logs/daily_tests.log`

---

## Развёртка на сервере

```bash
sudo bash scripts/install_server.sh --project-dir /srv/dreamcrm-tests
```

Устанавливает зависимости, настраивает nginx (`nginx/dreamcrm-dashboard.conf`), cron и делает первый зонд.

HTTPS:

```bash
sudo certbot --nginx -d your-domain.ru
```
