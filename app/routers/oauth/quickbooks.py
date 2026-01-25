"""
QuickBooks OAuth Routes

Handles OAuth authorization and callback for QuickBooks Online.
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
    parse_oauth_state_3parts,
)

logger = get_logger(__name__)
router = APIRouter(tags=["oauth"])


def _exchange_quickbooks_tokens(
    code: str, org_id: str, user_id: str
) -> tuple[dict[str, Any], datetime]:
    """Exchange authorization code for QuickBooks access/refresh tokens.

    Args:
        code: Authorization code from OAuth callback
        org_id: Organization ID for logging
        user_id: User ID for logging

    Returns:
        Tuple of (token_data dict, token_expiry datetime)

    Raises:
        HTTPException: If token exchange fails
    """
    client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
    client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")
    redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="QuickBooks OAuth not configured")

    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    logger.info(
        "Exchanging code for tokens",
        service="quickbooks",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_token_exchange_start",
    )

    token_start = time.time()
    response = requests.post(
        token_url,
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        auth=(client_id, client_secret),
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
        timeout=30,
    )
    token_duration_ms = (time.time() - token_start) * 1000

    if response.status_code != 200:
        logger.error(
            "Token exchange failed",
            service="quickbooks",
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            duration_ms=round(token_duration_ms, 2),
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

    token_data = response.json()
    token_expiry = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

    logger.info(
        "Token exchange successful",
        service="quickbooks",
        org_id=org_id,
        user_id=user_id,
        duration_ms=round(token_duration_ms, 2),
        token_expiry=token_expiry.isoformat(),
        log_event="oauth_token_exchange_success",
    )

    return token_data, token_expiry


def _store_quickbooks_credential(
    org_id: str,
    user_id: str,
    token_data: dict[str, Any],
    token_expiry: datetime,
    realm_id: str,
    credential_type: str,
) -> None:
    """Store QuickBooks OAuth credentials in database.

    Args:
        org_id: Organization ID
        user_id: User ID
        token_data: Token response from QuickBooks
        token_expiry: Token expiration datetime
        realm_id: QuickBooks company ID
        credential_type: Type of credential (customer/agent)
    """
    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="quickbooks",
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_expiry=token_expiry,
        realm_id=realm_id,
    )

    logger.info(
        "OAuth flow completed successfully",
        service="quickbooks",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_callback_success",
    )


@router.get("/oauth/quickbooks/authorize")
async def quickbooks_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate QuickBooks OAuth flow

    Redirects user to Intuit authorization page
    """
    logger.info(
        "OAuth authorization initiated",
        service="quickbooks",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_authorize_start",
    )

    client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
    redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")

    if not client_id or not redirect_uri:
        logger.error("OAuth not configured", service="quickbooks", log_event="oauth_config_error")
        raise HTTPException(status_code=500, detail="QuickBooks OAuth not configured")

    # State encodes org_id:user_id:credential_type for the callback
    state = f"{org_id}:{user_id}:{credential_type}"

    # OAuth authorization URL
    auth_base_url = "https://appcenter.intuit.com/connect/oauth2"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "state": state,
    }

    auth_url = f"{auth_base_url}?{urlencode(params)}"

    logger.debug("Redirecting to OAuth provider", service="quickbooks", log_event="oauth_redirect")

    return RedirectResponse(url=auth_url)


@router.get("/oauth/quickbooks/callback")
async def quickbooks_oauth_callback(code: str, state: str, realmId: str) -> RedirectResponse:
    """
    Handle QuickBooks OAuth callback

    Exchange authorization code for access/refresh tokens and store them.
    Redirects to N3 frontend on completion.
    """
    logger.info("OAuth callback received", service="quickbooks", log_event="oauth_callback_start")

    # Parse state first to get org_id for error redirects
    org_id: str | None = None
    try:
        org_id, user_id, credential_type = parse_oauth_state_3parts(state, "quickbooks")
    except HTTPException:
        return build_oauth_error_redirect(
            service="quickbooks",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        # Exchange authorization code for tokens
        token_data, token_expiry = _exchange_quickbooks_tokens(code, org_id, user_id)

        # Store credentials in database
        _store_quickbooks_credential(
            org_id, user_id, token_data, token_expiry, realmId, credential_type
        )

        return build_oauth_success_redirect(service="quickbooks", org_id=org_id)

    except HTTPException as e:
        return build_oauth_error_redirect(
            service="quickbooks",
            error="token_exchange_failed",
            error_description=str(e.detail),
            org_id=org_id,
        )
    except Exception as e:
        logger.error(
            "OAuth callback failed",
            service="quickbooks",
            error_type=type(e).__name__,
            log_event="oauth_callback_error",
            exc_info=True,
        )
        return build_oauth_error_redirect(
            service="quickbooks",
            error="callback_failed",
            error_description=str(e),
            org_id=org_id,
        )
