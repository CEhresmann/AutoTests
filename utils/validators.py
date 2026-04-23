from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator, RefResolver


def build_validator(schema_document: dict[str, Any], schema: dict[str, Any]) -> Draft202012Validator:
    resolver = RefResolver.from_schema(schema_document)
    return Draft202012Validator(schema, resolver=resolver)


def validate_instance(
    schema_document: dict[str, Any],
    schema: dict[str, Any],
    instance: Any,
) -> None:
    validator = build_validator(schema_document, schema)
    validator.validate(instance)


def assert_json_response(response) -> Any:
    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type, (
        f"Expected JSON response, got {content_type!r}. "
        f"Body: {response.text[:500]}"
    )
    return response.json()


def validate_response_against_openapi(
    *,
    schema_document: dict[str, Any],
    response,
    schema: dict[str, Any] | None,
) -> Any:
    payload = assert_json_response(response)
    if schema:
        validate_instance(schema_document, schema, payload)
    return payload

