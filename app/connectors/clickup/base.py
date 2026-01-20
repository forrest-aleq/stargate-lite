"""
Base class for ClickUp connector with authentication and request helpers.
"""

import os
from typing import Any

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class ClickUpBase:
    """
    ClickUp API connector base class.

    ClickUp is used by finance teams for:
    - Invoice approval workflows
    - Month-end close checklists
    - Budget review processes
    - Cross-functional project tracking
    """

    BASE_URL = "https://api.clickup.com/api/v2"
    AUTH_URL = "https://app.clickup.com/api"
    TOKEN_URL = "https://api.clickup.com/api/v2/oauth/token"

    def __init__(self) -> None:
        self.client_id = os.getenv("CLICKUP_CLIENT_ID")
        self.client_secret = os.getenv("CLICKUP_CLIENT_SECRET")
        self.redirect_uri = os.getenv("CLICKUP_REDIRECT_URI")

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """
        Retrieve ClickUp access token for user

        Note: Current ClickUp tokens do not expire (subject to change)
        """
        cred = CredentialManager.get_credential(org_id, user_id, "clickup")
        if not cred:
            raise CredentialMissingError("clickup", org_id, user_id)
        return cred

    def _make_request(
        self,
        org_id: str,
        user_id: str,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make authenticated request to ClickUp API

        Args:
            org_id: Organization ID
            user_id: User ID
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body for POST/PUT
            params: Query parameters

        Returns:
            API response as dictionary
        """
        cred = self._get_access_token(org_id, user_id)
        access_token = cred["access_token"]

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        # ClickUp OAuth tokens require Bearer prefix; personal API tokens (pk_*) do not
        auth_value = access_token if access_token.startswith("pk_") else f"Bearer {access_token}"
        headers = {"Authorization": auth_value, "Content-Type": "application/json"}

        result: dict[str, Any] = http_client.request(
            method=method, url=url, service="clickup", headers=headers, json=data, params=params
        )
        return result
