"""
Sage Intacct REST API connector - Base module with OAuth 2.0 authentication.

Reference: https://developer.sage.com/intacct/docs/1/sage-intacct-rest-api/get-started
API Version: v1 (January 2026)

Sage Intacct uses OAuth 2.0 with authorization code flow.
Requires a Web Services developer license and Sage App Registry app.
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.database import CredentialManager
from app.errors import CredentialMissingError, ExternalAPIError, ValidationError
from app.http_client import http_client
from app.logging_config import get_logger
from app.posthog_client import track_token_refreshed

logger = get_logger(__name__)


class SageIntacctBase:
    """Sage Intacct REST API base connector with OAuth 2.0 authentication."""

    API_BASE_URL = "https://api.intacct.com/ia/api/v1"
    TOKEN_URL = "https://api.intacct.com/ia/api/v1/oauth2/token"
    AUTHORIZATION_URL = "https://api.intacct.com/ia/api/v1/oauth2/authorize"

    # Rate limits: varies by contract, typically 2 concurrent connections
    DEFAULT_TIMEOUT = (10, 60)  # Sage Intacct can be slow

    def __init__(self) -> None:
        self.client_id = os.getenv("SAGE_INTACCT_CLIENT_ID", "")
        self.client_secret = os.getenv("SAGE_INTACCT_CLIENT_SECRET", "")
        self.sender_id = os.getenv("SAGE_INTACCT_SENDER_ID", "")
        self.sender_password = os.getenv("SAGE_INTACCT_SENDER_PASSWORD", "")

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token, refreshing if necessary."""
        cred = CredentialManager.get_credential(org_id, user_id, "sage_intacct")

        if not cred:
            raise CredentialMissingError("sage_intacct", org_id, user_id)

        # Check if token is expired or about to expire (within 5 minutes)
        if cred.get("token_expiry") and cred["token_expiry"] < datetime.now(UTC) + timedelta(
            minutes=5
        ):
            logger.info(
                "Sage Intacct token expired or expiring soon, refreshing",
                service="sage_intacct",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_needed",
            )
            return self._refresh_token(org_id, user_id, cred["refresh_token"], cred.get("realm_id"))

        return cred

    def _refresh_token(
        self, org_id: str, user_id: str, refresh_token: str, company_id: str | None = None
    ) -> dict[str, Any]:
        """Refresh the OAuth 2.0 access token."""
        logger.info(
            "Refreshing Sage Intacct token",
            service="sage_intacct",
            org_id=org_id,
            user_id=user_id,
            log_event="token_refresh_start",
        )

        if not self.client_id or not self.client_secret:
            raise ValidationError(
                "credentials",
                "SAGE_INTACCT_CLIENT_ID and SAGE_INTACCT_CLIENT_SECRET required",
            )

        try:
            token_data: dict[str, Any] = http_client.post(
                url=self.TOKEN_URL,
                service="sage_intacct",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=self.DEFAULT_TIMEOUT,
            )

            # Token typically expires in 3600 seconds (1 hour)
            expires_in = token_data.get("expires_in", 3600)
            new_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)

            # Store updated credentials (company_id stored as realm_id)
            CredentialManager.store_credential(
                org_id=org_id,
                user_id=user_id,
                service="sage_intacct",
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", refresh_token),
                token_expiry=new_expiry,
                realm_id=company_id,
            )

            logger.info(
                "Sage Intacct token refreshed successfully",
                service="sage_intacct",
                org_id=org_id,
                user_id=user_id,
                expires_in_seconds=expires_in,
                log_event="token_refresh_success",
            )

            # Track successful token refresh to PostHog
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="sage_intacct",
                success=True,
            )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token", refresh_token),
                "token_expiry": new_expiry,
                "realm_id": company_id,
            }

        except Exception as e:
            logger.error(
                "Sage Intacct token refresh failed",
                service="sage_intacct",
                org_id=org_id,
                user_id=user_id,
                error_type=type(e).__name__,
                log_event="token_refresh_error",
                exc_info=True,
            )
            # Track failed token refresh to PostHog
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="sage_intacct",
                success=False,
            )
            raise

    def _get_company_id(self, cred: dict[str, Any]) -> str:
        """Get the Sage Intacct company ID from credentials."""
        company_id = cred.get("realm_id")
        if not company_id:
            raise ValidationError(
                "company_id",
                "Sage Intacct company ID not found in credentials. "
                "Ensure the user completed OAuth authorization.",
            )
        return str(company_id)

    def _make_api_call(
        self,
        method: str,
        endpoint: str,
        cred: dict[str, Any],
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API call to Sage Intacct REST API."""
        company_id = self._get_company_id(cred)
        url = f"{self.API_BASE_URL}/{endpoint}"

        headers = {
            "Authorization": f"Bearer {cred['access_token']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "ia-company-id": company_id,
        }

        logger.debug(
            "Sage Intacct API request",
            service="sage_intacct",
            method=method,
            endpoint=endpoint,
            company_id=company_id,
            log_event="sage_intacct_api_request",
        )

        try:
            if method == "GET":
                return http_client.get(
                    url=url,
                    service="sage_intacct",
                    headers=headers,
                    params=params,
                    timeout=self.DEFAULT_TIMEOUT,
                )
            elif method == "POST":
                return http_client.post(
                    url=url,
                    service="sage_intacct",
                    headers=headers,
                    json=data,
                    timeout=self.DEFAULT_TIMEOUT,
                )
            elif method == "PUT":
                return http_client.put(
                    url=url,
                    service="sage_intacct",
                    headers=headers,
                    json=data,
                    timeout=self.DEFAULT_TIMEOUT,
                )
            elif method == "PATCH":
                return http_client.patch(
                    url=url,
                    service="sage_intacct",
                    headers=headers,
                    json=data,
                    timeout=self.DEFAULT_TIMEOUT,
                )
            elif method == "DELETE":
                return http_client.delete(
                    url=url, service="sage_intacct", headers=headers, timeout=self.DEFAULT_TIMEOUT
                )
            else:
                return cast(
                    dict[str, Any],
                    http_client.request(
                        method=method,
                        url=url,
                        service="sage_intacct",
                        headers=headers,
                        json=data,
                        timeout=self.DEFAULT_TIMEOUT,
                    ),
                )
        except Exception as e:
            self._handle_sage_error(e, endpoint)
            raise  # Re-raise if not handled

    def _handle_sage_error(self, error: Exception, operation: str) -> None:
        """Handle Sage Intacct-specific error responses."""
        error_message = str(error)

        # Parse common Sage Intacct error patterns
        if "BL" in error_message and "Invalid" in error_message:
            raise ValidationError("sage_data", f"Sage validation error: {error_message}")
        if "XL" in error_message:
            raise ExternalAPIError("sage_intacct", 500, f"Sage XML error: {error_message}")
        if "404" in error_message or "not found" in error_message.lower():
            raise ExternalAPIError("sage_intacct", 404, f"Resource not found: {error_message}")

    def _paginate(
        self,
        endpoint: str,
        cred: dict[str, Any],
        params: dict[str, Any] | None = None,
        page_size: int = 100,
        max_pages: int = 10,
    ) -> list[dict[str, Any]]:
        """Paginate through Sage Intacct API results."""
        all_results: list[dict[str, Any]] = []
        params = params or {}
        params["size"] = page_size
        page = 0

        while page < max_pages:
            params["start"] = page * page_size
            result = self._make_api_call("GET", endpoint, cred, params=params)

            items = result.get("ia::result", [])
            if not items:
                break

            all_results.extend(items)

            # Check if there are more pages
            meta = result.get("ia::meta", {})
            total_count = meta.get("totalCount", 0)
            if len(all_results) >= total_count:
                break

            page += 1

        return all_results

    def get_company_info(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get company information from Sage Intacct."""
        cred = self._get_access_token(org_id, user_id)
        company_id = self._get_company_id(cred)

        result = self._make_api_call("GET", "objects/company-info", cred)

        info = result.get("ia::result", {})
        logger.info(
            "Sage Intacct company info retrieved",
            service="sage_intacct",
            company_id=company_id,
            log_event="company_info_retrieved",
        )

        return {
            "company_id": company_id,
            "company_name": info.get("name"),
            "legal_name": info.get("legalName"),
            "federal_id": info.get("federalId"),
            "base_currency": info.get("baseCurrency"),
            "country": info.get("country"),
            "address": {
                "line1": info.get("address", {}).get("addressLine1"),
                "city": info.get("address", {}).get("city"),
                "state": info.get("address", {}).get("state"),
                "postal_code": info.get("address", {}).get("postalCode"),
                "country": info.get("address", {}).get("country"),
            },
            "status": "success",
        }
