"""
HubSpot connector base with authentication and token management.
"""

import os
from datetime import datetime, timedelta
from typing import Any

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class HubSpotBase:
    """Base class for HubSpot API with authentication."""

    BASE_URL = "https://api.hubapi.com"
    TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"

    def __init__(self) -> None:
        self.client_id = os.getenv("HUBSPOT_CLIENT_ID")
        self.client_secret = os.getenv("HUBSPOT_CLIENT_SECRET")

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token, refreshing if necessary"""
        cred = CredentialManager.get_credential(org_id, user_id, "hubspot")

        if not cred:
            raise CredentialMissingError("hubspot", org_id, user_id)

        # HubSpot tokens expire after ~6 hours
        if cred["token_expiry"] and cred["token_expiry"] < datetime.utcnow() + timedelta(minutes=5):
            logger.info(
                "Token expired or expiring soon, refreshing",
                service="hubspot",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_needed",
            )
            return self._refresh_token(org_id, user_id, cred["refresh_token"])

        return cred

    def _refresh_token(self, org_id: str, user_id: str, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token"""
        logger.info(
            "Refreshing HubSpot token",
            service="hubspot",
            org_id=org_id,
            user_id=user_id,
            log_event="token_refresh_start",
        )

        try:
            token_data = http_client.post(
                url=self.TOKEN_URL,
                service="hubspot",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
            )

            new_expiry = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

            # Store the new tokens
            CredentialManager.store_credential(
                org_id=org_id,
                user_id=user_id,
                service="hubspot",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expiry=new_expiry,
            )

            logger.info(
                "HubSpot token refreshed successfully",
                service="hubspot",
                org_id=org_id,
                user_id=user_id,
                expires_in_seconds=token_data["expires_in"],
                log_event="token_refresh_success",
            )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expiry": new_expiry,
            }
        except Exception as e:
            logger.error(
                "HubSpot token refresh failed",
                service="hubspot",
                org_id=org_id,
                user_id=user_id,
                error_type=type(e).__name__,
                log_event="token_refresh_error",
                exc_info=True,
            )
            raise
