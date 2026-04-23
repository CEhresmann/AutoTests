from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.test_data import accounting_bulk_product_payload, accounting_product_payload
from utils.validators import validate_response_against_openapi


@pytest.mark.accounting
@pytest.mark.regression
def test_list_products(accounting_client, accounting_openapi: dict) -> None:
    response = accounting_client.get(
        "/api/v1/accounting-external-api/product",
        params={"limit": 1, "offset": 0},
    )
    assert response.status_code == 200, response.text
    schema = response_schema(accounting_openapi, "/api/v1/accounting-external-api/product", "get", 200)
    payload = validate_response_against_openapi(
        schema_document=accounting_openapi,
        response=response,
        schema=schema,
    )
    assert payload["limit"] == 1
    assert payload["offset"] == 0


@pytest.mark.accounting
@pytest.mark.integration
@pytest.mark.regression
def test_create_product(accounting_client, accounting_openapi: dict) -> None:
    payload = accounting_product_payload()
    response = accounting_client.post("/api/v1/accounting-external-api/product", json=payload)
    assert response.status_code == 201, response.text
    schema = response_schema(accounting_openapi, "/api/v1/accounting-external-api/product", "post", 201)
    data = validate_response_against_openapi(schema_document=accounting_openapi, response=response, schema=schema)
    assert data["external_id"] == payload["external_id"]
    assert data["id"] > 0


@pytest.mark.accounting
@pytest.mark.bulk
@pytest.mark.integration
@pytest.mark.regression
def test_create_products_bulk(accounting_client, accounting_openapi: dict) -> None:
    payload = accounting_bulk_product_payload()
    response = accounting_client.post("/api/v1/accounting-external-api/product/bulk", json=payload)
    assert response.status_code == 200, response.text
    schema = response_schema(accounting_openapi, "/api/v1/accounting-external-api/product/bulk", "post", 200)
    data = validate_response_against_openapi(schema_document=accounting_openapi, response=response, schema=schema)
    assert data["total"] == len(payload["items"])
    assert data["success_count"] + data["error_count"] == data["total"]

