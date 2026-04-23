from __future__ import annotations

import pytest


@pytest.mark.negative
@pytest.mark.crm
@pytest.mark.parametrize("headers", [{"X-API-Key": ""}, {"X-API-Key": "invalid-key"}])
def test_crm_requires_valid_api_key(crm_client, headers: dict[str, str]) -> None:
    response = crm_client.post(
        "/api/v1/crm-external-integrations/customers/search",
        headers=headers,
        json={"filter": {"email": "autotest@example.com"}},
    )
    assert response.status_code == 401, response.text


@pytest.mark.negative
@pytest.mark.accounting
@pytest.mark.parametrize("headers", [{"X-API-Key": ""}, {"X-API-Key": "invalid-key"}])
def test_accounting_requires_valid_api_key(accounting_client, headers: dict[str, str]) -> None:
    response = accounting_client.get(
        "/api/v1/accounting-external-api/product",
        headers=headers,
        params={"limit": 1, "offset": 0},
    )
    assert response.status_code == 401, response.text
