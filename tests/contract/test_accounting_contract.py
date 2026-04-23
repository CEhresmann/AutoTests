from __future__ import annotations

import pytest

from utils.openapi import operation_schema


@pytest.mark.contract
@pytest.mark.accounting
@pytest.mark.parametrize(
    ("path", "method", "expected_statuses"),
    [
        ("/api/v1/accounting/ping", "get", {"200"}),
        ("/health", "get", {"200"}),
        ("/api/v1/accounting-external-api/product_category", "get", {"200", "401", "422", "500"}),
        ("/api/v1/accounting-external-api/product", "get", {"200", "401", "422", "500"}),
        ("/api/v1/accounting-external-api/product", "post", {"201", "400", "401", "409", "422", "500"}),
        ("/api/v1/accounting-external-api/product/bulk", "post", {"200", "400", "401", "422", "500"}),
        ("/api/v1/accounting-external-api/orders", "get", {"200", "422"}),
        ("/api/v1/accounting-external-api/orders", "post", {"201", "422"}),
        ("/api/v1/accounting-external-api/orders/{external_order_id}", "get", {"200", "422"}),
        ("/api/v1/accounting-external-api/orders/{external_order_id}", "patch", {"200", "422"}),
        ("/api/v1/accounting-external-api/orders/calculate", "post", {"200", "422"}),
    ],
)
def test_accounting_operations_match_work_plan(
    accounting_openapi: dict,
    path: str,
    method: str,
    expected_statuses: set[str],
) -> None:
    operation = operation_schema(accounting_openapi, path, method)
    assert set(operation["responses"]) == expected_statuses

