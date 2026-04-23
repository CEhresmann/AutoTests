from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
OPENAPI_DIR = ROOT_DIR / "OpenApi"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
REPORTS_DIR = ROOT_DIR / "reports"

load_dotenv(ROOT_DIR / ".env", override=False)


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


@dataclass(frozen=True)
class APISettings:
    name: str
    base_url: str
    api_key: str

    @property
    def default_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
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
)

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
