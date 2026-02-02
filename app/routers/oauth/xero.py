"""
Xero OAuth Routes

Handles OAuth 2.0 authorization and callback for Xero Accounting.

Xero OAuth flow:
1. Redirect user to Xero login with scopes
2. User authorizes, Xero redirects back with code
3. Exchange code for access/refresh tokens (form data, not Basic Auth)
4. Call /connections to get tenant ID (Xero org)
5. Store credentials with tenant ID as realm_id

Reference: https://developer.xero.com/documentation/guides/oauth2/auth-flow/
"""

import os
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.logging_config import get_logger
from app.routers.oauth.base import (
    build_oauth_error_redirect,
    build_oauth_success_redirect,
    build_signed_state_3parts,
    get_env_or_raise,
    parse_oauth_state_3parts,
)

logger = get_logger(__name__)
router = APIRouter(tags=["oauth"])

# Xero OAuth endpoints
XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_CONNECTIONS_URL = "https://api.xero.com/connections"

# Scopes required for full accounting access + offline refresh
XERO_SCOPES = (
    "openid profile email "
    "accounting.transactions accounting.transactions.read "
    "accounting.settings accounting.settings.read "
    "accounting.contacts accounting.contacts.read "
    "accounting.attachments accounting.attachments.read "
    "accounting.reports.read "
    "offline_access"
)


def _exchange_xero_tokens(
    code: str, org_id: str, user_id: str
) -> tuple[dict[str, Any], datetime]:
    """Exchange authorization code for Xero access/refresh tokens.

    Xero uses form-data POST (not Basic Auth) for token exchange.

    Returns:
        Tuple of (token_data dict, token_expiry datetime)

    Raises:
        HTTPException: If token exchange fails
    """
    client_id = get_env_or_raise("XERO_CLIENT_ID", "Xero")
    client_secret = get_env_or_raise("XERO_CLIENT_SECRET", "Xero")
    redirect_uri = get_env_or_raise("XERO_REDIRECT_URI", "Xero")

    logger.info(
        "Exchanging code for tokens",
        service="xero",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_token_exchange_start",
    )

    token_start = time.time()
    response = requests.post(
        XERO_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    token_duration_ms = (time.time() - token_start) * 1000

    if response.status_code != 200:
        logger.error(
            "Token exchange failed",
            service="xero",
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            response_body=response.text,
            redirect_uri=redirect_uri,
            duration_ms=round(token_duration_ms, 2),
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

    token_data = response.json()
    # Xero tokens expire in 30 minutes (1800 seconds)
    token_expiry = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 1800))

    logger.info(
        "Token exchange successful",
        service="xero",
        org_id=org_id,
        user_id=user_id,
        duration_ms=round(token_duration_ms, 2),
        token_expiry=token_expiry.isoformat(),
        log_event="oauth_token_exchange_success",
    )

    return token_data, token_expiry


def _fetch_xero_tenant_id(access_token: str) -> str | None:
    """Fetch the first connected tenant ID from Xero's /connections endpoint.

    Xero doesn't pass tenant info in the callback — you must query for it
    after getting the access token.

    Returns:
        Tenant ID string, or None if no connections found
    """
    try:
        response = requests.get(
            XERO_CONNECTIONS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        if response.status_code != 200:
            logger.warning(
                "Failed to fetch Xero connections",
                service="xero",
                status_code=response.status_code,
                log_event="xero_connections_fetch_error",
            )
            return None

        connections = response.json()
        if connections and len(connections) > 0:
            tenant_id = connections[0].get("tenantId")
            tenant_name = connections[0].get("tenantName")
            logger.info(
                "Xero tenant retrieved",
                service="xero",
                tenant_name=tenant_name,
                log_event="xero_tenant_fetched",
            )
            return tenant_id

        return None

    except Exception as e:
        logger.warning(
            "Error fetching Xero connections",
            service="xero",
            error_type=type(e).__name__,
            log_event="xero_connections_error",
        )
        return None


def _store_xero_credential(
    org_id: str,
    user_id: str,
    token_data: dict[str, Any],
    token_expiry: datetime,
    tenant_id: str | None,
    credential_type: str,
) -> None:
    """Store Xero OAuth credentials in database.

    Tenant ID is stored as realm_id for consistency with other connectors.
    """
    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="xero",
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=token_expiry,
        realm_id=tenant_id,
    )

    logger.info(
        "OAuth flow completed successfully",
        service="xero",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        tenant_id=tenant_id,
        log_event="oauth_callback_success",
    )


@router.get("/oauth/xero/authorize")
async def xero_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate Xero OAuth flow

    Redirects user to Xero authorization page with accounting scopes.
    """
    logger.info(
        "OAuth authorization initiated",
        service="xero",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_authorize_start",
    )

    client_id = get_env_or_raise("XERO_CLIENT_ID", "Xero")
    redirect_uri = get_env_or_raise("XERO_REDIRECT_URI", "Xero")

    state = build_signed_state_3parts(org_id, user_id, credential_type)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": XERO_SCOPES,
        "state": state,
    }

    auth_url = f"{XERO_AUTH_URL}?{urlencode(params)}"

    logger.debug("Redirecting to Xero OAuth", service="xero", log_event="oauth_redirect")

    return RedirectResponse(url=auth_url)


@router.get("/oauth/xero/callback")
async def xero_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Xero OAuth callback

    Exchange authorization code for tokens, fetch tenant ID from
    /connections, and store credentials.
    """
    logger.info("OAuth callback received", service="xero", log_event="oauth_callback_start")

    org_id: str | None = None
    try:
        org_id, user_id, credential_type = parse_oauth_state_3parts(state, "xero")
    except HTTPException:
        return build_oauth_error_redirect(
            service="xero",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        # Exchange authorization code for tokens
        token_data, token_expiry = _exchange_xero_tokens(code, org_id, user_id)

        # Fetch tenant ID from Xero connections endpoint
        tenant_id = _fetch_xero_tenant_id(token_data["access_token"])

        # Store credentials (tenant_id stored as realm_id)
        _store_xero_credential(
            org_id, user_id, token_data, token_expiry, tenant_id, credential_type
        )

        return build_oauth_success_redirect(service="xero", org_id=org_id)

    except HTTPException:
        return build_oauth_error_redirect(
            service="xero",
            error="token_exchange_failed",
            error_description="Token exchange failed",
            org_id=org_id,
        )
    except Exception as e:
        logger.error(
            "OAuth callback failed",
            service="xero",
            error_type=type(e).__name__,
            log_event="oauth_callback_error",
            exc_info=True,
        )
        return build_oauth_error_redirect(
            service="xero",
            error="callback_failed",
            error_description="An unexpected error occurred",
            org_id=org_id,
        )
