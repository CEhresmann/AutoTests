from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import pytest

from configs.settings import (
    ACCOUNTING_ORDER_ITEM_ID,
    ACCOUNTING_PROMOCODE_POOL_ID,
    ACCOUNTING_PROMOTION_ID,
    CRM_CAMPAIGN_ID,
    TEST_DATA,
)
from utils.openapi import load_schema_registry, resolve_ref
from utils.test_data import (
    accounting_bulk_product_payload,
    accounting_bonus_accrue_payload,
    accounting_bonus_activate_payload,
    accounting_bonus_hold_payload,
    accounting_bonus_hold_release_payload,
    accounting_bonus_pending_accrue_payload,
    accounting_calculate_payload,
    accounting_order_payload,
    accounting_order_update_payload,
    accounting_order_item_update_payload,
    accounting_promotion_apply_payload,
    accounting_promotion_apply_to_item_payload,
    accounting_promotion_available_payload,
    accounting_promotion_remove_payload,
    accounting_promotion_preview_payload,
    accounting_promocode_assign_payload,
    accounting_product_payload,
    accounting_gift_certificate_activate_payload,
    accounting_gift_certificate_credit_payload,
    accounting_gift_certificate_debit_payload,
    accounting_gift_certificate_refund_payload,
    accounting_gift_certificate_validate_payload,
    crm_campaign_automatic_send_payload,
    crm_customer_action_bulk_payload,
    crm_customer_action_payload,
    crm_customer_payload,
    crm_customer_search_payload,
    crm_customer_update_payload,
    crm_device_assign_payload,
    crm_device_payload,
)


SERVICE_FIXTURES = {
    "crm": ("crm_client", "crm_openapi", "test_data"),
    "accounting": ("accounting_client", "accounting_openapi", "test_data"),
    "app-content": ("app_content_client", "app_content_openapi", "app_content_test_data"),
    "mobile": ("mobile_client", "mobile_openapi", "mobile_test_data"),
}

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
BUSINESS_STATUSES = {400, 401, 403, 404, 405, 409, 422, 429}
_RESOURCE_CACHE: dict[str, Any] = {}
KNOWN_JSON_BODY_FACTORIES = {
    ("crm", "POST", "/api/v1/crm-external-integrations/customers"): crm_customer_payload,
    ("crm", "POST", "/api/v1/crm-external-integrations/customers/search"): crm_customer_search_payload,
    ("crm", "POST", "/api/v1/crm-external-integrations/customer-actions"): crm_customer_action_payload,
    ("crm", "POST", "/api/v1/crm-external-integrations/customer-actions/bulk"): crm_customer_action_bulk_payload,
    ("crm", "POST", "/api/v1/crm-external-integrations/campaigns/automatic/send"): lambda: crm_campaign_automatic_send_payload(
        CRM_CAMPAIGN_ID or 1
    ),
    ("crm", "POST", "/api/v1/crm-external-integrations/devices"): lambda: crm_device_payload(_ensure_crm_device_id()),
    ("crm", "POST", "/api/v1/crm-external-integrations/devices/assign"): lambda: crm_device_assign_payload(
        _ensure_crm_device_id()
    ),
    ("accounting", "POST", "/api/v1/accounting-external-api/product"): accounting_product_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/product/bulk"): accounting_bulk_product_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/orders"): accounting_order_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/orders/calculate"): accounting_calculate_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/bonuses/accrue-customer-points"): accounting_bonus_accrue_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/promotions/apply"): lambda: accounting_promotion_apply_payload(
        TEST_DATA.promotion_order_id or 1
    ),
    ("accounting", "POST", "/api/v1/accounting-external-api/promotions/preview"): lambda: accounting_promotion_preview_payload(
        TEST_DATA.promotion_order_id or 1
    ),
    ("accounting", "POST", "/api/v1/accounting-external-api/promotions/apply-to-item"): lambda: accounting_promotion_apply_to_item_payload(
        TEST_DATA.promotion_order_id or 1,
        1,
        1,
    ),
    ("accounting", "POST", "/api/v1/accounting-external-api/promotions/remove"): lambda: accounting_promotion_remove_payload(
        TEST_DATA.promotion_order_id or 1,
        1,
    ),
    ("accounting", "POST", "/api/v1/accounting-external-api/promotions/available"): lambda: accounting_promotion_available_payload(
        TEST_DATA.promotion_order_id or 1
    ),
    ("accounting", "POST", "/api/v1/accounting-external-api/promocodes/assign"): lambda: accounting_promocode_assign_payload(
        ACCOUNTING_PROMOCODE_POOL_ID or 1
    ),
    ("accounting", "POST", "/api/v1/accounting-external-api/gift-certificates/debit"): accounting_gift_certificate_debit_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/gift-certificates/credit"): accounting_gift_certificate_credit_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/gift-certificates/refund"): accounting_gift_certificate_refund_payload,
    ("accounting", "POST", "/api/v1/accounting-external-api/gift-certificates/validate"): accounting_gift_certificate_validate_payload,
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


