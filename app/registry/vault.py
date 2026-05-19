"""
Vault Capability Registry
Bitwarden Secrets Manager — Aleq's password and credential vault
"""

import threading
from collections.abc import Callable
from typing import Any

_vault_lock = threading.Lock()
_bitwarden_vault: Any = None


def _lazy_bitwarden(method_name: str) -> Callable[[str, str, dict[str, Any]], dict[str, Any]]:
    """Create lazy handler for Bitwarden vault methods."""

    def handler(org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        global _bitwarden_vault
        if _bitwarden_vault is None:
            with _vault_lock:
                if _bitwarden_vault is None:
                    from app.connectors.bitwarden import BitwardenVault

                    _bitwarden_vault = BitwardenVault()
        result: dict[str, Any] = getattr(_bitwarden_vault, method_name)(org_id, user_id, args)
        return result

    return handler


VAULT_CAPABILITIES: dict[str, dict[str, Any]] = {
    "vault.store": {
        "handler": _lazy_bitwarden("store_secret"),
        "tool_name": "bitwarden.store_secret",
        "description": "Store a secret (password, API key, credential) in Aleq's vault",
        "requires_oauth": False,
        "service": "bitwarden",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "vault.retrieve": {
        "handler": _lazy_bitwarden("retrieve_secret"),
        "tool_name": "bitwarden.retrieve_secret",
        "description": "Retrieve a secret from the vault by ID",
        "requires_oauth": False,
        "service": "bitwarden",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "vault.lookup": {
        "handler": _lazy_bitwarden("lookup_by_key"),
        "tool_name": "bitwarden.lookup_by_key",
        "description": "Look up a secret by key name (e.g., 'slack_password')",
        "requires_oauth": False,
        "service": "bitwarden",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "vault.list": {
        "handler": _lazy_bitwarden("list_secrets"),
        "tool_name": "bitwarden.list_secrets",
        "description": "List all secrets in Aleq's vault (names only, not values)",
        "requires_oauth": False,
        "service": "bitwarden",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "vault.delete": {
        "handler": _lazy_bitwarden("delete_secret"),
        "tool_name": "bitwarden.delete_secret",
        "description": "Delete a secret from the vault",
        "requires_oauth": False,
        "service": "bitwarden",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "vault.generate_password": {
        "handler": _lazy_bitwarden("generate_password"),
        "tool_name": "bitwarden.generate_password",
        "description": "Generate a strong random password",
        "requires_oauth": False,
        "service": "bitwarden",
        "credential_type": "agent",
        "supports_delegation": False,
    },
}
