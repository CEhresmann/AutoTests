from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.test_data import crm_customer_search_payload
from utils.validators import validate_response_against_openapi


@pytest.mark.crm
@pytest.mark.regression
def test_search_customer_by_email(crm_client, crm_openapi: dict, test_data) -> None:
    payload = crm_customer_search_payload()
    response = crm_client.post("/api/v1/crm-external-integrations/customers/search", json=payload)
    assert response.status_code == 200, response.text
    schema = response_schema(crm_openapi, "/api/v1/crm-external-integrations/customers/search", "post", 200)
    data = validate_response_against_openapi(schema_document=crm_openapi, response=response, schema=schema)
    assert data["page"] == payload["page"]
    assert data["page_size"] == payload["page_size"]
    assert any(customer.get("email") == test_data.email for customer in data["customers"])

