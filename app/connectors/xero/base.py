"""
Xero Accounting API connector - Base module with OAuth 2.0 authentication.

Reference: https://developer.xero.com/documentation/api/accounting/overview
API Version: api.xro/2.0 (January 2026)

Xero uses OAuth 2.0 with PKCE. Tokens expire after 30 minutes.
The refresh token is valid for 60 days from last use.
"""

import os
from datetime import datetime, timedelta
from typing import Any, cast

from app.database import CredentialManager
from app.errors import CredentialMissingError, ExternalAPIError, ValidationError
from app.http_client import http_client
from app.logging_config import get_logger

logger = get_logger(__name__)


class XeroBase:
    """Xero Accounting API base connector with OAuth 2.0 authentication."""

    API_BASE_URL = "https://api.xero.com/api.xro/2.0"
    CONNECTIONS_URL = "https://api.xero.com/connections"
    TOKEN_URL = "https://identity.xero.com/connect/token"

    # Xero API limits
    MINUTE_RATE_LIMIT = 60  # 60 calls per minute per tenant
    DAILY_RATE_LIMIT = 5000  # 5000 calls per day per tenant

    def __init__(self) -> None:
        self.client_id = os.getenv("XERO_CLIENT_ID", "")
        self.client_secret = os.getenv("XERO_CLIENT_SECRET", "")

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token, refreshing if necessary."""
        cred = CredentialManager.get_credential(org_id, user_id, "xero")

        if not cred:
            raise CredentialMissingError("xero", org_id, user_id)

        # Xero tokens expire after 30 minutes, refresh if within 5 minutes of expiry
        if cred.get("token_expiry") and cred["token_expiry"] < datetime.utcnow() + timedelta(
            minutes=5
        ):
            logger.info(
                "Xero token expired or expiring soon, refreshing",
                service="xero",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_needed",
            )
            return self._refresh_token(
                org_id, user_id, cred["refresh_token"], cred.get("tenant_id")
            )

        return cred

    def _refresh_token(
        self, org_id: str, user_id: str, refresh_token: str, tenant_id: str | None = None
    ) -> dict[str, Any]:
        """Refresh the OAuth 2.0 access token."""
        logger.info(
            "Refreshing Xero token",
            service="xero",
            org_id=org_id,
            user_id=user_id,
            log_event="token_refresh_start",
        )

        if not self.client_id or not self.client_secret:
            raise ValidationError(
                "credentials",
                "XERO_CLIENT_ID and XERO_CLIENT_SECRET environment variables required",
            )

        try:
            token_data: dict[str, Any] = http_client.post(
                url=self.TOKEN_URL,
                service="xero",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )

            new_expiry = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 1800))

            # Store updated credentials (tenant_id stored as realm_id)
            CredentialManager.store_credential(
                org_id=org_id,
                user_id=user_id,
                service="xero",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expiry=new_expiry,
                realm_id=tenant_id,
            )

            logger.info(
                "Xero token refreshed successfully",
                service="xero",
                org_id=org_id,
                user_id=user_id,
                expires_in_seconds=token_data.get("expires_in", 1800),
                log_event="token_refresh_success",
            )

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_expiry": new_expiry,
                "tenant_id": tenant_id,
            }

        except Exception as e:
            logger.error(
                "Xero token refresh failed",
                service="xero",
                org_id=org_id,
                user_id=user_id,
                error_type=type(e).__name__,
                log_event="token_refresh_error",
                exc_info=True,
            )
            raise

    def _get_tenant_id(self, cred: dict[str, Any], org_id: str, user_id: str) -> str:
        """Get the Xero tenant ID (organization ID in Xero's terms).

        If not stored in credentials, fetch from connections endpoint.
        """
        tenant_id = cred.get("tenant_id")
        if tenant_id:
            return str(tenant_id)

        # Fetch tenant from connections endpoint
        connections = self._get_connections(cred)
        if not connections:
            raise ValidationError(
                "tenant_id",
                "No Xero organizations connected. User must authorize access to an organization.",
            )

        # Use first connection by default
        tenant_id = connections[0]["tenantId"]

        # Update stored credential with tenant_id for future use (stored as realm_id)
        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="xero",
            access_token=cred["access_token"],
            refresh_token=cred.get("refresh_token"),
            token_expiry=cred.get("token_expiry"),
            realm_id=tenant_id,
        )

        return str(tenant_id)

    def _get_connections(self, cred: dict[str, Any]) -> list[dict[str, Any]]:
        """Get list of connected Xero organizations."""
        # Xero connections endpoint returns a list directly (not wrapped in a dict)
        result = http_client.get(
            url=self.CONNECTIONS_URL,
            service="xero",
            headers={"Authorization": f"Bearer {cred['access_token']}"},
        )
        # Cast to list - Xero returns array directly
        return cast(list[dict[str, Any]], result)

    def _make_api_call(
        self,
        method: str,
        endpoint: str,
        cred: dict[str, Any],
        tenant_id: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API call to Xero."""
        url = f"{self.API_BASE_URL}/{endpoint}"

        headers = {
            "Authorization": f"Bearer {cred['access_token']}",
            "Xero-Tenant-Id": tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        logger.debug(
            "Xero API request",
            service="xero",
            method=method,
            endpoint=endpoint,
            tenant_id=tenant_id,
            log_event="xero_api_request",
        )

        if method == "GET":
            return http_client.get(url=url, service="xero", headers=headers, params=params)
        elif method == "POST":
            return http_client.post(url=url, service="xero", headers=headers, json=data)
        elif method == "PUT":
            return http_client.put(url=url, service="xero", headers=headers, json=data)
        elif method == "DELETE":
            return http_client.delete(url=url, service="xero", headers=headers)
        else:
            return cast(
                dict[str, Any],
                http_client.request(
                    method=method, url=url, service="xero", headers=headers, json=data
                ),
            )

    def _handle_xero_error(self, error: Exception, operation: str) -> None:
        """Handle Xero-specific error responses."""
        error_message = str(error)

        # Parse common Xero error patterns
        if "ValidationException" in error_message:
            raise ValidationError("xero_data", f"Xero validation error: {error_message}")
        if "ObjectNotFound" in error_message:
            raise ExternalAPIError("xero", 404, f"Resource not found: {error_message}")
        if "RateLimitExceeded" in error_message:
            raise ExternalAPIError("xero", 429, "Xero rate limit exceeded")

        raise ExternalAPIError("xero", 500, f"Xero {operation} failed: {error_message}")

    def get_organization(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get details of the connected Xero organization."""
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        result = self._make_api_call("GET", "Organisation", cred, tenant_id)

        orgs = result.get("Organisations", [])
        if not orgs:
            raise ExternalAPIError("xero", 404, "No organization data returned")

        org_data = orgs[0]
        logger.info(
            "Xero organization retrieved",
            service="xero",
            org_name=org_data.get("Name"),
            log_event="organization_retrieved",
        )

        return {
            "organization_id": org_data.get("OrganisationID"),
            "name": org_data.get("Name"),
            "legal_name": org_data.get("LegalName"),
            "short_code": org_data.get("ShortCode"),
            "edition": org_data.get("Edition"),
            "class": org_data.get("OrganisationEntityType"),
            "country_code": org_data.get("CountryCode"),
            "base_currency": org_data.get("BaseCurrency"),
            "timezone": org_data.get("Timezone"),
            "financial_year_end_day": org_data.get("FinancialYearEndDay"),
            "financial_year_end_month": org_data.get("FinancialYearEndMonth"),
            "sales_tax_basis": org_data.get("SalesTaxBasis"),
            "sales_tax_period": org_data.get("SalesTaxPeriod"),
            "status": "success",
        }

    def list_connections(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all Xero organizations the user has connected."""
        cred = self._get_access_token(org_id, user_id)
        connections = self._get_connections(cred)

        return {
            "connections": [
                {
                    "tenant_id": conn.get("tenantId"),
                    "tenant_name": conn.get("tenantName"),
                    "tenant_type": conn.get("tenantType"),
                    "created_date": conn.get("createdDateUtc"),
                    "updated_date": conn.get("updatedDateUtc"),
                }
                for conn in connections
            ],
            "count": len(connections),
            "status": "success",
        }