def _ensure_crm_device_id() -> str:
    device_id = _RESOURCE_CACHE.get("crm_device_id")
    if not device_id:
        device_id = f"autotest-device-{uuid4().hex[:10]}"
        _RESOURCE_CACHE["crm_device_id"] = device_id
    return device_id


def _ensure_crm_device_created(client) -> str:
    device_id = _ensure_crm_device_id()
    if _RESOURCE_CACHE.get("crm_device_created"):
        return device_id
    response = client.post(
        "/api/v1/crm-external-integrations/devices",
        json=crm_device_payload(device_id),
        timeout=15,
    )
    assert response.status_code in {200, 201}, response.text
    _RESOURCE_CACHE["crm_device_created"] = True
    return device_id


def _ensure_accounting_order_payload() -> dict[str, Any]:
    payload = _RESOURCE_CACHE.get("accounting_order_payload")
    if not payload:
        payload = accounting_order_payload()
        _RESOURCE_CACHE["accounting_order_payload"] = payload
    return payload


def _ensure_accounting_bonus_id(client) -> str:
    bonus_id = _RESOURCE_CACHE.get("accounting_bonus_id")
    if bonus_id:
        return bonus_id
    response = client.post(
        "/api/v1/accounting-external-api/bonuses/accrue-customer-points",
        json=accounting_bonus_pending_accrue_payload(),
        timeout=15,
    )
    assert response.status_code in {200, 201}, response.text
    bonus_id = response.json()["id"]
    _RESOURCE_CACHE["accounting_bonus_id"] = bonus_id
    return bonus_id


def _ensure_accounting_hold_id(client) -> str:
    hold_id = _RESOURCE_CACHE.get("accounting_hold_id")
    if hold_id:
        return hold_id
    order_context = _ensure_accounting_order_context(client)
    response = client.post(
        "/api/v1/accounting-external-api/bonuses/hold",
        json=accounting_bonus_hold_payload(order_context["external_order_id"]),
        timeout=15,
    )
    assert response.status_code in {200, 201}, response.text
    hold_id = response.json()["hold_id"]
    _RESOURCE_CACHE["accounting_hold_id"] = hold_id
    return hold_id


def _ensure_accounting_order_context(client) -> dict[str, str]:
    context = _RESOURCE_CACHE.get("accounting_order_context")
    if context:
        return context
    payload = _ensure_accounting_order_payload()
    response = client.post("/api/v1/accounting-external-api/orders", json=payload, timeout=15)
    assert response.status_code in {200, 201}, response.text
    context = {
        "external_order_id": payload["external_order_id"],
        "external_line_id": payload.get("items", [{}])[0].get("external_line_id", "line-1"),
    }
    _RESOURCE_CACHE["accounting_order_context"] = context
    return context


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


def _replace_path_params(
    path: str,
    operation: dict[str, Any],
    data: Any,
    *,
    overrides: dict[str, Any] | None = None,
) -> str:
    parameters = {param["name"]: param for param in operation.get("parameters", []) if param.get("in") == "path"}
    overrides = overrides or {}

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in overrides:
            return quote(str(overrides[name]), safe="")
        parameter = parameters.get(name, {})
        value = _sample_value(name, parameter.get("schema"), data)
        return quote(str(value), safe="")

    return re.sub(r"\{([^}]+)\}", replace, path)


