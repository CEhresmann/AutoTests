from __future__ import annotations

import pytest

from utils.openapi import operation_schema


@pytest.mark.contract
@pytest.mark.crm
@pytest.mark.parametrize(
    ("path", "method", "expected_statuses"),
    [
        ("/api/v1/customers/ping", "get", {"200"}),
        ("/health", "get", {"200"}),
        ("/api/v1/crm-external-integrations/customers", "post", {"200", "207", "400", "401", "422", "429", "500"}),
        ("/api/v1/crm-external-integrations/customers", "patch", {"200", "207", "400", "401", "422", "429", "500"}),
        ("/api/v1/crm-external-integrations/customers/search", "post", {"200", "400", "401", "422", "429", "500"}),
        ("/api/v1/crm-external-integrations/customer-actions", "post", {"201", "401", "422", "429", "500"}),
        ("/api/v1/crm-external-integrations/customer-actions/bulk", "post", {"200", "422"}),
    ],
)
def test_crm_operations_match_work_plan(crm_openapi: dict, path: str, method: str, expected_statuses: set[str]) -> None:
    operation = operation_schema(crm_openapi, path, method)
    assert set(operation["responses"]) == expected_statuses

