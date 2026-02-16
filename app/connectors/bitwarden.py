"""
Bitwarden Secrets Manager connector.

Aleq's credential vault — stores and retrieves passwords, API keys,
and service credentials for autonomous account management.

Uses Bitwarden Secrets Manager (machine account access tokens),
not the regular Bitwarden vault (which requires human auth).

Env vars:
    BWS_ACCESS_TOKEN: Machine account access token
    BWS_ORGANIZATION_ID: Bitwarden organization UUID
    BWS_PROJECT_ID: Project UUID for Aleq's secrets
"""

import os
from typing import Any

from app.logging_config import get_logger

logger = get_logger(__name__)


class BitwardenVault:
    """Bitwarden Secrets Manager client for Aleq's credential vault."""

    def __init__(self) -> None:
        self.access_token = os.getenv("BWS_ACCESS_TOKEN")
        self.organization_id = os.getenv("BWS_ORGANIZATION_ID")
        self.project_id = os.getenv("BWS_PROJECT_ID")
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-init the Bitwarden SDK client."""
        if self._client is not None:
            return self._client

        if not self.access_token:
            raise ValueError("BWS_ACCESS_TOKEN not set — cannot connect to Bitwarden vault")

        from bitwarden_sdk import BitwardenClient, DeviceType, client_settings_from_dict

        self._client = BitwardenClient(
            client_settings_from_dict(
                {
                    "apiUrl": "https://api.bitwarden.com",
                    "deviceType": DeviceType.SDK,
                    "identityUrl": "https://identity.bitwarden.com",
                    "userAgent": "Stargate-Lite/1.0",
                }
            )
        )
        self._client.auth().login_access_token(self.access_token)
        logger.info("Bitwarden vault connected", log_event="bitwarden_init_success")
        return self._client

    def store_secret(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Store a secret in the vault.

        Args:
            key: Name/identifier for the secret (e.g., "slack_password")
            value: The secret value to store
            note: Optional description
        """
        key: str = args.get("key", "")
        value: str = args.get("value", "")
        note: str = args.get("note", "")

        if not key or not value:
            return {"status": "error", "error": "key and value are required"}

        client = self._get_client()
        result = client.secrets().create(
            organization_id=self.organization_id,
            key=key,
            value=value,
            note=note,
            project_ids=[self.project_id] if self.project_id else None,
        )

        secret_id: str = str(result.data.id)
        logger.info(
            "Secret stored in vault",
            secret_key=key,
            secret_id=secret_id,
            log_event="vault_store_success",
        )
        return {"status": "success", "secret_id": secret_id, "key": key}

    def retrieve_secret(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Retrieve a secret by ID.

        Args:
            secret_id: UUID of the secret to retrieve
        """
        secret_id: str = args.get("secret_id", "")
        if not secret_id:
            return {"status": "error", "error": "secret_id is required"}

        client = self._get_client()
        result = client.secrets().get(secret_id)

        return {
            "status": "success",
            "key": result.data.key,
            "value": result.data.value,
            "note": result.data.note,
        }

    def list_secrets(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all secrets in the vault (names and IDs only, not values)."""
        client = self._get_client()
        result = client.secrets().list(self.organization_id)

        secrets = [
            {"id": str(s.id), "key": s.key}
            for s in (result.data.data if result.data and result.data.data else [])
        ]

        return {"status": "success", "secrets": secrets, "count": len(secrets)}

    def delete_secret(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a secret by ID.

        Args:
            secret_id: UUID of the secret to delete
        """
        secret_id: str = args.get("secret_id", "")
        if not secret_id:
            return {"status": "error", "error": "secret_id is required"}

        client = self._get_client()
        client.secrets().delete([secret_id])

        logger.info(
            "Secret deleted from vault",
            secret_id=secret_id,
            log_event="vault_delete_success",
        )
        return {"status": "success", "deleted": secret_id}

    def generate_password(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Generate a strong random password.

        Args:
            length: Password length (default: 32)
            special: Include special characters (default: True)
        """
        length: int = args.get("length", 32)
        special: bool = args.get("special", True)

        client = self._get_client()
        password: str = client.generators().generate(
            length=length,
            avoid_ambiguous=True,
            lowercase=True,
            uppercase=True,
            numbers=True,
            special=special,
        )

        return {"status": "success", "password": password, "length": len(password)}

    def lookup_by_key(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Look up a secret by key name (list + filter + get).

        Args:
            key: The key name to search for (exact match)
        """
        key: str = args.get("key", "")
        if not key:
            return {"status": "error", "error": "key is required"}

        client = self._get_client()
        listing = client.secrets().list(self.organization_id)

        for s in listing.data.data if listing.data and listing.data.data else []:
            if s.key == key:
                result = client.secrets().get(str(s.id))
                return {
                    "status": "success",
                    "key": result.data.key,
                    "value": result.data.value,
                    "note": result.data.note,
                    "secret_id": str(result.data.id),
                }

        return {"status": "not_found", "error": f"No secret with key '{key}'"}