def _collect_params(
    operation: dict[str, Any],
    data: Any,
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    overrides = overrides or {}
    for parameter in operation.get("parameters", []):
        location = parameter.get("in")
        if location in {"path", "header"}:
            continue
        schema = parameter.get("schema", {})
        if parameter["name"] in overrides:
            params[parameter["name"]] = overrides[parameter["name"]]
            continue
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

    path_overrides: dict[str, Any] = {}
    param_overrides: dict[str, Any] = {}
    json_body: Any | None = None

    if service == "crm":
        if schema_path == "/api/v1/crm-external-integrations/campaigns/automatic/send":
            if CRM_CAMPAIGN_ID is None:
                pytest.skip("Set DREAMCRM_CRM_CAMPAIGN_ID to call campaign send")
            json_body = crm_campaign_automatic_send_payload(CRM_CAMPAIGN_ID)
        elif schema_path == "/api/v1/crm-external-integrations/devices":
            device_id = _ensure_crm_device_id()
            json_body = crm_device_payload(device_id)
        elif schema_path == "/api/v1/crm-external-integrations/devices/assign":
            device_id = _ensure_crm_device_created(client)
            param_overrides["device_id"] = device_id
            if method == "POST":
                json_body = crm_device_assign_payload(device_id)

    if service == "accounting":
        if schema_path in {
            "/api/v1/accounting-external-api/orders/{external_order_id}",
            "/api/v1/accounting-external-api/orders/{external_order_id}/items/{external_line_id}",
            "/api/v1/accounting-external-api/bonuses/hold",
            "/api/v1/accounting-external-api/bonuses/hold/{hold_id}",
            "/api/v1/accounting-external-api/gift-certificates/activate",
        }:
            order_context = _ensure_accounting_order_context(client)
            path_overrides["external_order_id"] = order_context["external_order_id"]
            if schema_path == "/api/v1/accounting-external-api/orders/{external_order_id}/items/{external_line_id}":
                path_overrides["external_line_id"] = order_context["external_line_id"]
        if schema_path == "/api/v1/accounting-external-api/orders/{external_order_id}":
            if method == "PATCH":
                if not TEST_DATA.contact_point_id:
                    pytest.skip("Set DREAMCRM_CONTACT_POINT_ID to call order patch")
                json_body = accounting_order_update_payload(TEST_DATA.contact_point_id)
        elif schema_path == "/api/v1/accounting-external-api/orders/{external_order_id}/items/{external_line_id}":
            if method == "PATCH":
                json_body = accounting_order_item_update_payload()
        elif schema_path == "/api/v1/accounting-external-api/bonuses/accrue-customer-points":
            json_body = accounting_bonus_accrue_payload()
        elif schema_path == "/api/v1/accounting-external-api/bonuses/activate-customer-points":
            json_body = accounting_bonus_activate_payload(_ensure_accounting_bonus_id(client))
        elif schema_path == "/api/v1/accounting-external-api/bonuses/hold":
            json_body = accounting_bonus_hold_payload(_ensure_accounting_order_context(client)["external_order_id"])
        elif schema_path == "/api/v1/accounting-external-api/bonuses/hold/{hold_id}":
            if method == "PATCH":
                path_overrides["hold_id"] = _ensure_accounting_hold_id(client)
                json_body = accounting_bonus_hold_release_payload()
        elif schema_path == "/api/v1/accounting-external-api/promotions/apply":
            if TEST_DATA.promotion_order_id is None:
                pytest.skip("Set DREAMCRM_PROMOTION_ORDER_ID to call promotion apply")
            json_body = accounting_promotion_apply_payload(TEST_DATA.promotion_order_id)
        elif schema_path == "/api/v1/accounting-external-api/promotions/preview":
            if TEST_DATA.promotion_order_id is None:
                pytest.skip("Set DREAMCRM_PROMOTION_ORDER_ID to call promotions preview")
            json_body = accounting_promotion_preview_payload(TEST_DATA.promotion_order_id)
        elif schema_path == "/api/v1/accounting-external-api/promotions/apply-to-item":
            if TEST_DATA.promotion_order_id is None or ACCOUNTING_ORDER_ITEM_ID is None or ACCOUNTING_PROMOTION_ID is None:
                pytest.skip(
                    "Set DREAMCRM_PROMOTION_ORDER_ID, DREAMCRM_ACCOUNTING_ORDER_ITEM_ID and DREAMCRM_ACCOUNTING_PROMOTION_ID to call promotion apply-to-item"
                )
            json_body = accounting_promotion_apply_to_item_payload(
                TEST_DATA.promotion_order_id,
                ACCOUNTING_ORDER_ITEM_ID,
                ACCOUNTING_PROMOTION_ID,
            )
        elif schema_path == "/api/v1/accounting-external-api/promotions/remove":
            if TEST_DATA.promotion_order_id is None or ACCOUNTING_PROMOTION_ID is None:
                pytest.skip("Set DREAMCRM_PROMOTION_ORDER_ID to call promotion remove")
            json_body = accounting_promotion_remove_payload(TEST_DATA.promotion_order_id, ACCOUNTING_PROMOTION_ID)
        elif schema_path == "/api/v1/accounting-external-api/promotions/available":
            if TEST_DATA.promotion_order_id is None:
                pytest.skip("Set DREAMCRM_PROMOTION_ORDER_ID to call promotions available")
            json_body = accounting_promotion_available_payload(TEST_DATA.promotion_order_id)
        elif schema_path == "/api/v1/accounting-external-api/promocodes/assign":
            if ACCOUNTING_PROMOCODE_POOL_ID is None:
                pytest.skip("Set DREAMCRM_ACCOUNTING_PROMOCODE_POOL_ID to call promocodes assign")
            json_body = accounting_promocode_assign_payload(ACCOUNTING_PROMOCODE_POOL_ID)
        elif schema_path == "/api/v1/accounting-external-api/gift-certificates/activate":
            json_body = accounting_gift_certificate_activate_payload(
                _ensure_accounting_order_context(client)["external_order_id"]
            )
        elif schema_path == "/api/v1/accounting-external-api/gift-certificates/debit":
            json_body = accounting_gift_certificate_debit_payload()
        elif schema_path == "/api/v1/accounting-external-api/gift-certificates/credit":
            json_body = accounting_gift_certificate_credit_payload()
        elif schema_path == "/api/v1/accounting-external-api/gift-certificates/refund":
            json_body = accounting_gift_certificate_refund_payload()
        elif schema_path == "/api/v1/accounting-external-api/gift-certificates/validate":
            json_body = accounting_gift_certificate_validate_payload()

    operation = schema_document["paths"][schema_path][method.lower()]
    actual_path = _replace_path_params(schema_path, operation, data, overrides=path_overrides)
    params = _collect_params(operation, data, overrides=param_overrides)
    if method in MUTATING_METHODS:
        if json_body is None:
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
