from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.test_data import crm_customer_action_bulk_payload, crm_customer_action_payload
from utils.validators import validate_response_against_openapi


@pytest.mark.crm
@pytest.mark.integration
@pytest.mark.regression
def test_create_customer_action(crm_client, crm_openapi: dict) -> None:
    payload = crm_customer_action_payload()
    response = crm_client.post("/api/v1/crm-external-integrations/customer-actions", json=payload)
    assert response.status_code == 201, response.text
    schema = response_schema(crm_openapi, "/api/v1/crm-external-integrations/customer-actions", "post", 201)
    data = validate_response_against_openapi(schema_document=crm_openapi, response=response, schema=schema)
    assert data["action_template_id"] > 0


@pytest.mark.crm
@pytest.mark.bulk
@pytest.mark.integration
@pytest.mark.regression
def test_create_customer_actions_bulk(crm_client, crm_openapi: dict) -> None:
    payload = crm_customer_action_bulk_payload()
    response = crm_client.post("/api/v1/crm-external-integrations/customer-actions/bulk", json=payload)
    assert response.status_code in {200, 207}, response.text
    schema = response_schema(crm_openapi, "/api/v1/crm-external-integrations/customer-actions/bulk", "post", 200)
    data = validate_response_against_openapi(schema_document=crm_openapi, response=response, schema=schema)
    assert data["total"] == len(payload["actions"])
    assert data["success_count"] + data["error_count"] == data["total"]
