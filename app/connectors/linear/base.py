"""
Base class for Linear connector with authentication and GraphQL helpers.
"""

import os
from datetime import datetime, timedelta
from typing import Any, cast

from app.database import CredentialManager
from app.errors import CredentialMissingError, ExecutionError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class LinearBase:
    """
    Linear API connector base class with authentication.

    Linear agents can:
    - Be assigned issues (app:assignable scope)
    - Be @mentioned in comments (app:mentionable scope)
    - Create issues/comments with custom identity
    - Participate as first-class team members
    """

    GRAPHQL_ENDPOINT = "https://api.linear.app/graphql"

    def __init__(self) -> None:
        self.client_id = os.getenv("LINEAR_CLIENT_ID")
        self.client_secret = os.getenv("LINEAR_CLIENT_SECRET")
        self.agent_name = os.getenv("LINEAR_AGENT_NAME", "Aleq AI")
        self.agent_avatar_url = os.getenv("LINEAR_AGENT_AVATAR_URL", "")

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid Linear access token, refreshing if necessary"""
        cred = CredentialManager.get_credential(org_id, user_id, "linear")

        if not cred:
            raise CredentialMissingError("linear", org_id, user_id)

        # Check if token needs refresh (within 5 minutes of expiry)
        expiry_threshold = cred["token_expiry"] - timedelta(minutes=5)
        if cred["token_expiry"] and datetime.utcnow() >= expiry_threshold:
            if cred["refresh_token"]:
                logger.info(
                    "Token expired or expiring soon, refreshing",
                    service="linear",
                    org_id=org_id,
                    user_id=user_id,
                    log_event="token_refresh_needed",
                )
                try:
                    # Refresh the token
                    token_data = http_client.post(
                        url="https://api.linear.app/oauth/token",
                        service="linear",
                        data={
                            "grant_type": "refresh_token",
                            "refresh_token": cred["refresh_token"],
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                        },
                    )

                    # Calculate new credential values
                    new_refresh_token = token_data.get("refresh_token", cred["refresh_token"])
                    expires_in = token_data.get("expires_in")
                    if expires_in is None:
                        logger.warning(
                            "Token refresh response missing expires_in, using default 1 hour",
                            service="linear",
                            org_id=org_id,
                            user_id=user_id,
                        )
                        expires_in = 3600
                    new_token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

                    # Update stored credentials
                    CredentialManager.store_credential(
                        org_id=org_id,
                        user_id=user_id,
                        service="linear",
                        access_token=token_data["access_token"],
                        refresh_token=new_refresh_token,
                        token_expiry=new_token_expiry,
                    )

                    # Update ALL credential fields in-memory to prevent stale data
                    cred["access_token"] = token_data["access_token"]
                    cred["refresh_token"] = new_refresh_token
                    cred["token_expiry"] = new_token_expiry

                    logger.info(
                        "Linear token refreshed successfully",
                        service="linear",
                        org_id=org_id,
                        user_id=user_id,
                        expires_in_seconds=token_data["expires_in"],
                        log_event="token_refresh_success",
                    )
                except Exception as e:
                    logger.error(
                        "Linear token refresh failed",
                        service="linear",
                        org_id=org_id,
                        user_id=user_id,
                        error_type=type(e).__name__,
                        log_event="token_refresh_error",
                        exc_info=True,
                    )
                    raise

        return cred

    def _graphql_request(
        self, org_id: str, user_id: str, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute GraphQL request with authentication"""
        cred = self._get_access_token(org_id, user_id)

        headers = {
            "Authorization": f"Bearer {cred['access_token']}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        result = http_client.post(
            url=self.GRAPHQL_ENDPOINT,
            service="linear",
            headers=headers,
            json=payload,
            timeout=(5, 30),  # Custom read timeout for GraphQL queries
        )

        # Check for GraphQL errors (application-level errors, not HTTP)
        if "errors" in result:
            errors = result["errors"]
            error_messages = [e.get("message", str(e)) for e in errors]
            raise ExecutionError(
                f"Linear GraphQL errors: {', '.join(error_messages)}",
                {"service": "linear", "graphql_errors": errors},
            )

        return cast(dict[str, Any], result.get("data", {}))
