from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from configs.settings import OPENAPI_DIR


CRM_SCHEMA_FILE = OPENAPI_DIR / "CRM-EXTERNAL-INTEGRATIONS-openapi.json"
ACCOUNTING_SCHEMA_FILE = OPENAPI_DIR / "ACCOUNTING-EXTERNAL-INTEGRATIONS-openapi.json"
APP_CONTENT_SCHEMA_FILE = OPENAPI_DIR / "dreamisland-back-all-app-content.json"
MOBILE_SCHEMA_FILE = OPENAPI_DIR / "dreamisland-back-mobile.json"

SCHEMA_FILES = {
    "crm": CRM_SCHEMA_FILE,
    "accounting": ACCOUNTING_SCHEMA_FILE,
    "app-content": APP_CONTENT_SCHEMA_FILE,
    "mobile": MOBILE_SCHEMA_FILE,
}


@lru_cache(maxsize=8)
def load_openapi_schema(path: str | Path) -> dict[str, Any]:
    schema_path = Path(path)
    return json.loads(schema_path.read_text(encoding="utf-8"))


def resolve_ref(document: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Unsupported ref: {ref}")

    node: Any = document
    for part in ref.removeprefix("#/").split("/"):
        node = node[part]
    return node


def operation_schema(document: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    return document["paths"][path][method.lower()]


def response_schema(
    document: dict[str, Any],
    path: str,
    method: str,
    status_code: int | str,
    content_type: str = "application/json",
) -> dict[str, Any] | None:
    operation = operation_schema(document, path, method)
    response = operation["responses"].get(str(status_code))
    if not response:
        return None
    return response.get("content", {}).get(content_type, {}).get("schema")


def request_body_schema(
    document: dict[str, Any],
    path: str,
    method: str,
    content_type: str = "application/json",
) -> dict[str, Any] | None:
    operation = operation_schema(document, path, method)
    return (
        operation.get("requestBody", {})
        .get("content", {})
        .get(content_type, {})
        .get("schema")
    )


def load_schema_registry(names: list[str] | None = None) -> dict[str, dict[str, Any]]:
    selected_names = names or list(SCHEMA_FILES)
    return {name: load_openapi_schema(SCHEMA_FILES[name]) for name in selected_names}


@lru_cache(maxsize=128)
def _compiled_path_patterns(schema_path: str) -> re.Pattern[str]:
    pattern = re.sub(r"\{[^/]+\}", r"[^/]+", schema_path)
    return re.compile(f"^{pattern}$")


def match_openapi_path(document: dict[str, Any], actual_path: str) -> str | None:
    if actual_path in document["paths"]:
        return actual_path

    candidates: list[str] = []
    for schema_path in document["paths"]:
        if _compiled_path_patterns(schema_path).match(actual_path):
            candidates.append(schema_path)
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (-item.count("{"), -len(item)))[0]
