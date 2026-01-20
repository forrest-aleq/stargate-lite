"""
Shopify connector - Base module with authentication
"""

import os
from datetime import datetime, timedelta
from typing import Any

from app.database import CredentialManager
from app.errors import CredentialMissingError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class ShopifyBase:
    """Shopify Admin API base connector with authentication"""

    API_VERSION = "2026-01"

    def __init__(self) -> None:
        self.client_id = os.getenv("SHOPIFY_CLIENT_ID")
        self.client_secret = os.getenv("SHOPIFY_CLIENT_SECRET")

    def _get_base_url(self, shop_domain: str) -> str:
        """Get base URL for a shop"""
        return f"https://{shop_domain}/admin/api/{self.API_VERSION}"

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token"""
        cred = CredentialManager.get_credential(org_id, user_id, "shopify")

        if not cred:
            raise CredentialMissingError("shopify", org_id, user_id)

        # Shopify tokens don't expire for offline access, but check anyway
        expiry = cred.get("token_expiry")
        if expiry and expiry < datetime.utcnow() + timedelta(minutes=5):
            logger.info("Token expired, refreshing", service="shopify", org_id=org_id)
            return self._refresh_token(org_id, user_id, cred)

        return cred

    def _refresh_token(self, org_id: str, user_id: str, cred: dict[str, Any]) -> dict[str, Any]:
        """Refresh the access token (for online access mode)"""
        shop_domain = cred.get("shop_domain")
        if not shop_domain:
            raise ValueError("shop_domain is required but not found in credentials")

        token_data = http_client.post(
            url=f"https://{shop_domain}/admin/oauth/access_token",
            service="shopify",
            headers={"Content-Type": "application/json"},
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": cred["refresh_token"],
            },
        )

        new_expiry = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 86400))

        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="shopify",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", cred["refresh_token"]),
            token_expiry=new_expiry,
            extra_data={"shop_domain": shop_domain},
        )

        return {
            "access_token": token_data["access_token"],
            "shop_domain": shop_domain,
        }
