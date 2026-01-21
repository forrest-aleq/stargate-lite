"""
Square connector - Base module with authentication
"""

import os
from datetime import datetime, timedelta
from typing import Any

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger
from app.posthog_client import track_token_refreshed

logger = get_logger(__name__)


class SquareBase:
    """Square API base connector with authentication"""

    BASE_URL = "https://connect.squareup.com/v2"
    SANDBOX_URL = "https://connect.squareupsandbox.com/v2"
    AUTH_URL = "https://connect.squareup.com/oauth2/token"
    API_VERSION = "2025-10-16"

    def __init__(self) -> None:
        self.client_id = os.getenv("SQUARE_CLIENT_ID")
        self.client_secret = os.getenv("SQUARE_CLIENT_SECRET")
        self.environment = os.getenv("SQUARE_ENVIRONMENT", "sandbox")
        self.base_url = self.SANDBOX_URL if self.environment == "sandbox" else self.BASE_URL

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Square-Version": self.API_VERSION,
        }

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token, refreshing if necessary"""
        cred = CredentialManager.get_credential(org_id, user_id, "square")

        if not cred:
            raise CredentialMissingError("square", org_id, user_id)

        if cred["token_expiry"] and cred["token_expiry"] < datetime.utcnow() + timedelta(minutes=5):
            logger.info("Token expired, refreshing", service="square", org_id=org_id)
            return self._refresh_token(org_id, user_id, cred["refresh_token"])

        return cred

    def _refresh_token(self, org_id: str, user_id: str, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token"""
        try:
            token_data = http_client.post(
                url=self.AUTH_URL,
                service="square",
                headers={"Content-Type": "application/json"},
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )

            new_expiry = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 2592000))

            CredentialManager.store_credential(
                org_id=org_id,
                user_id=user_id,
                service="square",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expiry=new_expiry,
            )

            # Track successful token refresh to PostHog
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="square",
                success=True,
            )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expiry": new_expiry,
            }
        except Exception:
            # Track failed token refresh to PostHog
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="square",
                success=False,
            )
            raise
