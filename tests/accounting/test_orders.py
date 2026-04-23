from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.test_data import (
    accounting_calculate_payload,
    accounting_order_payload,
    accounting_order_update_payload,
)
from utils.validators import validate_response_against_openapi


@pytest.mark.accounting
@pytest.mark.regression
def test_list_orders(accounting_client, accounting_openapi: dict) -> None:
    response = accounting_client.get(
        "/api/v1/accounting-external-api/orders",
        params={"limit": 1, "offset": 0},
    )
    assert response.status_code == 200, response.text
    schema = response_schema(accounting_openapi, "/api/v1/accounting-external-api/orders", "get", 200)
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
def test_create_and_update_order(accounting_client, accounting_openapi: dict) -> None:
    from configs.settings import TEST_DATA

    create_payload = accounting_order_payload()
    create_response = accounting_client.post("/api/v1/accounting-external-api/orders", json=create_payload)
    assert create_response.status_code == 201, create_response.text
    create_schema = response_schema(accounting_openapi, "/api/v1/accounting-external-api/orders", "post", 201)
    create_data = validate_response_against_openapi(
        schema_document=accounting_openapi,
        response=create_response,
        schema=create_schema,
    )
    assert create_data["external_order_id"] == create_payload["external_order_id"]
    assert create_data["status"] == "cart"

    get_response = accounting_client.get(
        f"/api/v1/accounting-external-api/orders/{create_payload['external_order_id']}"
    )
    assert get_response.status_code == 200, get_response.text
    get_schema = response_schema(
        accounting_openapi,
        "/api/v1/accounting-external-api/orders/{external_order_id}",
        "get",
        200,
    )
    get_data = validate_response_against_openapi(
        schema_document=accounting_openapi,
        response=get_response,
        schema=get_schema,
    )
    assert get_data["order"]["external_order_id"] == create_payload["external_order_id"]

    if not TEST_DATA.contact_point_id:
        pytest.skip("Set DREAMCRM_CONTACT_POINT_ID to verify PATCH /orders/{external_order_id}")

    update_response = accounting_client.patch(
        f"/api/v1/accounting-external-api/orders/{create_payload['external_order_id']}",
        json=accounting_order_update_payload(TEST_DATA.contact_point_id),
    )
    assert update_response.status_code == 200, update_response.text
    update_schema = response_schema(
        accounting_openapi,
        "/api/v1/accounting-external-api/orders/{external_order_id}",
        "patch",
        200,
    )
    update_data = validate_response_against_openapi(
        schema_document=accounting_openapi,
        response=update_response,
        schema=update_schema,
    )
    assert update_data["external_order_id"] == create_payload["external_order_id"]
    assert update_data["status"] == "new"


@pytest.mark.accounting
@pytest.mark.integration
@pytest.mark.regression
def test_calculate_order(accounting_client, accounting_openapi: dict) -> None:
    payload = accounting_calculate_payload()
    response = accounting_client.post("/api/v1/accounting-external-api/orders/calculate", json=payload)
    assert response.status_code == 200, response.text
    schema = response_schema(accounting_openapi, "/api/v1/accounting-external-api/orders/calculate", "post", 200)
    data = validate_response_against_openapi(schema_document=accounting_openapi, response=response, schema=schema)
    assert isinstance(data.get("items", []), list)
    assert "errors" in data
