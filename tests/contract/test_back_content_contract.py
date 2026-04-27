from __future__ import annotations

import pytest

from utils.openapi import request_body_schema


@pytest.mark.contract
@pytest.mark.app_content
def test_app_content_openapi_has_expected_shape(app_content_openapi: dict) -> None:
    assert app_content_openapi["openapi"].startswith("3.0.")
    assert len(app_content_openapi["paths"]) >= 150
    assert "/api/app/content/booking/{id}/view" in app_content_openapi["paths"]
    assert "/api/app/buying/view" in app_content_openapi["paths"]


@pytest.mark.contract
@pytest.mark.mobile
def test_mobile_openapi_has_expected_shape(mobile_openapi: dict) -> None:
    assert mobile_openapi["openapi"].startswith("3.0.")
    assert len(mobile_openapi["paths"]) >= 80
    assert "/api/mobile/v1/buying/view" in mobile_openapi["paths"]
    assert "/api/mobile/v1/content/event/list" in mobile_openapi["paths"]


@pytest.mark.contract
@pytest.mark.app_content
@pytest.mark.mobile
@pytest.mark.parametrize("schema_name", ["app_content_openapi", "mobile_openapi"])
def test_backend_operations_have_declared_responses(request, schema_name: str) -> None:
    document = request.getfixturevalue(schema_name)
    for path, methods in document["paths"].items():
        for method, operation in methods.items():
            assert operation.get("responses"), f"{method.upper()} {path} has no responses"


@pytest.mark.contract
@pytest.mark.app_content
@pytest.mark.mobile
@pytest.mark.parametrize("schema_name", ["app_content_openapi", "mobile_openapi"])
def test_backend_mutating_operations_have_request_body_when_declared(request, schema_name: str) -> None:
    document = request.getfixturevalue(schema_name)
    for path, methods in document["paths"].items():
        for method in methods:
            if method.lower() not in {"post", "put", "patch"}:
                continue
            operation = document["paths"][path][method]
            if "requestBody" in operation:
                assert request_body_schema(document, path, method) is not None
