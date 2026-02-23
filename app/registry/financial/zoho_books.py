"""
Zoho Books Capability Registry.

Builds one capability per operation from the generated OpenAPI manifest.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.connectors.zoho_books import get_operations, zoho_books_connector


def _make_operation_handler(
    operation: dict[str, Any],
) -> Callable[[str, str, dict[str, Any]], dict[str, Any]]:
    """Create a registry handler for a specific Zoho Books operation."""

    def handler(org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        return zoho_books_connector.execute_operation(org_id, user_id, operation, args)

    operation_id = str(operation.get("operation_id", "operation"))
    handler.__name__ = f"zoho_books_{operation_id}"
    return handler


ZOHO_BOOKS_CAPABILITIES: dict[str, dict[str, Any]] = {}

for operation in get_operations():
    capability_key = str(operation["capability_key"])
    method = str(operation.get("method", "GET"))
    path = str(operation.get("path", "/"))
    summary = str(operation.get("summary") or f"{method} {path}")

    ZOHO_BOOKS_CAPABILITIES[capability_key] = {
        "handler": _make_operation_handler(operation),
        "tool_name": str(operation.get("tool_name", capability_key)),
        "description": f"{summary} ({method} {path})",
        "requires_oauth": True,
        "service": "zoho_books",
        "credential_type": "customer",
        "supports_delegation": False,
    }
