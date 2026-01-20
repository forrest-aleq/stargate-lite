"""
NetSuite REST API connector base class with bulletproof authentication.

Supports both OAuth 2.0 (Bearer token) and TBA (Token-Based Auth / OAuth 1.0).
Reference: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_4247329078.html

CRITICAL: SOAP is deprecated as of 2025.2. Use REST only.
"""

import json
import os
from typing import Any, cast

from app.database import CredentialManager
from app.errors import CredentialMissingError, ExternalAPIError, ValidationError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class NetSuiteBase:
    """
    NetSuite REST API connector base class.

    Authentication methods supported:
    1. OAuth 2.0 - Uses Bearer token (access_token in credentials)
    2. TBA (OAuth 1.0) - Uses consumer_key, consumer_secret, token_key, token_secret

    The connector auto-detects which method to use based on stored credentials.
    """

    def __init__(self) -> None:
        # Global config (from env - used for TBA if not per-tenant)
        self.account_id = os.getenv("NETSUITE_ACCOUNT_ID", "")
        self.consumer_key = os.getenv("NETSUITE_CONSUMER_KEY", "")
        self.consumer_secret = os.getenv("NETSUITE_CONSUMER_SECRET", "")

    def _get_base_url(self, account_id: str) -> str:
        """Get REST API base URL for the account."""
        # Account IDs may have underscores that need to be replaced with hyphens
        # e.g., "12345_SB1" becomes "12345-sb1"
        normalized = account_id.lower().replace("_", "-")
        return f"https://{normalized}.suitetalk.api.netsuite.com/services/rest"

    def _get_credentials(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get stored credentials for this org/user."""
        cred = CredentialManager.get_credential(org_id, user_id, "netsuite")

        if not cred:
            raise CredentialMissingError("netsuite", org_id, user_id)

        return cred

    def _get_auth_header(self, cred: dict[str, Any], method: str, url: str) -> dict[str, str]:
        """
        Generate authentication header based on credential type.

        If credentials contain 'access_token' -> OAuth 2.0 Bearer token
        If credentials contain 'token_key' and 'token_secret' -> TBA (OAuth 1.0)
        """
        # OAuth 2.0 path - simple Bearer token
        if cred.get("access_token"):
            return {"Authorization": f"Bearer {cred['access_token']}"}

        # TBA (OAuth 1.0) path - requires signature generation
        if cred.get("token_key") and cred.get("token_secret"):
            return self._generate_tba_header(cred, method, url)

        raise ValidationError(
            "credentials",
            "NetSuite credentials must contain either 'access_token' (OAuth 2.0) "
            "or 'token_key'/'token_secret' (TBA)",
        )

    def _generate_tba_header(self, cred: dict[str, Any], method: str, url: str) -> dict[str, str]:
        """
        Generate OAuth 1.0 TBA authorization header.

        Uses requests-oauthlib for proper signature generation.
        Reference: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1534941088.html
        """
        try:
            from requests_oauthlib import OAuth1
        except ImportError as err:
            raise ImportError(
                "requests-oauthlib is required for NetSuite TBA authentication. "
                "Install with: pip install requests-oauthlib"
            ) from err

        # Get credentials - prefer per-tenant, fall back to global env
        consumer_key = cred.get("consumer_key") or self.consumer_key
        consumer_secret = cred.get("consumer_secret") or self.consumer_secret
        token_key = cred["token_key"]
        token_secret = cred["token_secret"]
        realm = cred.get("account_id") or self.account_id

        if not all([consumer_key, consumer_secret, token_key, token_secret, realm]):
            raise ValidationError(
                "credentials",
                "TBA requires: consumer_key, consumer_secret, token_key, token_secret, account_id",
            )

        # Create OAuth1 auth object
        oauth = OAuth1(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=token_key,
            resource_owner_secret=token_secret,
            realm=realm,
            signature_method="HMAC-SHA256",
        )

        # Generate the signed header using a dummy request
        import requests

        req = requests.Request(method=method, url=url)
        prepared = req.prepare()
        oauth_signed = oauth(prepared)

        return {"Authorization": oauth_signed.headers.get("Authorization", "")}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        cred: dict[str, Any],
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make authenticated request to NetSuite REST API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (e.g., "record/v1/journalentry")
            cred: Credential dict from _get_credentials
            data: Request body (for POST/PUT/PATCH)
            params: Query parameters

        Returns:
            Response JSON as dict
        """
        account_id = cred.get("account_id") or self.account_id
        base_url = self._get_base_url(account_id)
        url = f"{base_url}/{endpoint}"

        if params:
            from urllib.parse import urlencode

            url = f"{url}?{urlencode(params)}"

        logger.debug(
            "NetSuite API request",
            service="netsuite",
            method=method,
            endpoint=endpoint,
            account_id=account_id,
            log_event="netsuite_api_request",
        )

        # Get auth header (OAuth 2.0 or TBA)
        auth_header = self._get_auth_header(cred, method, url)

        headers = {
            **auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            raise ValidationError("method", f"Unsupported HTTP method: {method}")

        try:
            # Special handling for DELETE which may return 204 No Content
            if method == "DELETE":
                response = http_client.request(
                    method=method,
                    url=url,
                    service="netsuite",
                    headers=headers,
                    json=data if data else None,
                    parse_json=False,
                )
                if response.status_code == 204:
                    return {"status": "deleted"}
                try:
                    return cast(dict[str, Any], response.json())
                except (json.JSONDecodeError, ValueError):
                    return {"status": "deleted", "status_code": response.status_code}

            # GET, POST, PUT, PATCH - standard JSON response
            result: dict[str, Any] = http_client.request(
                method=method,
                url=url,
                service="netsuite",
                headers=headers,
                json=data if data else None,
            )
            return result

        except Exception as e:
            error_msg = str(e)
            # Parse common NetSuite errors for better messages
            if "INVALID_KEY_OR_REF" in error_msg:
                raise ExternalAPIError(
                    "netsuite",
                    400,
                    f"Invalid reference ID. Check IDs. {error_msg}",
                ) from e
            if "INVALID_LOGIN" in error_msg:
                raise CredentialMissingError("netsuite", "org", "user") from e
            raise

    def _make_suiteql_request(
        self, cred: dict[str, Any], query: str, limit: int = 1000, offset: int = 0
    ) -> dict[str, Any]:
        """
        Execute a SuiteQL query.

        SuiteQL is NetSuite's SQL-like query language.
        Max 100,000 results, 1,000 per page.

        Reference: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_157909186990.html
        """
        account_id = cred.get("account_id") or self.account_id
        base_url = self._get_base_url(account_id)
        url = f"{base_url}/query/v1/suiteql"

        params = {"limit": min(limit, 1000), "offset": offset}
        from urllib.parse import urlencode

        full_url = f"{url}?{urlencode(params)}"

        auth_header = self._get_auth_header(cred, "POST", full_url)

        headers = {
            **auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "transient",  # Required for SuiteQL
        }

        result: dict[str, Any] = http_client.request(
            method="POST",
            url=full_url,
            service="netsuite",
            headers=headers,
            json={"q": query},
        )

        return result
