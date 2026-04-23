from __future__ import annotations

from typing import Any


def prune_payload(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            pruned = prune_payload(item)
            if pruned in (None, "", [], {}):
                continue
            result[key] = pruned
        return result

    if isinstance(value, list):
        result = []
        for item in value:
            pruned = prune_payload(item)
            if pruned in (None, "", [], {}):
                continue
            result.append(pruned)
        return result

    return value

