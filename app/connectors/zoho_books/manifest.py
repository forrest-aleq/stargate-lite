"""
Zoho Books operation manifest loader.

The manifest is generated from Zoho's official OpenAPI bundle and contains one
entry per API operation (method + path + parameter metadata).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

MANIFEST_FILENAME = "operations_manifest.json"


def _manifest_path() -> Path:
    return Path(__file__).with_name(MANIFEST_FILENAME)


@lru_cache(maxsize=1)
def _load_manifest_payload() -> dict[str, Any]:
    with _manifest_path().open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        return {}
    return payload


@lru_cache(maxsize=1)
def get_operations() -> tuple[dict[str, Any], ...]:
    """Return all Zoho Books operations from the generated manifest."""
    payload = _load_manifest_payload()
    operations = payload.get("operations", [])
    if not isinstance(operations, list):
        return ()
    return tuple(op for op in operations if isinstance(op, dict))


@lru_cache(maxsize=1)
def get_operation_map() -> dict[str, dict[str, Any]]:
    """Map capability_key -> operation manifest entry."""
    return {
        str(op["capability_key"]): op
        for op in get_operations()
        if isinstance(op.get("capability_key"), str)
    }


def get_operation_count() -> int:
    return len(get_operations())


def get_recommended_scopes() -> str:
    payload = _load_manifest_payload()
    scopes = payload.get("recommended_scopes", "")
    return scopes if isinstance(scopes, str) else ""
