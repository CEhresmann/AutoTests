from __future__ import annotations

import pytest

from configs.settings import ACCOUNTING_GIFT_CERT_TRANSACTION_ID
from utils.openapi import response_schema
from utils.test_data import (
    accounting_gift_certificate_credit_payload,
    accounting_gift_certificate_debit_payload,
    accounting_gift_certificate_refund_payload,
    accounting_gift_certificate_validate_payload,
)
from utils.validators import validate_response_against_openapi


requires_cert = pytest.mark.skipif(
    not ACCOUNTING_GIFT_CERT_TRANSACTION_ID,
    reason="Set DREAMCRM_ACCOUNTING_GIFT_CERT_TRANSACTION_ID (реальный номер сертификата)",
)


@pytest.mark.accounting
@pytest.mark.regression
@requires_cert
def test_validate_gift_certificate(accounting_client, accounting_openapi: dict) -> None:
    payload = accounting_gift_certificate_validate_payload(ACCOUNTING_GIFT_CERT_TRANSACTION_ID)
    response = accounting_client.post(
        "/api/v1/accounting-external-api/gift-certificates/validate",
        json=payload,
    )
    assert response.status_code == 200, response.text
    schema = response_schema(
        accounting_openapi, "/api/v1/accounting-external-api/gift-certificates/validate", "post", 200
    )
    data = validate_response_against_openapi(schema_document=accounting_openapi, response=response, schema=schema)
    assert data["certificate_number"] == ACCOUNTING_GIFT_CERT_TRANSACTION_ID
    assert "is_valid" in data
    assert "status" in data


@pytest.mark.accounting
@pytest.mark.negative
@pytest.mark.regression
def test_validate_gift_certificate_requires_identifier(accounting_client) -> None:
    # без certificate_id/certificate_number -> 422 (контракт валидации)
    response = accounting_client.post(
        "/api/v1/accounting-external-api/gift-certificates/validate",
        json={"transaction_id": "autotest-no-id"},
    )
    assert response.status_code == 422, response.text


@pytest.mark.accounting
@pytest.mark.integration
@pytest.mark.regression
@requires_cert
@pytest.mark.xfail(
    reason="Требуется сертификат в статусе 'activated'. Текущий тестовый сертификат "
    "в статусе 'not_activated', поэтому debit/credit/refund возвращают 422 "
    "('Certificate status is not activated'). Нужны данные активированной карты.",
    strict=False,
)
@pytest.mark.parametrize(
    ("path", "payload_factory"),
    [
        ("/api/v1/accounting-external-api/gift-certificates/debit", accounting_gift_certificate_debit_payload),
        ("/api/v1/accounting-external-api/gift-certificates/credit", accounting_gift_certificate_credit_payload),
        ("/api/v1/accounting-external-api/gift-certificates/refund", accounting_gift_certificate_refund_payload),
    ],
)
def test_gift_certificate_operations_require_activated(accounting_client, path, payload_factory) -> None:
    payload = payload_factory()
    payload["certificate_number"] = ACCOUNTING_GIFT_CERT_TRANSACTION_ID
    response = accounting_client.post(path, json=payload)
    assert response.status_code == 200, response.text
