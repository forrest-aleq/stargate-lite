"""
Stripe Connect OAuth Routes

Handles OAuth authorization and callback for Stripe Connect.
Allows customers to connect their own Stripe accounts.
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

# Stripe Connect OAuth URLs
STRIPE_CONNECT_AUTHORIZE_URL = "https://connect.stripe.com/oauth/authorize"
STRIPE_CONNECT_TOKEN_URL = "https://connect.stripe.com/oauth/token"


def _exchange_stripe_tokens(code: str, org_id: str, user_id: str) -> dict[str, Any]:
    """Exchange authorization code for Stripe access tokens.

    Args:
        code: Authorization code from OAuth callback
        org_id: Organization ID for logging
        user_id: User ID for logging

    Returns:
        Token data dict containing access_token, stripe_user_id, etc.

    Raises:
        HTTPException: If token exchange fails
    """
    client_secret = os.getenv("STRIPE_SECRET_KEY")

    if not client_secret:
        raise HTTPException(status_code=500, detail="Stripe OAuth not configured")

    logger.info(
        "Exchanging code for tokens",
        service="stripe",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_token_exchange_start",
    )

    token_start = time.time()
    # Stripe Connect uses form data with client_secret (not Basic Auth)
    response = requests.post(
        STRIPE_CONNECT_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    token_duration_ms = (time.time() - token_start) * 1000

    if response.status_code != 200:
        # Log full error for debugging (truncate for safety)
        logger.error(
            "Token exchange failed",
            service="stripe",
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            response_text=response.text[:500] if response.text else None,
            duration_ms=round(token_duration_ms, 2),
            log_event="oauth_token_exchange_error",
        )
        # Return generic message to avoid leaking sensitive error details
        raise HTTPException(status_code=500, detail="Token exchange failed")

    token_data: dict[str, Any] = response.json()

    logger.info(
        "Token exchange successful",
        service="stripe",
        org_id=org_id,
        user_id=user_id,
        duration_ms=round(token_duration_ms, 2),
        stripe_user_id=token_data.get("stripe_user_id"),
        log_event="oauth_token_exchange_success",
    )

    return token_data


def _store_stripe_credential(
    org_id: str,
    user_id: str,
    token_data: dict[str, Any],
    credential_type: str,
) -> None:
    """Store Stripe Connect credentials in database.

    Args:
        org_id: Organization ID
        user_id: User ID
        token_data: Token response from Stripe (includes access_token, stripe_user_id)
        credential_type: Type of credential (customer/agent)
    """
    # Stripe Connect tokens don't expire - use 100 year expiry
    token_expiry = datetime.utcnow() + timedelta(days=36500)

    # Store stripe_user_id in extra_data for connected account operations
    extra_data = {
        "stripe_user_id": token_data.get("stripe_user_id"),
        "scope": token_data.get("scope"),
        "livemode": token_data.get("livemode"),
        "token_type": token_data.get("token_type"),
    }

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="stripe",
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=token_expiry,
        credential_type=credential_type,
        extra_data=extra_data,
    )

    logger.info(
        "OAuth flow completed successfully",
        service="stripe",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        stripe_user_id=token_data.get("stripe_user_id"),
        log_event="oauth_callback_success",
    )


@router.get("/oauth/stripe/authorize")
async def stripe_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate Stripe Connect OAuth flow

    Redirects user to Stripe authorization page
    """
    logger.info(
        "OAuth authorization initiated",
        service="stripe",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_authorize_start",
    )

    client_id = os.getenv("STRIPE_CLIENT_ID")
    redirect_uri = os.getenv("STRIPE_REDIRECT_URI")

    if not client_id or not redirect_uri:
        logger.error("OAuth not configured", service="stripe", log_event="oauth_config_error")
        raise HTTPException(status_code=500, detail="Stripe Connect OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_3parts(org_id, user_id, credential_type)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "read_write",
        "state": state,
    }

    auth_url = f"{STRIPE_CONNECT_AUTHORIZE_URL}?{urlencode(params)}"

    logger.debug("Redirecting to OAuth provider", service="stripe", log_event="oauth_redirect")

    return RedirectResponse(url=auth_url)


@router.get("/oauth/stripe/callback")
async def stripe_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Stripe Connect OAuth callback

    Exchange authorization code for access token and store credentials.
    Redirects to N3 frontend on completion.
    """
    logger.info("OAuth callback received", service="stripe", log_event="oauth_callback_start")

    # Parse state first to get org_id for error redirects
    org_id: str | None = None
    try:
        org_id, user_id, credential_type = parse_oauth_state_3parts(state, "stripe")
    except HTTPException:
        return build_oauth_error_redirect(
            service="stripe",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        # Exchange authorization code for tokens
        token_data = _exchange_stripe_tokens(code, org_id, user_id)

        # Store credentials in database
        _store_stripe_credential(org_id, user_id, token_data, credential_type)

        return build_oauth_success_redirect(service="stripe", org_id=org_id)

    except HTTPException:
        return build_oauth_error_redirect(
            service="stripe",
            error="token_exchange_failed",
            error_description="Token exchange failed",
            org_id=org_id,
        )
    except Exception as e:
        logger.error(
            "OAuth callback failed",
            service="stripe",
            error_type=type(e).__name__,
            log_event="oauth_callback_error",
            exc_info=True,
        )
        return build_oauth_error_redirect(
            service="stripe",
            error="callback_failed",
            error_description="An unexpected error occurred",
            org_id=org_id,
        )
