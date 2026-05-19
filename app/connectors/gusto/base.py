"""
Gusto connector - Base module with authentication
"""

import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from app.database import CredentialManager
from app.errors import CredentialMissingError, NetworkError
from app.http_client import http_client
from app.logging_config import get_logger
from app.posthog_client import track_token_refreshed

logger = get_logger(__name__)


class GustoBase:
    """Gusto API base connector with authentication"""

    BASE_URL = "https://api.gusto.com"
    SANDBOX_URL = "https://api.gusto-demo.com"
    AUTH_URL = "https://api.gusto.com/oauth/token"
    API_VERSION = "2025-06-15"

    def __init__(self) -> None:
        self.client_id = os.getenv("GUSTO_CLIENT_ID")
        self.client_secret = os.getenv("GUSTO_CLIENT_SECRET")
        self.environment = os.getenv("GUSTO_ENVIRONMENT", "sandbox")
        self.base_url = self.SANDBOX_URL if self.environment == "sandbox" else self.BASE_URL

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Gusto-API-Version": self.API_VERSION,
        }

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token, refreshing if necessary"""
        cred = CredentialManager.get_credential(org_id, user_id, "gusto")

        if not cred:
            raise CredentialMissingError("gusto", org_id, user_id)

        if cred["token_expiry"] and cred["token_expiry"] < datetime.now(UTC) + timedelta(minutes=5):
            logger.info("Token expired, refreshing", service="gusto", org_id=org_id)
            return self._refresh_token(org_id, user_id, cred["refresh_token"])

        return cred

    def _refresh_token(self, org_id: str, user_id: str, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token"""
        for attempt in range(2):
            try:
                token_data = http_client.post(
                    url=self.AUTH_URL,
                    service="gusto",
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
                    service="gusto",
                    access_token=token_data["access_token"],
                    refresh_token=token_data["refresh_token"],
                    token_expiry=new_expiry,
                )

                # Track successful token refresh to PostHog
                track_token_refreshed(
                    user_id=user_id,
                    org_id=org_id,
                    service="gusto",
                    success=True,
                )

                return {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data["refresh_token"],
                    "token_expiry": new_expiry,
                }
            except NetworkError:
                if attempt == 0:
                    logger.warning(
                        "Token refresh transient failure, retrying",
                        service="gusto",
                        log_event="token_refresh_retry",
                    )
                    time.sleep(1.0)
                    continue
                track_token_refreshed(
                    user_id=user_id, org_id=org_id, service="gusto", success=False
                )
                raise
            except Exception:
                track_token_refreshed(
                    user_id=user_id, org_id=org_id, service="gusto", success=False
                )
                raise
        raise NetworkError(service="gusto")
