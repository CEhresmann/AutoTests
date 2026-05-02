# DREAMCRM OpenAPI tests

Набор pytest-тестов для контрактной и базовой сценарной проверки OpenAPI-схем:

- CRM-EXTERNAL-INTEGRATIONS
- ACCOUNTING-EXTERNAL-INTEGRATIONS
- dreamisland-back-all-app-content
- dreamisland-back-mobile

## Старт

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pytest -m smoke
.\.venv\Scripts\python.exe -m pytest -m contract
```

`-m ...` включает только выбранный marker, поэтому остальные тесты pytest покажет как `deselected`.
Чтобы запускать весь текущий набор без фильтрации, используйте:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Полный live-прогон OpenAPI

Для проверки всех операций, объявленных во всех OpenAPI-схемах:

```powershell
$env:DREAMCRM_RUN_FULL_OPENAPI_TESTS = "1"
.\.venv\Scripts\python.exe -m pytest -m full_api
```

По умолчанию этот режим вызывает только read-only операции. Чтобы также дергать `POST`,
`PATCH`, `PUT` и `DELETE`, включите отдельный флаг:

```powershell
$env:DREAMCRM_RUN_FULL_OPENAPI_TESTS = "1"
$env:DREAMCRM_RUN_MUTATING_OPENAPI_TESTS = "1"
.\.venv\Scripts\python.exe -m pytest -m full_api
```

## Артефакты наблюдений

После запуска pytest автоматически строятся:

- artifacts/observed_responses.jsonl сырые request/response
- artifacts/coverage_matrix.json матрица объявлено vs подтверждено
- artifacts/coverage_matrix.csv табличный экспорт
- artifacts/failed_tests.json проблемные кейсы текущей сессии
- reports/index.html HTML-визуализатор

## Пересборка HTML без запуска тестов

powershell
python scripts\build_observation_report.py


Эта команда перечитывает уже накопленные artifacts/*.json* и пересобирает reports/index.html.


## Примеры запуска

```powershell
pytest -m smoke
pytest -m contract
pytest -m "crm and negative"
pytest -m "accounting and not integration"
```
