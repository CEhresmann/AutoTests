from __future__ import annotations

import pytest

from configs.settings import ACCOUNTING_SETTINGS, CRM_SETTINGS, TEST_DATA
from utils.api_client import APIClient
from utils.openapi import (
    ACCOUNTING_SCHEMA_FILE,
    CRM_SCHEMA_FILE,
    load_openapi_schema,
)


@pytest.fixture(scope="session")
def crm_client() -> APIClient:
    return APIClient(CRM_SETTINGS)


@pytest.fixture(scope="session")
def accounting_client() -> APIClient:
    return APIClient(ACCOUNTING_SETTINGS)


@pytest.fixture(scope="session")
def crm_openapi() -> dict:
    return load_openapi_schema(CRM_SCHEMA_FILE)


@pytest.fixture(scope="session")
def accounting_openapi() -> dict:
    return load_openapi_schema(ACCOUNTING_SCHEMA_FILE)


@pytest.fixture(scope="session")
def test_data():
    return TEST_DATA

