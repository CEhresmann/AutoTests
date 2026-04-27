from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.validators import validate_response_against_openapi


@pytest.mark.crm
@pytest.mark.integration
@pytest.mark.regression
def test_search_customer_by_unknown_website_id_returns_empty_page_not_500(crm_client, crm_openapi: dict) -> None:
    payload = {
        "filter": {
            "website_id": "WS-0999",
        },
        "page": 1,
        "page_size": 20,
    }
    response = crm_client.post("/api/v1/crm-external-integrations/customers/search", json=payload, timeout=10)
    assert response.status_code == 200, response.text
    schema = response_schema(crm_openapi, "/api/v1/crm-external-integrations/customers/search", "post", 200)
    data = validate_response_against_openapi(schema_document=crm_openapi, response=response, schema=schema)
    assert data["total"] == 0
    assert data["customers"] == []


@pytest.mark.crm
@pytest.mark.integration
@pytest.mark.regression
def test_search_customer_by_ids_filters_exact_customer(crm_client, crm_openapi: dict, test_data) -> None:
    payload = {
        "filter": {
            "ids": [test_data.customer_id],
        },
        "page": 1,
        "page_size": 20,
    }
    response = crm_client.post("/api/v1/crm-external-integrations/customers/search", json=payload, timeout=10)
    assert response.status_code == 200, response.text
    schema = response_schema(crm_openapi, "/api/v1/crm-external-integrations/customers/search", "post", 200)
    data = validate_response_against_openapi(schema_document=crm_openapi, response=response, schema=schema)
    assert data["total"] <= 1
    assert all(customer["id"] == test_data.customer_id for customer in data["customers"])


@pytest.mark.crm
@pytest.mark.negative
@pytest.mark.regression
def test_search_customer_rejects_undocumented_id_scalar_filter(crm_client, test_data) -> None:
    payload = {
        "filter": {
            "id": test_data.customer_id,
        },
        "page": 1,
        "page_size": 20,
    }
    response = crm_client.post("/api/v1/crm-external-integrations/customers/search", json=payload, timeout=10)
    assert response.status_code in {400, 422}, response.text
