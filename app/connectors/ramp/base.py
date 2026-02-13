"""
Ramp connector base with OAuth authentication and token management.
Uses CredentialManager for proper token storage and refresh.
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger
from app.posthog_client import track_token_refreshed

logger = get_logger(__name__)


class RampBase:
    """Base class for Ramp API with OAuth authentication."""

    BASE_URL = "https://api.ramp.com/developer/v1"
    TOKEN_URL = "https://api.ramp.com/developer/v1/token"

    def __init__(self) -> None:
        self.client_id = os.getenv("RAMP_CLIENT_ID")
        self.client_secret = os.getenv("RAMP_CLIENT_SECRET")

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token from DB, refreshing if necessary."""
        cred = CredentialManager.get_credential(org_id, user_id, "ramp")

        if not cred:
            raise CredentialMissingError("ramp", org_id, user_id)

        # Ramp tokens expire after 1 hour — refresh if within 5 minutes
        if cred["token_expiry"] and cred["token_expiry"] < datetime.now(UTC) + timedelta(minutes=5):
            logger.info(
                "Token expired or expiring soon, refreshing",
                service="ramp",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_needed",
            )
            return self._refresh_token(org_id, user_id, cred["refresh_token"])

        return cred

    def _refresh_token(self, org_id: str, user_id: str, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token."""
        logger.info(
            "Refreshing Ramp token",
            service="ramp",
            org_id=org_id,
            user_id=user_id,
            log_event="token_refresh_start",
        )

        try:
            token_data = http_client.post(
                url=self.TOKEN_URL,
                service="ramp",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            )

            new_expiry = datetime.now(UTC) + timedelta(seconds=token_data["expires_in"])

            CredentialManager.store_credential(
                org_id=org_id,
                user_id=user_id,
                service="ramp",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expiry=new_expiry,
            )

            logger.info(
                "Ramp token refreshed successfully",
                service="ramp",
                org_id=org_id,
                user_id=user_id,
                expires_in_seconds=token_data["expires_in"],
                log_event="token_refresh_success",
            )

            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="ramp",
                success=True,
            )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expiry": new_expiry,
            }
        except Exception as e:
            logger.error(
                "Ramp token refresh failed",
                service="ramp",
                org_id=org_id,
                user_id=user_id,
                error_type=type(e).__name__,
                log_event="token_refresh_error",
                exc_info=True,
            )
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="ramp",
                success=False,
            )
            raise

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        org_id: str,
        user_id: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated request to Ramp API."""
        cred = self._get_access_token(org_id, user_id)
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers(cred["access_token"])

        if method == "GET":
            return http_client.get(url=url, service="ramp", headers=headers, params=params or data)

        result: dict[str, Any] = http_client.request(
            method=method, url=url, service="ramp", headers=headers, json=data
        )
        return result
