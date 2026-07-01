from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
OPENAPI_DIR = ROOT_DIR / "OpenAPI"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
REPORTS_DIR = ROOT_DIR / "reports"

load_dotenv(ROOT_DIR / ".env", override=False)


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        # Нечисловое значение (напр. system_name вместо id) — трактуем как «не задано»,
        # чтобы тест ушёл в skip, а не падал импорт всего пакета.
        return default


@dataclass(frozen=True)
class APISettings:
    name: str
    base_url: str
    api_key: str
    authorization: str = ""
    authkey: str = ""
    contact_point_id: str = ""

    @property
    def default_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.authorization:
            headers["Authorization"] = self.authorization
        if self.authkey:
            headers["AUTHKEY"] = self.authkey
        # Accounting требует contact_point_id заголовком во всех запросах
        # (см. DreamCRM_Contracts.md, раздел 0). Без него часть GET -> 400.
        if self.contact_point_id:
            headers["contact_point_id"] = self.contact_point_id
        return headers


@dataclass(frozen=True)
class TestData:
    email: str
    customer_id: int
    website_id: str
    discount_card_number: str
    mindbox_id: str
    mobile_phone: str
    action_template_system_name: str
    contact_point_id: str | None
    promotion_order_id: int | None


CRM_SETTINGS = APISettings(
    name="crm",
    base_url=os.getenv(
        "DREAMCRM_BASE_URL",
        "https://crmstage-external-integrations-di-dev.dreamisland.ru",
    ).rstrip("/"),
    api_key=os.getenv(
        "DREAMCRM_API_KEY",
        "41577ef4-29b1-48d5-a318-3ff309fbde67",
    ),
)

ACCOUNTING_SETTINGS = APISettings(
    name="accounting",
    base_url=os.getenv(
        "DREAMCRM_ACCOUNTING_BASE_URL",
        "https://crmstage-accounting-external-api-di-dev.dreamisland.ru",
    ).rstrip("/"),
    api_key=os.getenv(
        "DREAMCRM_ACCOUNTING_API_KEY",
        "41577ef4-29b1-48d5-a318-3ff309fbde67",
    ),
    contact_point_id=os.getenv("DREAMCRM_CONTACT_POINT_ID", "ecom_web"),
)

CRM_CAMPAIGN_ID = _int_env("DREAMCRM_CRM_CAMPAIGN_ID", 0) or None
# pool_id по спеке и стенду — integer (system_name строкой стенд отклоняет 422).
ACCOUNTING_PROMOCODE_POOL_ID = _int_env("DREAMCRM_ACCOUNTING_PROMOCODE_POOL_ID", 0) or None
ACCOUNTING_PROMOTION_ID = _int_env("DREAMCRM_ACCOUNTING_PROMOTION_ID", 0) or None
ACCOUNTING_ORDER_ITEM_ID = _int_env("DREAMCRM_ACCOUNTING_ORDER_ITEM_ID", 0) or None
ACCOUNTING_EXTERNAL_ORDER_ID = os.getenv("DREAMCRM_ACCOUNTING_EXTERNAL_ORDER_ID") or None
ACCOUNTING_GIFT_CERT_TRANSACTION_ID = os.getenv("DREAMCRM_ACCOUNTING_GIFT_CERT_TRANSACTION_ID") or None
ACCOUNTING_GIFT_CERT_NOMINAL = _int_env("DREAMCRM_ACCOUNTING_GIFT_CERT_NOMINAL", 0) or None

TEST_DATA = TestData(
    email=os.getenv("DREAMCRM_EMAIL", "n.tadzhibaeva@gmail.com"),
    customer_id=_int_env("DREAMCRM_CUSTOMER_ID", 554781),
    website_id=os.getenv("DREAMCRM_WEBSITE_ID", "1000636"),
    discount_card_number=os.getenv("DREAMCRM_DISCOUNT_CARD_NUMBER", "1000636"),
    mindbox_id=os.getenv("DREAMCRM_MINDBOX_ID", "1117930"),
    mobile_phone=os.getenv("DREAMCRM_MOBILE_PHONE", "+79258935369"),
    action_template_system_name=os.getenv(
        "DREAMCRM_ACTION_TEMPLATE_SYSTEM_NAME",
        "ZaprosVosstanovleniyaParolya",
    ),
    contact_point_id=os.getenv("DREAMCRM_CONTACT_POINT_ID") or None,
    promotion_order_id=_int_env("DREAMCRM_PROMOTION_ORDER_ID", 0) or None,
)
