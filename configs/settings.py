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
    authorization: str = ""
    authkey: str = ""

    @property
    def default_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.authorization:
            headers["Authorization"] = self.authorization
        if self.authkey:
            headers["AUTHKEY"] = self.authkey
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


@dataclass(frozen=True)
class BackendTestData:
    auth_key: str
    username: str
    password: str
    password_confirm: str
    email: str
    mail: str
    phone: str
    name: str
    code: str
    confirm_code: str
    correlation_id: str
    email_correlation_id: str
    user_id: str
    booking_id: str
    order_id: str
    ticket_id: str
    qrcode: str
    coordinates: str
    point_of_contact: str
    first_name: str
    last_name: str
    refresh_token: str
    agree_to_processing_personal_data: str
    is_confirm_policy: str
    is_mail_confirm: str
    is_phone_confirm: str
    is_subs: str


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

APP_CONTENT_SETTINGS = APISettings(
    name="app-content",
    base_url=os.getenv("DREAMCRM_APP_CONTENT_BASE_URL", "").rstrip("/"),
    api_key=os.getenv("DREAMCRM_APP_CONTENT_API_KEY", ""),
    authorization=os.getenv("DREAMCRM_APP_CONTENT_AUTHORIZATION", ""),
    authkey=os.getenv("DREAMCRM_APP_CONTENT_AUTHKEY", ""),
)

MOBILE_SETTINGS = APISettings(
    name="mobile",
    base_url=os.getenv("DREAMCRM_MOBILE_BASE_URL", "").rstrip("/"),
    api_key=os.getenv("DREAMCRM_MOBILE_API_KEY", ""),
    authorization=os.getenv("DREAMCRM_MOBILE_AUTHORIZATION", ""),
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

APP_CONTENT_TEST_DATA = BackendTestData(
    auth_key=os.getenv("DREAMCRM_APP_CONTENT_AUTH_KEY", ""),
    username=os.getenv("DREAMCRM_APP_CONTENT_USERNAME", ""),
    password=os.getenv("DREAMCRM_APP_CONTENT_PASSWORD", ""),
    password_confirm=os.getenv("DREAMCRM_APP_CONTENT_PASSWORD_CONFIRM", ""),
    email=os.getenv("DREAMCRM_APP_CONTENT_EMAIL", ""),
    mail=os.getenv("DREAMCRM_APP_CONTENT_MAIL", ""),
    phone=os.getenv("DREAMCRM_APP_CONTENT_PHONE", ""),
    name=os.getenv("DREAMCRM_APP_CONTENT_NAME", ""),
    code=os.getenv("DREAMCRM_APP_CONTENT_CODE", ""),
    confirm_code=os.getenv("DREAMCRM_APP_CONTENT_CONFIRM_CODE", ""),
    correlation_id=os.getenv("DREAMCRM_APP_CONTENT_CORRELATION_ID", ""),
    email_correlation_id=os.getenv("DREAMCRM_APP_CONTENT_EMAIL_CORRELATION_ID", ""),
    user_id=os.getenv("DREAMCRM_APP_CONTENT_USER_ID", ""),
    booking_id=os.getenv("DREAMCRM_APP_CONTENT_BOOKING_ID", ""),
    order_id=os.getenv("DREAMCRM_APP_CONTENT_ORDER_ID", ""),
    ticket_id=os.getenv("DREAMCRM_APP_CONTENT_TICKET_ID", ""),
    qrcode=os.getenv("DREAMCRM_APP_CONTENT_QRCODE", ""),
    coordinates=os.getenv("DREAMCRM_APP_CONTENT_COORDINATES", ""),
    point_of_contact=os.getenv("DREAMCRM_APP_CONTENT_POINT_OF_CONTACT", ""),
    first_name=os.getenv("DREAMCRM_APP_CONTENT_FIRST_NAME", ""),
    last_name=os.getenv("DREAMCRM_APP_CONTENT_LAST_NAME", ""),
    refresh_token=os.getenv("DREAMCRM_APP_CONTENT_REFRESH_TOKEN", ""),
    agree_to_processing_personal_data=os.getenv(
        "DREAMCRM_APP_CONTENT_AGREE_TO_PROCESSING_PERSONAL_DATA", ""
    ),
    is_confirm_policy=os.getenv("DREAMCRM_APP_CONTENT_IS_CONFIRM_POLICY", ""),
    is_mail_confirm=os.getenv("DREAMCRM_APP_CONTENT_IS_MAIL_CONFIRM", ""),
    is_phone_confirm=os.getenv("DREAMCRM_APP_CONTENT_IS_PHONE_CONFIRM", ""),
    is_subs=os.getenv("DREAMCRM_APP_CONTENT_IS_SUBS", ""),
)

MOBILE_TEST_DATA = BackendTestData(
    auth_key=os.getenv("DREAMCRM_MOBILE_AUTH_KEY", ""),
    username=os.getenv("DREAMCRM_MOBILE_USERNAME", ""),
    password=os.getenv("DREAMCRM_MOBILE_PASSWORD", ""),
    password_confirm=os.getenv("DREAMCRM_MOBILE_PASSWORD_CONFIRM", ""),
    email=os.getenv("DREAMCRM_MOBILE_EMAIL", ""),
    mail=os.getenv("DREAMCRM_MOBILE_MAIL", ""),
    phone=os.getenv("DREAMCRM_MOBILE_PHONE_FOR_AUTH", ""),
    name=os.getenv("DREAMCRM_MOBILE_NAME", ""),
    code=os.getenv("DREAMCRM_MOBILE_CODE", ""),
    confirm_code=os.getenv("DREAMCRM_MOBILE_CONFIRM_CODE", ""),
    correlation_id=os.getenv("DREAMCRM_MOBILE_CORRELATION_ID", ""),
    email_correlation_id=os.getenv("DREAMCRM_MOBILE_EMAIL_CORRELATION_ID", ""),
    user_id=os.getenv("DREAMCRM_MOBILE_USER_ID", ""),
    booking_id=os.getenv("DREAMCRM_MOBILE_BOOKING_ID", ""),
    order_id=os.getenv("DREAMCRM_MOBILE_ORDER_ID", ""),
    ticket_id=os.getenv("DREAMCRM_MOBILE_TICKET_ID", ""),
    qrcode=os.getenv("DREAMCRM_MOBILE_QRCODE", ""),
    coordinates=os.getenv("DREAMCRM_MOBILE_COORDINATES", ""),
    point_of_contact=os.getenv("DREAMCRM_MOBILE_POINT_OF_CONTACT", ""),
    first_name=os.getenv("DREAMCRM_MOBILE_FIRST_NAME", ""),
    last_name=os.getenv("DREAMCRM_MOBILE_LAST_NAME", ""),
    refresh_token=os.getenv("DREAMCRM_MOBILE_REFRESH_TOKEN", ""),
    agree_to_processing_personal_data=os.getenv(
        "DREAMCRM_MOBILE_AGREE_TO_PROCESSING_PERSONAL_DATA", ""
    ),
    is_confirm_policy=os.getenv("DREAMCRM_MOBILE_IS_CONFIRM_POLICY", ""),
    is_mail_confirm=os.getenv("DREAMCRM_MOBILE_IS_MAIL_CONFIRM", ""),
    is_phone_confirm=os.getenv("DREAMCRM_MOBILE_IS_PHONE_CONFIRM", ""),
    is_subs=os.getenv("DREAMCRM_MOBILE_IS_SUBS", ""),
)
