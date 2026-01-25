"""
HR & Payroll OAuth Routes.

Handles OAuth authorization and callback for:
- Gusto (payroll, employees, benefits)

Gusto OAuth Documentation:
https://docs.gusto.com/app-integrations/v2024-03-01/docs/oauth2
"""

import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.logging_config import get_logger
from app.routers.oauth.base import (
    build_oauth_error_redirect,
    build_oauth_success_redirect,
    get_env_or_raise,
    parse_oauth_state_3parts,
)

logger = get_logger(__name__)

router = APIRouter(tags=["oauth"])

# Gusto OAuth endpoints
# Production: api.gusto.com
# Demo/Sandbox: api.gusto-demo.com
GUSTO_AUTH_URL = "https://api.gusto.com/oauth/authorize"
GUSTO_TOKEN_URL = "https://api.gusto.com/oauth/token"
GUSTO_DEMO_AUTH_URL = "https://api.gusto-demo.com/oauth/authorize"
GUSTO_DEMO_TOKEN_URL = "https://api.gusto-demo.com/oauth/token"


def _get_gusto_urls() -> tuple[str, str]:
    """Get Gusto OAuth URLs based on environment."""
    use_demo = os.getenv("GUSTO_USE_DEMO", "false").lower() == "true"
    if use_demo:
        return GUSTO_DEMO_AUTH_URL, GUSTO_DEMO_TOKEN_URL
    return GUSTO_AUTH_URL, GUSTO_TOKEN_URL


@router.get("/oauth/gusto/authorize")
async def gusto_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate Gusto OAuth flow.

    Redirects user to Gusto authorization page to grant access to payroll data.

    Args:
        org_id: Organization identifier
        user_id: User identifier
        credential_type: Type of credential (customer/agent)

    Returns:
        Redirect to Gusto authorization page
    """
    client_id = get_env_or_raise("GUSTO_CLIENT_ID", "Gusto")
    redirect_uri = get_env_or_raise("GUSTO_REDIRECT_URI", "Gusto")

    auth_url, _ = _get_gusto_urls()

    # State encodes org_id:user_id:credential_type for the callback
    state = f"{org_id}:{user_id}:{credential_type}"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
    }

    authorization_url = f"{auth_url}?{urlencode(params)}"

    logger.info(
        "Initiating Gusto OAuth flow",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_gusto_authorize_start",
    )

    return RedirectResponse(url=authorization_url)


@router.get("/oauth/gusto/callback")
async def gusto_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Gusto OAuth callback.

    Exchange authorization code for access/refresh tokens and store them.
    Redirects to N3 frontend on completion.
    """
    # Parse state first
    try:
        org_id, user_id, _credential_type = parse_oauth_state_3parts(state, "gusto")
    except HTTPException:
        return build_oauth_error_redirect(
            service="gusto",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        client_id = get_env_or_raise("GUSTO_CLIENT_ID", "Gusto")
        client_secret = get_env_or_raise("GUSTO_CLIENT_SECRET", "Gusto")
        redirect_uri = get_env_or_raise("GUSTO_REDIRECT_URI", "Gusto")

        _, token_url = _get_gusto_urls()

        response = requests.post(
            token_url,
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

        if response.status_code != 200:
            logger.error("Gusto token exchange failed", status_code=response.status_code)
            return build_oauth_error_redirect(
                service="gusto",
                error="token_exchange_failed",
                error_description="Token exchange with Gusto failed",
                org_id=org_id,
            )

        token_data = response.json()
        expires_in = token_data.get("expires_in", 7200)
        token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="gusto",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=token_expiry,
        )

        logger.info("Gusto OAuth completed", org_id=org_id)
        return build_oauth_success_redirect(service="gusto", org_id=org_id)

    except HTTPException as e:
        return build_oauth_error_redirect(
            service="gusto",
            error="config_error",
            error_description=str(e.detail),
            org_id=org_id,
        )
    except Exception as e:
        logger.error("Gusto OAuth callback failed", error=str(e), exc_info=True)
        return build_oauth_error_redirect(
            service="gusto",
            error="callback_failed",
            error_description=str(e),
            org_id=org_id,
        )
