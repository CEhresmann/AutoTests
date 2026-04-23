from __future__ import annotations

import pytest


@pytest.mark.negative
@pytest.mark.crm
def test_customers_create_rejects_missing_required_array(crm_client) -> None:
    response = crm_client.post("/api/v1/crm-external-integrations/customers", json={})
    assert response.status_code == 422, response.text


@pytest.mark.negative
@pytest.mark.crm
def test_customer_action_rejects_missing_required_fields(crm_client) -> None:
    response = crm_client.post("/api/v1/crm-external-integrations/customer-actions", json={"email": "test@example.com"})
    assert response.status_code == 422, response.text


@pytest.mark.negative
@pytest.mark.accounting
def test_product_create_rejects_missing_external_id(accounting_client) -> None:
    response = accounting_client.post(
        "/api/v1/accounting-external-api/product",
        json={"external_system": "Ecom"},
    )
    assert response.status_code == 422, response.text


@pytest.mark.negative
@pytest.mark.accounting
def test_calculate_rejects_wrong_scalar_type(accounting_client) -> None:
    response = accounting_client.post(
        "/api/v1/accounting-external-api/orders/calculate",
        json={"customer_id": "not-an-integer"},
    )
    assert response.status_code == 422, response.text

