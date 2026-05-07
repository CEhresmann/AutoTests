# DREAMCRM API Tests

Автоматические тесты для четырёх API-сервисов Dream Island: контрактная валидация по OpenAPI-схемам, сценарные проверки, мониторинг доступности с HTML-дашбордами.

## Сервисы

| Сервис | Base URL | Схема |
|--------|----------|-------|
| CRM | `crmstage-external-integrations-di-dev.dreamisland.ru` | `CRM-EXTERNAL-INTEGRATIONS-openapi.json` |
| Accounting | `crmstage-accounting-external-api-di-dev.dreamisland.ru` | `ACCOUNTING-EXTERNAL-INTEGRATIONS-openapi.json` |
| App Content | `dreamisland.ru` | `dreamisland-back-all-app-content.json` |
| Mobile (legacy) | `dreamisland.ru` | `dreamisland-back-mobile.json` |
| Mobile Shop | `dreamisland.ru` | `OpenApi/Mobile/openapi_back_shop_new.yaml` |
| Mobile Site | `back.dreamisland.ru` | `OpenApi/Mobile/openapi_back_site.yaml` |

---

## Быстрый старт (Linux / macOS)

```bash
python3.11 -m venv .venv
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
| `DREAMCRM_API_KEY` | API-ключ CRM |
| `DREAMCRM_BASE_URL` | Base URL CRM |
| `DREAMCRM_ACCOUNTING_API_KEY` | API-ключ Accounting |
| `DREAMCRM_ACCOUNTING_BASE_URL` | Base URL Accounting |
| `DREAMCRM_EMAIL` | Email тестового клиента |
| `DREAMCRM_CUSTOMER_ID` | ID клиента в CRM |
| `DREAMCRM_RUN_FULL_OPENAPI_TESTS=1` | **Включает полный live-прогон** (без этого 90% тестов пропускается) |
| `DREAMCRM_RUN_MUTATING_OPENAPI_TESTS=1` | Разрешает POST/PATCH/DELETE |

### Токены для мобильных и app-content эндпойнтов

| Переменная | Как получить |
|-----------|-------------|
| `DREAMCRM_MOBILE_AUTHORIZATION` | Браузер → DevTools → Network → любой запрос к `dreamisland.ru` → заголовок `Authorization` после логина |
| `DREAMCRM_APP_CONTENT_AUTHORIZATION` | То же самое (dreamisland.ru) |
| `DREAMCRM_MOBILE_SITE_AUTHORIZATION` | Автоматически: `python scripts/get_site_token.py --update-env` (back.dreamisland.ru, без капчи) |

> `dreamisland.ru` требует Yandex SmartCaptcha при логине — токен нельзя получить автоматически.
> `back.dreamisland.ru` капчи не требует, токен обновляется скриптом.

### Для тестов конкретных ресурсов (иначе skip)

| Переменная | Зачем |
|-----------|-------|
| `DREAMCRM_PROMOTION_ORDER_ID` | Тесты промоакций |
| `DREAMCRM_CRM_CAMPAIGN_ID` | Campaign automatic send |
| `DREAMCRM_ACCOUNTING_PROMOCODE_POOL_ID` | Promocodes assign |
| `DREAMCRM_ACCOUNTING_PROMOTION_ID` | Promotion apply-to-item |
| `DREAMCRM_ACCOUNTING_ORDER_ITEM_ID` | Order item update |
| `DREAMCRM_CONTACT_POINT_ID` | Order PATCH |

---

## Маркеры pytest

```bash
pytest -m smoke               # health/ping — быстрая проверка доступности
pytest -m contract            # валидация OpenAPI-схем
pytest -m "crm"               # только CRM
pytest -m "accounting"        # только Accounting
pytest -m "negative"          # негативные сценарии (400/401/422)
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
| `app_content` | dreamisland back all app-content |
| `mobile` | dreamisland back mobile (legacy) |
| `mobile_shop` | dreamisland back shop (новая схема) |
| `mobile_site` | dreamisland back site (новая схема) |
| `full_api` | Генерированные live-запросы по всем операциям OpenAPI |
| `integration` | Сценарные тесты с побочными эффектами |
| `regression` | Регрессия |

---

## Артефакты и отчёты

После запуска pytest или скриптов мониторинга автоматически создаются:

```
artifacts/
  observed_responses.jsonl    # все request/response текущей сессии (JSONL)
  coverage_matrix.json        # declared vs observed статус-коды
  coverage_matrix.csv         # то же в CSV
  failed_tests.json           # упавшие/skipped кейсы

  availability_history.jsonl  # накопительная история health-зондов (никогда не очищается)

reports/
  index.html          # детальный отчёт: покрытие, endpoint passports, contract mismatches
  availability.html   # uptime-дашборд: доступность по сервисам, лента проверок, график
```

### Пересборка отчётов без запуска тестов

```bash
# Покрытие / observation report
python scripts/build_observation_report.py

# Uptime-дашборд
python scripts/build_availability_report.py
```

