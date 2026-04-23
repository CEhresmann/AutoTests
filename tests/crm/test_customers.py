from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.test_data import crm_customer_payload, crm_customer_update_payload
from utils.validators import validate_response_against_openapi


@pytest.mark.crm
@pytest.mark.integration
@pytest.mark.regression
def test_create_customer_with_minimal_pruned_payload(crm_client, crm_openapi: dict) -> None:
    payload = crm_customer_payload()
    response = crm_client.post("/api/v1/crm-external-integrations/customers", json=payload)
    assert response.status_code in {200, 207}, response.text
    schema = response_schema(crm_openapi, "/api/v1/crm-external-integrations/customers", "post", 200)
    data = validate_response_against_openapi(schema_document=crm_openapi, response=response, schema=schema)
    assert data["total"] == len(payload["customers"])
    assert data["success_count"] >= 1


@pytest.mark.crm
@pytest.mark.integration
@pytest.mark.regression
def test_update_customer_partial_payload(crm_client, crm_openapi: dict, test_data) -> None:
    payload = crm_customer_update_payload(test_data.customer_id)
    response = crm_client.patch("/api/v1/crm-external-integrations/customers", json=payload)
    assert response.status_code in {200, 207}, response.text
    schema = response_schema(crm_openapi, "/api/v1/crm-external-integrations/customers", "patch", 200)
    data = validate_response_against_openapi(schema_document=crm_openapi, response=response, schema=schema)
    assert data["total"] == 1
    assert data["customers"]

