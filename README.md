# DREAMCRM OpenAPI tests

Набор `pytest`-тестов для контрактной, smoke, negative и базовой сценарной проверки двух OpenAPI-схем:

- `CRM-EXTERNAL-INTEGRATIONS`
- `ACCOUNTING-EXTERNAL-INTEGRATIONS`

## Быстрый старт

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
Copy-Item .env.example .env
pytest -m smoke
pytest -m contract
```

Для отдельных accounting-сценариев могут понадобиться дополнительные стендовые данные:

- `DREAMCRM_CONTACT_POINT_ID` для `PATCH /orders/{external_order_id}`
- `DREAMCRM_PROMOTION_ORDER_ID` для `POST /promotions/preview`

## Артефакты наблюдений

После запуска `pytest` автоматически строятся:

- [artifacts/observed_responses.jsonl](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\artifacts\observed_responses.jsonl) — сырые request/response
- [artifacts/coverage_matrix.json](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\artifacts\coverage_matrix.json) — матрица declared vs observed
- [artifacts/coverage_matrix.csv](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\artifacts\coverage_matrix.csv) — табличный экспорт
- [artifacts/failed_tests.json](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\artifacts\failed_tests.json) — проблемные кейсы текущей сессии
- [reports/index.html](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\reports\index.html) — HTML-визуализатор

HTML-отчёт показывает:

- какие коды ответов заявлены в OpenAPI
- какие коды реально встретились в тестах
- какие коды пока не воспроизведены
- какие ответы вышли за пределы контракта
- явные `contract mismatches` по упавшим тестам
- последние детальные request/response-наблюдения

## Пересборка HTML без запуска тестов

```powershell
python scripts\build_observation_report.py
```

Эта команда перечитывает уже накопленные `artifacts/*.json*` и пересобирает [reports/index.html](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\reports\index.html).

## Основные директории

- [configs/settings.py](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\configs\settings.py)
- [utils/api_client.py](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\utils\api_client.py)
- [utils/validators.py](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\utils\validators.py)
- [tests](C:\Users\titr\Desktop\[DRM_ISLND]\pytests\tests)

## Примеры запуска

```powershell
pytest -m smoke
pytest -m contract
pytest -m "crm and negative"
pytest -m "accounting and not integration"
```