---

## Мониторинг доступности

### Разовый прогон зонда

```bash
python scripts/availability_monitor.py
```

Зондирует `/health` и `/ping` для CRM и Accounting, записывает результат в `artifacts/availability_history.jsonl`, пересобирает `reports/availability.html`. Выходит с кодом `1` если хоть один сервис упал.

### Обновление токена для mobile-site

```bash
python scripts/get_site_token.py              # напечатать токен
python scripts/get_site_token.py --update-env # записать в .env
```

### Установка крона (Linux)

```bash
bash scripts/setup_cron.sh           # установить
bash scripts/setup_cron.sh --remove  # удалить
```

Расписание:
- **Каждые 4 часа** — `availability_monitor.py` → `logs/availability.log`
- **Каждые 6 часов** — `pytest -m "smoke or contract"` → `logs/daily_tests.log`

---

## Развёртка на сервере

### Одна команда

```bash
sudo bash scripts/install_server.sh --project-dir /srv/dreamcrm-tests
```

Устанавливает зависимости, настраивает nginx, cron, делает первый зонд.

### Nginx вручную

```bash
sudo cp nginx/dreamcrm-dashboard.conf /etc/nginx/sites-available/dreamcrm
sudo ln -s /etc/nginx/sites-available/dreamcrm /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Конфиг в [nginx/dreamcrm-dashboard.conf](nginx/dreamcrm-dashboard.conf):
- `server_name _;` — работает с любым IP или доменом
- `/` → `reports/availability.html` (uptime-дашборд)
- `/index.html` → детальный отчёт по покрытию
- `/` и `/index.html` связаны вкладками прямо в UI

### HTTPS

```bash
sudo certbot --nginx -d your-domain.ru
```

### Структура на сервере

```
/srv/dreamcrm-tests/
├── .env                      # секреты (chmod 600, не в git)
├── reports/                  # статика, раздаётся nginx
│   ├── availability.html     # uptime-дашборд  ← /
│   └── index.html            # coverage report ← /index.html
├── artifacts/                # сырые данные (nginx блокирует доступ снаружи)
│   └── availability_history.jsonl
├── logs/                     # вывод крона
│   ├── availability.log
│   └── daily_tests.log
└── scripts/
    ├── availability_monitor.py
    ├── setup_cron.sh
    ├── install_server.sh
    └── get_site_token.py
```

---

## Структура проекта

```
configs/
  settings.py           # APISettings для всех сервисов, чтение из .env

utils/
  api_client.py         # requests-обёртка с записью в ObservationRecorder
  observability.py      # ObservationRecorder, HTML-генератор для index.html
  openapi.py            # загрузка JSON/YAML схем, resolve_ref, match_openapi_path
  validators.py         # jsonschema-валидация ответов
  test_data.py          # фабрики payload'ов для всех сервисов
  payload_pruner.py     # обрезка лишних полей из тела запросов

tests/
  smoke/                # test_health_ping.py
  contract/             # test_crm_contract.py, test_accounting_contract.py, ...
  full/                 # test_openapi_live_requests.py — генерированный прогон
  negative/             # test_auth.py, test_validation.py, test_boundaries.py
  crm/                  # test_customers.py, test_customer_actions.py
  conftest.py           # фикстуры клиентов, схем, ObservationRecorder

scripts/
  availability_monitor.py      # health-зонды → availability_history.jsonl
  build_availability_report.py # HTML uptime-дашборд
  build_observation_report.py  # пересборка index.html из артефактов
  get_site_token.py            # обновление JWT для back.dreamisland.ru
  setup_cron.sh                # установка/удаление cron-заданий
  install_server.sh            # полная установка на сервер

nginx/
  dreamcrm-dashboard.conf      # готовый конфиг nginx

OpenApi/                       # OpenAPI-схемы (в .gitignore)
  *.json
  Mobile/
    openapi_back_shop_new.yaml
    openapi_back_site.yaml
```

---

## Диагностика типичных проблем

| Симптом | Причина | Решение |
|---------|---------|---------|
| 90% тестов `deselected` / пропущены | `DREAMCRM_RUN_FULL_OPENAPI_TESTS` не установлен | Добавить `=1` в `.env` |
| `/api/mobile/v1/*` возвращает пустой 400 | Нужен user JWT, не app-key | Обновить `DREAMCRM_MOBILE_AUTHORIZATION` из браузера |
| `/api/app/personal/*` → 401 `expired` | JWT истёк | Обновить `DREAMCRM_APP_CONTENT_AUTHORIZATION` из браузера |
| Accounting GET → 400 `At least one identifier required` | Исправлено в коде: `customer_id` теперь инжектируется автоматически | — |
| `pytest.skip: Set DREAMCRM_PROMOTION_ORDER_ID` | Не задан ID реального заказа | Добавить переменную в `.env` |
| `reports/availability.html` не обновляется | Крон не установлен или упал | `crontab -l`, `cat logs/availability.log` |
