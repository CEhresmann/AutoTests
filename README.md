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
