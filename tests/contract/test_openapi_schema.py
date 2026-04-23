from __future__ import annotations

import pytest

from utils.openapi import request_body_schema


@pytest.mark.contract
@pytest.mark.parametrize(
    ("schema_name", "required_paths"),
    [
        (
            "crm_openapi",
            {
                "/api/v1/customers/ping",
                "/health",
                "/api/v1/crm-external-integrations/customers",
                "/api/v1/crm-external-integrations/customers/search",
                "/api/v1/crm-external-integrations/customer-actions",
                "/api/v1/crm-external-integrations/customer-actions/bulk",
            },
        ),
        (
            "accounting_openapi",
            {
                "/api/v1/accounting/ping",
                "/health",
                "/api/v1/accounting-external-api/product_category",
                "/api/v1/accounting-external-api/product",
                "/api/v1/accounting-external-api/product/bulk",
                "/api/v1/accounting-external-api/orders",
                "/api/v1/accounting-external-api/orders/{external_order_id}",
                "/api/v1/accounting-external-api/orders/calculate",
            },
        ),
    ],
)
def test_openapi_has_expected_paths(request, schema_name: str, required_paths: set[str]) -> None:
    document = request.getfixturevalue(schema_name)
    assert document["openapi"] == "3.1.0"
    assert required_paths.issubset(set(document["paths"]))


@pytest.mark.contract
@pytest.mark.parametrize(
    ("schema_name", "path", "method"),
    [
        ("crm_openapi", "/api/v1/crm-external-integrations/customers", "post"),
        ("crm_openapi", "/api/v1/crm-external-integrations/customers", "patch"),
        ("crm_openapi", "/api/v1/crm-external-integrations/customers/search", "post"),
        ("crm_openapi", "/api/v1/crm-external-integrations/customer-actions", "post"),
        ("crm_openapi", "/api/v1/crm-external-integrations/customer-actions/bulk", "post"),
        ("accounting_openapi", "/api/v1/accounting-external-api/product", "post"),
        ("accounting_openapi", "/api/v1/accounting-external-api/product/bulk", "post"),
        ("accounting_openapi", "/api/v1/accounting-external-api/orders", "post"),
        ("accounting_openapi", "/api/v1/accounting-external-api/orders/{external_order_id}", "patch"),
        ("accounting_openapi", "/api/v1/accounting-external-api/orders/calculate", "post"),
    ],
)
def test_mutating_operations_have_request_schema(request, schema_name: str, path: str, method: str) -> None:
    document = request.getfixturevalue(schema_name)
    assert request_body_schema(document, path, method) is not None


@pytest.mark.contract
@pytest.mark.parametrize("schema_name", ["crm_openapi", "accounting_openapi"])
def test_all_operations_have_declared_responses(request, schema_name: str) -> None:
    document = request.getfixturevalue(schema_name)
    for path, methods in document["paths"].items():
        for method, operation in methods.items():
            assert operation.get("responses"), f"{method.upper()} {path} has no responses"

