from __future__ import annotations

import pytest

from utils.openapi import response_schema
from utils.validators import validate_response_against_openapi


@pytest.mark.smoke
@pytest.mark.crm
@pytest.mark.parametrize("path", ["/api/v1/customers/ping", "/health"])
def test_crm_health_endpoints(crm_client, crm_openapi: dict, path: str) -> None:
    response = crm_client.get(path)
    assert response.status_code == 200, response.text
    schema = response_schema(crm_openapi, path, "get", 200)
    validate_response_against_openapi(schema_document=crm_openapi, response=response, schema=schema)


@pytest.mark.smoke
@pytest.mark.accounting
@pytest.mark.parametrize("path", ["/api/v1/accounting/ping", "/health"])
def test_accounting_health_endpoints(accounting_client, accounting_openapi: dict, path: str) -> None:
    response = accounting_client.get(path)
    assert response.status_code == 200, response.text
    schema = response_schema(accounting_openapi, path, "get", 200)
    validate_response_against_openapi(schema_document=accounting_openapi, response=response, schema=schema)

