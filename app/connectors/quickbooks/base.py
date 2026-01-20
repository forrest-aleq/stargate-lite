"""
QuickBooks Online connector - Base module with authentication
"""

import os
from datetime import datetime, timedelta
from typing import Any, cast

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class QuickBooksBase:
    """QuickBooks Online API base connector with authentication"""

    SANDBOX_BASE_URL = "https://sandbox-quickbooks.api.intuit.com/v3/company"
    PRODUCTION_BASE_URL = "https://quickbooks.api.intuit.com/v3/company"
    TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    def __init__(self) -> None:
        self.client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
        self.client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")
        self.environment = os.getenv("QUICKBOOKS_ENVIRONMENT", "sandbox")
        if self.environment == "sandbox":
            self.base_url = self.SANDBOX_BASE_URL
        else:
            self.base_url = self.PRODUCTION_BASE_URL

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token, refreshing if necessary"""
        cred = CredentialManager.get_credential(org_id, user_id, "quickbooks")

        if not cred:
            raise CredentialMissingError("quickbooks", org_id, user_id)

        # Check if token is expired or about to expire
        if cred["token_expiry"] and cred["token_expiry"] < datetime.utcnow() + timedelta(minutes=5):
            logger.info(
                "Token expired or expiring soon, refreshing",
                service="quickbooks",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_needed",
            )
            return self._refresh_token(org_id, user_id, cred["refresh_token"])

        return cred

    def _refresh_token(self, org_id: str, user_id: str, refresh_token: str) -> dict[str, Any]:
        """Refresh the access token"""
        logger.info(
            "Refreshing QuickBooks token",
            service="quickbooks",
            org_id=org_id,
            user_id=user_id,
            log_event="token_refresh_start",
        )

        try:
            token_data = http_client.post(
                url=self.TOKEN_URL,
                service="quickbooks",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            )

            new_expiry = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            cred = CredentialManager.get_credential(org_id, user_id, "quickbooks")
            realm_id = cred["realm_id"] if cred else None

            CredentialManager.store_credential(
                org_id=org_id,
                user_id=user_id,
                service="quickbooks",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expiry=new_expiry,
                realm_id=realm_id,
            )

            logger.info(
                "QuickBooks token refreshed successfully",
                service="quickbooks",
                org_id=org_id,
                user_id=user_id,
                expires_in_seconds=token_data["expires_in"],
                log_event="token_refresh_success",
            )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expiry": new_expiry,
                "realm_id": realm_id,
            }
        except Exception as e:
            logger.error(
                "QuickBooks token refresh failed",
                service="quickbooks",
                org_id=org_id,
                user_id=user_id,
                error_type=type(e).__name__,
                log_event="token_refresh_error",
                exc_info=True,
            )
            raise

    def _make_api_call(
        self,
        method: str,
        endpoint: str,
        cred: dict[str, Any],
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API call to QuickBooks"""
        realm_id = cred["realm_id"]
        url = f"{self.base_url}/{realm_id}/{endpoint}"

        headers = {
            "Authorization": f"Bearer {cred['access_token']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if method == "GET":
            return http_client.get(url=url, service="quickbooks", headers=headers, params=params)
        elif method == "POST":
            return http_client.post(url=url, service="quickbooks", headers=headers, json=data)
        else:
            return cast(
                dict[str, Any],
                http_client.request(
                    method=method, url=url, service="quickbooks", headers=headers, json=data
                ),
            )
