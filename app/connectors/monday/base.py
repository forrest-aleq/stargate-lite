"""
Base class for Monday.com connector with authentication and GraphQL helpers.
"""

import os
from typing import Any, cast

from app.database import CredentialManager
from app.errors import CredentialMissingError, ExecutionError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class MondayBase:
    """
    Monday.com GraphQL API connector base class.

    Monday.com is used by finance/operations teams for:
    - Invoice approval workflows
    - Month-end close tracking
    - Budget review boards
    - Cross-functional project coordination
    """

    GRAPHQL_ENDPOINT = "https://api.monday.com/v2"
    API_VERSION = "2025-07"  # Latest API version

    def __init__(self) -> None:
        self.client_id = os.getenv("MONDAY_CLIENT_ID")
        self.client_secret = os.getenv("MONDAY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("MONDAY_REDIRECT_URI")

    def _get_access_token(self, org_id: str, user_id: str) -> str:
        """
        Retrieve Monday.com access token for user

        Note: Monday.com tokens do not expire
        """
        cred = CredentialManager.get_credential(org_id, user_id, "monday")
        if not cred:
            raise CredentialMissingError("monday", org_id, user_id)
        return str(cred["access_token"])

    def _execute_graphql(
        self, org_id: str, user_id: str, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute GraphQL query or mutation

        Args:
            org_id: Organization ID
            user_id: User ID
            query: GraphQL query or mutation string
            variables: Optional variables for the query

        Returns:
            GraphQL response data
        """
        access_token = self._get_access_token(org_id, user_id)

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json",
            "API-Version": self.API_VERSION,
        }

        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        result = http_client.post(
            url=self.GRAPHQL_ENDPOINT, service="monday", headers=headers, json=payload
        )

        # Check for GraphQL errors (application-level errors, not HTTP)
        if "errors" in result:
            errors = result["errors"]
            error_messages = [e.get("message", str(e)) for e in errors]
            raise ExecutionError(
                f"Monday.com GraphQL errors: {', '.join(error_messages)}",
                {"service": "monday", "graphql_errors": errors},
            )

        return cast(dict[str, Any], result.get("data", {}))
