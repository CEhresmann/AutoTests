from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.test_data import accounting_order_payload, accounting_promotion_preview_payload
from utils.validators import validate_response_against_openapi


@pytest.mark.accounting
@pytest.mark.integration
@pytest.mark.regression
def test_preview_promotion_application(accounting_client, accounting_openapi: dict) -> None:
    from configs.settings import TEST_DATA

    if not TEST_DATA.promotion_order_id:
        pytest.skip("Set DREAMCRM_PROMOTION_ORDER_ID to verify POST /promotions/preview")

    preview_response = accounting_client.post(
        "/api/v1/accounting-external-api/promotions/preview",
        json=accounting_promotion_preview_payload(TEST_DATA.promotion_order_id),
    )
    assert preview_response.status_code == 200, preview_response.text
    schema = response_schema(accounting_openapi, "/api/v1/accounting-external-api/promotions/preview", "post", 200)
    data = validate_response_against_openapi(
        schema_document=accounting_openapi,
        response=preview_response,
        schema=schema,
    )
    assert isinstance(data, dict)
