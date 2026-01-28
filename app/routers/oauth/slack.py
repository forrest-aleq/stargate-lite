"""
Slack OAuth Routes

Handles OAuth authorization and callback for Slack.

Slack OAuth Documentation:
https://api.slack.com/authentication/oauth-v2

Token Lifecycle:
- Bot tokens don't expire
- User tokens don't expire (unless revoked)
- Workspace tokens are long-lived
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

# Slack OAuth endpoints
SLACK_AUTH_URL = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"

# Slack bot scopes (v2 granular scopes)
# See: https://api.slack.com/scopes
SLACK_BOT_SCOPES = " ".join([
    "chat:write",           # Send messages
    "channels:read",        # View channel info
    "channels:history",     # View messages in channels
    "files:write",          # Upload files
    "files:read",           # Access files
    "users:read",           # View users
    "users:read.email",     # View user emails
    "groups:read",          # View private channels
    "im:read",              # View direct messages
    "mpim:read",            # View group direct messages
])


def _exchange_slack_tokens(
    code: str, org_id: str, user_id: str
) -> dict[str, Any]:
    """Exchange authorization code for Slack access token.

    Args:
        code: Authorization code from OAuth callback
        org_id: Organization ID for logging
        user_id: User ID for logging

    Returns:
        Token data dict containing access_token, team info, etc.

    Raises:
        HTTPException: If token exchange fails
    """
    client_id = os.getenv("SLACK_CLIENT_ID")
    client_secret = os.getenv("SLACK_CLIENT_SECRET")
    redirect_uri = os.getenv("SLACK_REDIRECT_URI")

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=500, detail="Slack OAuth not configured")

    logger.info(
        "Exchanging code for tokens",
        service="slack",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_token_exchange_start",
    )

    token_start = time.time()
    response = requests.post(
        SLACK_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
        timeout=30,
    )
    token_duration_ms = (time.time() - token_start) * 1000

    if response.status_code != 200:
        logger.error(
            "Token exchange HTTP failed",
            service="slack",
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            duration_ms=round(token_duration_ms, 2),
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail="Token exchange failed")

    token_data = response.json()

    # Slack returns ok=false on error even with HTTP 200
    if not token_data.get("ok"):
        error_code = token_data.get("error", "unknown_error")
        logger.error(
            "Slack OAuth error",
            service="slack",
            org_id=org_id,
            user_id=user_id,
            slack_error=error_code,
            duration_ms=round(token_duration_ms, 2),
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail=f"Slack error: {error_code}")

    logger.info(
        "Token exchange successful",
        service="slack",
        org_id=org_id,
        user_id=user_id,
        duration_ms=round(token_duration_ms, 2),
        team_id=token_data.get("team", {}).get("id"),
        log_event="oauth_token_exchange_success",
    )

    return token_data


def _store_slack_credential(
    org_id: str,
    user_id: str,
    token_data: dict[str, Any],
    credential_type: str,
) -> None:
    """Store Slack OAuth credentials in database.

    Args:
        org_id: Organization ID
        user_id: User ID
        token_data: Token response from Slack
        credential_type: Type of credential (customer/agent)
    """
    # Slack tokens don't expire - use 100 year expiry
    token_expiry = datetime.utcnow() + timedelta(days=36500)

    # Extract team and bot info
    extra_data = {
        "team_id": token_data.get("team", {}).get("id"),
        "team_name": token_data.get("team", {}).get("name"),
        "bot_user_id": token_data.get("bot_user_id"),
        "app_id": token_data.get("app_id"),
    }

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="slack",
        access_token=token_data["access_token"],
        refresh_token=None,  # Slack tokens don't use refresh
        token_expiry=token_expiry,
        extra_data=extra_data,
    )

    logger.info(
        "OAuth flow completed successfully",
        service="slack",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        team_id=extra_data.get("team_id"),
        log_event="oauth_callback_success",
    )


@router.get("/oauth/slack/authorize")
async def slack_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "agent"
) -> RedirectResponse:
    """
    Initiate Slack OAuth flow

    Redirects user to Slack authorization page
    Note: Slack is always an agent credential (bot acting on behalf of workspace)
    """
    logger.info(
        "OAuth authorization initiated",
        service="slack",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_authorize_start",
    )

    client_id = os.getenv("SLACK_CLIENT_ID")
    redirect_uri = os.getenv("SLACK_REDIRECT_URI")

    if not client_id or not redirect_uri:
        logger.error("OAuth not configured", service="slack", log_event="oauth_config_error")
        raise HTTPException(status_code=500, detail="Slack OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_3parts(org_id, user_id, credential_type)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": SLACK_BOT_SCOPES,
        "state": state,
    }

    auth_url = f"{SLACK_AUTH_URL}?{urlencode(params)}"

    logger.debug("Redirecting to OAuth provider", service="slack", log_event="oauth_redirect")

    return RedirectResponse(url=auth_url)


@router.get("/oauth/slack/callback")
async def slack_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Slack OAuth callback

    Exchange authorization code for access token and store credentials.
    Redirects to N3 frontend on completion.
    """
    logger.info("OAuth callback received", service="slack", log_event="oauth_callback_start")

    # Parse state first to get org_id for error redirects
    org_id: str | None = None
    try:
        org_id, user_id, credential_type = parse_oauth_state_3parts(state, "slack")
    except HTTPException:
        return build_oauth_error_redirect(
            service="slack",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        # Exchange authorization code for tokens
        token_data = _exchange_slack_tokens(code, org_id, user_id)

        # Store credentials in database
        _store_slack_credential(org_id, user_id, token_data, credential_type)

        return build_oauth_success_redirect(service="slack", org_id=org_id)

    except HTTPException:
        return build_oauth_error_redirect(
            service="slack",
            error="token_exchange_failed",
            error_description="Token exchange failed",
            org_id=org_id,
        )
    except Exception as e:
        logger.error(
            "OAuth callback failed",
            service="slack",
            error_type=type(e).__name__,
            log_event="oauth_callback_error",
            exc_info=True,
        )
        return build_oauth_error_redirect(
            service="slack",
            error="callback_failed",
            error_description="An unexpected error occurred",
            org_id=org_id,
        )
