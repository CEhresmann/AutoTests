from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import quote

import pytest

from utils.openapi import load_schema_registry, resolve_ref
from utils.test_data import (
    accounting_bulk_product_payload,
    accounting_calculate_payload,
    accounting_order_payload,
    accounting_product_payload,
    crm_customer_action_bulk_payload,
    crm_customer_action_payload,
    crm_customer_payload,
    crm_customer_search_payload,
    crm_customer_update_payload,
)


SERVICE_FIXTURES = {
    "crm": ("crm_client", "crm_openapi", "test_data"),
    "accounting": ("accounting_client", "accounting_openapi", "test_data"),
    "app-content": ("app_content_client", "app_content_openapi", "app_content_test_data"),
    "mobile": ("mobile_client", "mobile_openapi", "mobile_test_data"),
}

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
BUSINESS_STATUSES = {400, 401, 403, 404, 405, 409, 422, 429}
KNOWN_JSON_BODY_FACTORIES = {
    ("crm", "POST", "/api/v1/crm-external-integrations/customers"): crm_customer_payload,
    ("crm", "POST", "/api/v1/crm-external-integrations/customers/search"): crm_customer_search_payload,
    ("crm", "POST", "/api/v1/crm-external-integrations/customer-actions"): crm_customer_action_payload,
    ("crm", "POST", "/api/v1/crm-external-integrations/customer-actions/bulk"): crm_customer_action_bulk_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/product"): accounting_product_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/product/bulk"): accounting_bulk_product_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/orders"): accounting_order_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/orders/calculate"): accounting_calculate_payload,
}


def iter_openapi_operations() -> list[pytest.ParamSpec]:
    operations: list[pytest.ParamSpec] = []
    for service, document in load_schema_registry().items():
        for path, methods in document["paths"].items():
            for method in methods:
                operations.append(
                    pytest.param(
                        service,
                        method.upper(),
                        path,
                        id=f"{service}:{method.upper()} {path}",
                    )
                )
    return operations


def _data_value(data: Any, *names: str) -> str:
    for name in names:
        if hasattr(data, name):
            value = getattr(data, name)
            if value not in {None, ""}:
                return str(value)
    return ""


def _sample_value(name: str, schema: dict[str, Any] | None, data: Any) -> Any:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    direct = _data_value(data, normalized)
    if direct:
        return direct

    aliases = {
        "id": ("booking_id", "customer_id", "user_id"),
        "orderid": ("order_id", "promotion_order_id"),
        "order_id": ("order_id", "promotion_order_id"),
        "ticketid": ("ticket_id",),
        "ticket_id": ("ticket_id",),
        "external_order_id": ("promotion_order_id", "order_id"),
        "token": ("refresh_token", "auth_key"),
        "auth_key": ("auth_key",),
        "authorization": ("authorization",),
        "authkey": ("auth_key",),
        "confirmcode": ("confirm_code",),
        "confirm_code": ("confirm_code",),
        "correlationid": ("correlation_id",),
        "correlation_id": ("correlation_id",),
        "emailcorrelationid": ("email_correlation_id",),
        "email_correlation_id": ("email_correlation_id",),
        "userid": ("user_id", "customer_id"),
        "user_id": ("user_id", "customer_id"),
        "phone": ("phone", "mobile_phone"),
        "mail": ("mail", "email"),
        "email": ("email",),
        "username": ("username", "email"),
        "password": ("password",),
        "passwordconfirm": ("password_confirm", "password"),
        "password_confirm": ("password_confirm", "password"),
        "qrcode": ("qrcode",),
        "coordinates": ("coordinates",),
        "pointofcontact": ("point_of_contact",),
        "point_of_contact": ("point_of_contact",),
        "firstname": ("first_name",),
        "first_name": ("first_name",),
        "lastname": ("last_name",),
        "last_name": ("last_name",),
    }
    alias_value = _data_value(data, *aliases.get(normalized, ()))
    if alias_value:
        return alias_value

    if schema:
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]
        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]
        schema_format = schema.get("format")
        if schema_format == "date-time":
            return "2026-01-01T00:00:00Z"
        if schema_format == "date":
            return "2026-01-01"
        schema_type = schema.get("type")
        if schema_type in {"integer", "number"}:
            return 1
        if schema_type == "boolean":
            return True
        if schema_type == "array":
            return []

    return "autotest"


