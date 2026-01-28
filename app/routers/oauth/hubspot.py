"""
HubSpot OAuth Routes

Handles OAuth authorization and callback for HubSpot CRM.

HubSpot OAuth Documentation:
https://developers.hubspot.com/docs/apps/legacy-apps/authentication/working-with-oauth

Token Lifecycle:
- Access tokens expire after 30 minutes
- Refresh tokens are long-lived (use /oauth/v1/token with grant_type=refresh_token)
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
    parse_oauth_state_3parts,
)

logger = get_logger(__name__)
router = APIRouter(tags=["oauth"])

# HubSpot OAuth endpoints
HUBSPOT_AUTH_URL = "https://app.hubspot.com/oauth/authorize"
HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"

# Comprehensive CRM scopes for full data access
# See: https://developers.hubspot.com/docs/api/oauth/scopes
HUBSPOT_SCOPES = " ".join([
    # Core CRM objects
    "crm.objects.contacts.read",
    "crm.objects.contacts.write",
    "crm.objects.companies.read",
    "crm.objects.companies.write",
    "crm.objects.deals.read",
    "crm.objects.deals.write",
    # Owners (for attribution)
    "crm.objects.owners.read",
    # Customer service
    "crm.objects.tickets.read",
    "crm.objects.tickets.write",
    # Commerce/quotes
    "crm.objects.line_items.read",
    "crm.objects.line_items.write",
    "crm.objects.quotes.read",
    # Products
    "crm.objects.products.read",
    # Lists (for segmentation)
    "crm.lists.read",
])


def _exchange_hubspot_tokens(
    code: str, org_id: str, user_id: str
) -> tuple[dict[str, Any], datetime]:
    """Exchange authorization code for HubSpot access/refresh tokens.

    Args:
        code: Authorization code from OAuth callback
        org_id: Organization ID for logging
        user_id: User ID for logging

    Returns:
        Tuple of (token_data dict, token_expiry datetime)

    Raises:
        HTTPException: If token exchange fails
    """
    client_id = os.getenv("HUBSPOT_CLIENT_ID")
    client_secret = os.getenv("HUBSPOT_CLIENT_SECRET")
    redirect_uri = os.getenv("HUBSPOT_REDIRECT_URI")

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=500, detail="HubSpot OAuth not configured")

    logger.info(
        "Exchanging code for tokens",
        service="hubspot",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_token_exchange_start",
    )

    token_start = time.time()
    response = requests.post(
        HUBSPOT_TOKEN_URL,
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
            service="hubspot",
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            response_text=response.text[:500] if response.text else None,
            duration_ms=round(token_duration_ms, 2),
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail="Token exchange failed")

    token_data = response.json()
    # HubSpot tokens expire after 30 minutes (1800 seconds)
    token_expiry = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 1800))

    logger.info(
        "Token exchange successful",
        service="hubspot",
        org_id=org_id,
        user_id=user_id,
        duration_ms=round(token_duration_ms, 2),
        token_expiry=token_expiry.isoformat(),
        log_event="oauth_token_exchange_success",
    )

    return token_data, token_expiry


def _store_hubspot_credential(
    org_id: str,
    user_id: str,
    token_data: dict[str, Any],
    token_expiry: datetime,
    credential_type: str,
) -> None:
    """Store HubSpot OAuth credentials in database.

    Args:
        org_id: Organization ID
        user_id: User ID
        token_data: Token response from HubSpot
        token_expiry: Token expiration datetime
        credential_type: Type of credential (customer/agent)
    """
    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="hubspot",
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_expiry=token_expiry,
    )

    logger.info(
        "OAuth flow completed successfully",
        service="hubspot",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_callback_success",
    )


@router.get("/oauth/hubspot/authorize")
async def hubspot_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate HubSpot OAuth flow

    Redirects user to HubSpot authorization page
    """
    logger.info(
        "OAuth authorization initiated",
        service="hubspot",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_authorize_start",
    )

    client_id = os.getenv("HUBSPOT_CLIENT_ID")
    redirect_uri = os.getenv("HUBSPOT_REDIRECT_URI")

    if not client_id or not redirect_uri:
        logger.error("OAuth not configured", service="hubspot", log_event="oauth_config_error")
        raise HTTPException(status_code=500, detail="HubSpot OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_3parts(org_id, user_id, credential_type)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": HUBSPOT_SCOPES,
        "state": state,
    }

    auth_url = f"{HUBSPOT_AUTH_URL}?{urlencode(params)}"

    logger.debug("Redirecting to OAuth provider", service="hubspot", log_event="oauth_redirect")

    return RedirectResponse(url=auth_url)


@router.get("/oauth/hubspot/callback")
async def hubspot_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle HubSpot OAuth callback

    Exchange authorization code for access/refresh tokens and store them.
    Redirects to N3 frontend on completion.
    """
    logger.info("OAuth callback received", service="hubspot", log_event="oauth_callback_start")

    # Parse state first to get org_id for error redirects
    org_id: str | None = None
    try:
        org_id, user_id, credential_type = parse_oauth_state_3parts(state, "hubspot")
    except HTTPException:
        return build_oauth_error_redirect(
            service="hubspot",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        # Exchange authorization code for tokens
        token_data, token_expiry = _exchange_hubspot_tokens(code, org_id, user_id)

        # Store credentials in database
        _store_hubspot_credential(org_id, user_id, token_data, token_expiry, credential_type)

        return build_oauth_success_redirect(service="hubspot", org_id=org_id)

    except HTTPException:
        return build_oauth_error_redirect(
            service="hubspot",
            error="token_exchange_failed",
            error_description="Token exchange failed",
            org_id=org_id,
        )
    except Exception as e:
        logger.error(
            "OAuth callback failed",
            service="hubspot",
            error_type=type(e).__name__,
            log_event="oauth_callback_error",
            exc_info=True,
        )
        return build_oauth_error_redirect(
            service="hubspot",
            error="callback_failed",
            error_description="An unexpected error occurred",
            org_id=org_id,
        )
