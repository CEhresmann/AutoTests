from __future__ import annotations

import pytest

from configs.settings import TEST_DATA
from utils.openapi import response_schema
from utils.test_data import (
    accounting_bonus_accrue_payload,
    accounting_bonus_hold_payload,
    accounting_bonus_hold_release_payload,
    accounting_order_payload,
)
from utils.validators import validate_response_against_openapi


@pytest.mark.accounting
@pytest.mark.regression
def test_bonus_balance_by_customer_id(accounting_client, accounting_openapi: dict) -> None:
    response = accounting_client.get(
        "/api/v1/accounting-external-api/bonuses/balance",
        params={"customer_id": TEST_DATA.customer_id, "include_holds": "true"},
    )
    assert response.status_code == 200, response.text
    schema = response_schema(accounting_openapi, "/api/v1/accounting-external-api/bonuses/balance", "get", 200)
    data = validate_response_against_openapi(schema_document=accounting_openapi, response=response, schema=schema)
    # контракт: либо вложенный balance{total,available,held}, либо плоский формат
    balance = data.get("balance", data)
    assert "available" in balance and "held" in balance and "total" in balance


@pytest.mark.accounting
@pytest.mark.regression
def test_bonus_balance_by_website_id(accounting_client) -> None:
    response = accounting_client.get(
        "/api/v1/accounting-external-api/bonuses/balance",
        params={"website_id": TEST_DATA.website_id, "include_holds": "true"},
    )
    assert response.status_code == 200, response.text


@pytest.mark.accounting
@pytest.mark.regression
def test_customer_points_history(accounting_client, accounting_openapi: dict) -> None:
    response = accounting_client.get(
        "/api/v1/accounting-external-api/bonuses/customer-points-history",
        params={"customer_id": TEST_DATA.customer_id, "limit": 10, "offset": 0},
    )
    assert response.status_code == 200, response.text
    schema = response_schema(
        accounting_openapi, "/api/v1/accounting-external-api/bonuses/customer-points-history", "get", 200
    )
    data = validate_response_against_openapi(schema_document=accounting_openapi, response=response, schema=schema)
    assert isinstance(data["items"], list)
    assert data["limit"] == 10
    assert data["offset"] == 0


@pytest.mark.accounting
@pytest.mark.integration
@pytest.mark.regression
def test_accrue_customer_points(accounting_client, accounting_openapi: dict) -> None:
    payload = accounting_bonus_accrue_payload()
    response = accounting_client.post(
        "/api/v1/accounting-external-api/bonuses/accrue-customer-points",
        json=payload,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data.get("id"), data


@pytest.mark.accounting
@pytest.mark.integration
@pytest.mark.regression
def test_bonus_hold_and_release(accounting_client) -> None:
    # создаём заказ, чтобы привязать hold к валидному external_order_id
    order = accounting_order_payload()
    order_resp = accounting_client.post("/api/v1/accounting-external-api/orders", json=order)
    assert order_resp.status_code == 201, order_resp.text

    hold_resp = accounting_client.post(
        "/api/v1/accounting-external-api/bonuses/hold",
        json=accounting_bonus_hold_payload(order["external_order_id"]),
    )
    assert hold_resp.status_code == 201, hold_resp.text
    hold_id = hold_resp.json()["hold_id"]

    release_resp = accounting_client.patch(
        f"/api/v1/accounting-external-api/bonuses/hold/{hold_id}",
        json=accounting_bonus_hold_release_payload(),
    )
    assert release_resp.status_code == 200, release_resp.text


@pytest.mark.accounting
@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.xfail(
    reason="Дефект стенда: POST /bonuses/activate-customer-points возвращает 500 "
    "(greenlet_spawn / SQLAlchemy async IO) на корректном bonus_id из accrue. "
    "Когда стенд починят — станет XPASS.",
    strict=False,
)
def test_activate_customer_points(accounting_client) -> None:
    accrue = accounting_client.post(
        "/api/v1/accounting-external-api/bonuses/accrue-customer-points",
        json=accounting_bonus_accrue_payload(),
    )
    assert accrue.status_code == 201, accrue.text
    bonus_id = accrue.json()["id"]

    response = accounting_client.post(
        "/api/v1/accounting-external-api/bonuses/activate-customer-points",
        json={"bonus_id": bonus_id},
    )
    assert response.status_code == 200, response.text