def _replace_path_params(path: str, operation: dict[str, Any], data: Any) -> str:
    parameters = {param["name"]: param for param in operation.get("parameters", []) if param.get("in") == "path"}

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        parameter = parameters.get(name, {})
        value = _sample_value(name, parameter.get("schema"), data)
        return quote(str(value), safe="")

    return re.sub(r"\{([^}]+)\}", replace, path)


def _collect_params(operation: dict[str, Any], data: Any) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for parameter in operation.get("parameters", []):
        location = parameter.get("in")
        if location in {"path", "header"}:
            continue
        schema = parameter.get("schema", {})
        if parameter.get("required") or "default" in schema:
            params[parameter["name"]] = _sample_value(parameter["name"], schema, data)
    return params


def _resolve_schema(document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    if "$ref" in schema:
        return resolve_ref(document, schema["$ref"])
    return schema


def _sample_json(schema_document: dict[str, Any], schema: dict[str, Any] | None, data: Any) -> Any:
    if not schema:
        return {}
    schema = _resolve_schema(schema_document, schema)
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "allOf" in schema:
        merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
        for item in schema["allOf"]:
            resolved = _resolve_schema(schema_document, item)
            merged["properties"].update(resolved.get("properties", {}))
            merged["required"].extend(resolved.get("required", []))
        schema = merged
    if "anyOf" in schema:
        return _sample_json(schema_document, schema["anyOf"][0], data)
    if "oneOf" in schema:
        return _sample_json(schema_document, schema["oneOf"][0], data)

    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        result: dict[str, Any] = {}
        for name in schema.get("required", []):
            property_schema = schema.get("properties", {}).get(name, {"type": "string"})
            result[name] = _sample_json(schema_document, property_schema, data)
        return result
    if schema_type == "array":
        if schema.get("maxItems") == 0:
            return []
        return [_sample_json(schema_document, schema.get("items", {"type": "string"}), data)]

    return _sample_value(schema.get("title", "value"), schema, data)


def _request_json(schema_document: dict[str, Any], operation: dict[str, Any], data: Any) -> Any:
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    json_schema = content.get("application/json", {}).get("schema")
    return _sample_json(schema_document, json_schema, data) if json_schema else None


def _known_request_json(service: str, method: str, schema_path: str, data: Any) -> Any:
    if service == "crm" and method == "PATCH" and schema_path == "/api/v1/crm-external-integrations/customers":
        return crm_customer_update_payload(int(_data_value(data, "customer_id") or 0))

    factory = KNOWN_JSON_BODY_FACTORIES.get((service, method, schema_path))
    return factory() if factory else None


@pytest.mark.full_api
@pytest.mark.parametrize(("service", "method", "schema_path"), iter_openapi_operations())
def test_openapi_operation_is_callable(request, service: str, method: str, schema_path: str) -> None:
    if os.getenv("DREAMCRM_RUN_FULL_OPENAPI_TESTS") != "1":
        pytest.skip("Set DREAMCRM_RUN_FULL_OPENAPI_TESTS=1 to call every OpenAPI operation")
    if method in MUTATING_METHODS and os.getenv("DREAMCRM_RUN_MUTATING_OPENAPI_TESTS") != "1":
        pytest.skip("Set DREAMCRM_RUN_MUTATING_OPENAPI_TESTS=1 to call mutating operations")

    client_fixture, schema_fixture, data_fixture = SERVICE_FIXTURES[service]
    client = request.getfixturevalue(client_fixture)
    schema_document = request.getfixturevalue(schema_fixture)
    data = request.getfixturevalue(data_fixture)

    if not client.settings.base_url:
        pytest.skip(f"Set base URL for {service} to call generated OpenAPI requests")

    operation = schema_document["paths"][schema_path][method.lower()]
    actual_path = _replace_path_params(schema_path, operation, data)
    params = _collect_params(operation, data)
    json_body = None
    if method in MUTATING_METHODS:
        json_body = _known_request_json(service, method, schema_path, data)
        if json_body is None:
            json_body = _request_json(schema_document, operation, data)

    response = client.request(method, actual_path, params=params or None, json=json_body, timeout=15)
    declared_statuses = {
        int(code) for code in operation.get("responses", {}) if str(code).isdigit()
    }

    assert response.status_code < 500, response.text
    assert (
        not declared_statuses
        or response.status_code in declared_statuses
        or response.status_code in BUSINESS_STATUSES
    ), response.text
