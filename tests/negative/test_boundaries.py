from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.validators import validate_response_against_openapi


@pytest.mark.negative
@pytest.mark.accounting
def test_product_category_boundary_paging(accounting_client, accounting_openapi: dict) -> None:
    response = accounting_client.get(
        "/api/v1/accounting-external-api/product_category",
        params={"limit": 1, "offset": 0},
    )
    assert response.status_code == 200, response.text
    schema = response_schema(
        accounting_openapi,
        "/api/v1/accounting-external-api/product_category",
        "get",
        200,
    )
    payload = validate_response_against_openapi(
        schema_document=accounting_openapi,
        response=response,
        schema=schema,
    )
    assert payload["limit"] == 1
    assert payload["offset"] == 0


@pytest.mark.negative
@pytest.mark.crm
def test_customer_search_boundary_page_size(crm_client, crm_openapi: dict, test_data) -> None:
    response = crm_client.post(
        "/api/v1/crm-external-integrations/customers/search",
        json={"filter": {"email": test_data.email}, "page": 1, "page_size": 1},
    )
    assert response.status_code == 200, response.text
    schema = response_schema(
        crm_openapi,
        "/api/v1/crm-external-integrations/customers/search",
        "post",
        200,
    )
    payload = validate_response_against_openapi(
        schema_document=crm_openapi,
        response=response,
        schema=schema,
    )
    assert payload["page_size"] == 1
    assert payload["page"] == 1


@pytest.mark.negative
@pytest.mark.accounting
def test_orders_list_rejects_invalid_limit_type(accounting_client) -> None:
    response = accounting_client.get(
        "/api/v1/accounting-external-api/orders",
        params={"limit": "wrong-type"},
    )
    assert response.status_code == 422, response.text

