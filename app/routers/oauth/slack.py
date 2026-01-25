"""
Slack OAuth Routes

Handles OAuth authorization and callback for Slack.
"""

import os
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
)

logger = get_logger(__name__)
router = APIRouter(tags=["oauth"])


@router.get("/oauth/slack/authorize")
async def slack_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "agent"
) -> RedirectResponse:
    """
    Initiate Slack OAuth flow

    Redirects user to Slack authorization page
    Note: Slack is always an agent credential (bot acting on behalf of workspace)
    """
    client_id = os.getenv("SLACK_CLIENT_ID")
    redirect_uri = os.getenv("SLACK_REDIRECT_URI")

    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="Slack OAuth not configured")

    # State encodes org_id:user_id:credential_type
    state = f"{org_id}:{user_id}:{credential_type}"

    # Slack OAuth scopes (v2 granular scopes)
    scopes = "chat:write channels:read channels:history files:write files:read users:read"

    params = {"client_id": client_id, "redirect_uri": redirect_uri, "scope": scopes, "state": state}

    auth_url = f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/slack/callback")
async def slack_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Slack OAuth callback

    Exchange authorization code for access/refresh tokens and store them.
    State format: {org_id}:{user_id}:{credential_type}
    Redirects to N3 frontend on completion.
    """
    # Parse state first
    parts = state.split(":")
    if len(parts) != 3:
        return build_oauth_error_redirect(
            service="slack",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    org_id, user_id, credential_type = parts

    if not org_id or not user_id or not credential_type:
        return build_oauth_error_redirect(
            service="slack",
            error="invalid_state",
            error_description="Invalid state parameter: empty values",
        )

    try:
        # Exchange code for tokens (Slack OAuth v2)
        client_id = os.getenv("SLACK_CLIENT_ID")
        client_secret = os.getenv("SLACK_CLIENT_SECRET")
        redirect_uri = os.getenv("SLACK_REDIRECT_URI")

        token_url = "https://slack.com/api/oauth.v2.access"

        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.error("Slack token exchange failed", status_code=response.status_code)
            return build_oauth_error_redirect(
                service="slack",
                error="token_exchange_failed",
                error_description="Token exchange with Slack failed",
                org_id=org_id,
            )

        token_data = response.json()

        if not token_data.get("ok"):
            error_msg = token_data.get("error", "Unknown error")
            logger.error("Slack OAuth error", error=error_msg)
            return build_oauth_error_redirect(
                service="slack",
                error="oauth_error",
                error_description=f"Slack OAuth error: {error_msg}",
                org_id=org_id,
            )

        # Slack tokens don't expire, but store with far future date
        bot_access_token = token_data.get("access_token")

        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="slack",
            access_token=bot_access_token,
            refresh_token=None,
            token_expiry=datetime.utcnow() + timedelta(days=36500),
        )

        return build_oauth_success_redirect(service="slack", org_id=org_id)

    except Exception as e:
        logger.error("Slack OAuth callback failed", error=str(e), exc_info=True)
        return build_oauth_error_redirect(
            service="slack",
            error="callback_failed",
            error_description=str(e),
            org_id=org_id,
        )
