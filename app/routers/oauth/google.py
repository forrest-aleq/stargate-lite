"""
Google OAuth Routes

Handles OAuth authorization and callback for Google Workspace (Gmail, Drive, Calendar, Sheets).

Google OAuth Documentation:
https://developers.google.com/identity/protocols/oauth2

Token Lifecycle:
- Access tokens expire after 1 hour (3600 seconds)
- Refresh tokens are long-lived but limited to 100 per user per client
- Use access_type=offline and prompt=consent to get refresh token
"""

import os
import time
from datetime import UTC, datetime, timedelta
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
    build_signed_state_4parts,
    parse_oauth_state_4parts,
)

logger = get_logger(__name__)
router = APIRouter(tags=["oauth"])

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Service-specific scopes
# See: https://developers.google.com/identity/protocols/oauth2/scopes
GOOGLE_SCOPE_MAP = {
    "gmail": " ".join(
        [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.labels",
        ]
    ),
    "drive": " ".join(
        [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
        ]
    ),
    "calendar": " ".join(
        [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
        ]
    ),
    "sheets": " ".join(
        [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ]
    ),
    "all": " ".join(
        [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
    ),
}


def _exchange_google_tokens(
    code: str, org_id: str, user_id: str, service: str
) -> tuple[dict[str, Any], datetime]:
    """Exchange authorization code for Google access/refresh tokens.

    Args:
        code: Authorization code from OAuth callback
        org_id: Organization ID for logging
        user_id: User ID for logging
        service: Google service name (gmail, drive, etc.)

    Returns:
        Tuple of (token_data dict, token_expiry datetime)

    Raises:
        HTTPException: If token exchange fails
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    logger.info(
        "Exchanging code for tokens",
        service="google",
        google_service=service,
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_token_exchange_start",
    )

    token_start = time.time()
    response = requests.post(
        GOOGLE_TOKEN_URL,
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
            service="google",
            google_service=service,
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            response_text=response.text[:500] if response.text else None,
            duration_ms=round(token_duration_ms, 2),
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail="Token exchange failed")

    token_data = response.json()
    # Google tokens expire after 1 hour (3600 seconds)
    token_expiry = datetime.now(UTC) + timedelta(seconds=token_data.get("expires_in", 3600))

    logger.info(
        "Token exchange successful",
        service="google",
        google_service=service,
        org_id=org_id,
        user_id=user_id,
        duration_ms=round(token_duration_ms, 2),
        token_expiry=token_expiry.isoformat(),
        has_refresh_token=bool(token_data.get("refresh_token")),
        log_event="oauth_token_exchange_success",
    )

    return token_data, token_expiry


def _store_google_credential(
    org_id: str,
    user_id: str,
    token_data: dict[str, Any],
    token_expiry: datetime,
    credential_type: str,
    service: str,
) -> None:
    """Store Google OAuth credentials in database.

    Args:
        org_id: Organization ID
        user_id: User ID
        token_data: Token response from Google
        token_expiry: Token expiration datetime
        credential_type: Type of credential (customer/agent)
        service: Google service name
    """
    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="google",
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=token_expiry,
        extra_data={"google_service": service},
    )

    logger.info(
        "OAuth flow completed successfully",
        service="google",
        google_service=service,
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_callback_success",
    )


@router.get("/oauth/google/authorize")
async def google_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", service: str = "gmail"
) -> RedirectResponse:
    """
    Initiate Google Workspace OAuth flow

    Redirects user to Google authorization page

    Args:
        service: gmail, drive, calendar, sheets, all (determines scopes)
        credential_type: "customer" or "agent"
    """
    logger.info(
        "OAuth authorization initiated",
        service="google",
        google_service=service,
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_authorize_start",
    )

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if not client_id or not redirect_uri:
        logger.error("OAuth not configured", service="google", log_event="oauth_config_error")
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_4parts(org_id, user_id, credential_type, service)

    scopes = GOOGLE_SCOPE_MAP.get(service, GOOGLE_SCOPE_MAP["all"])

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "access_type": "offline",  # Get refresh token
        "prompt": "consent",  # Force consent to ensure refresh token
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    logger.debug(
        "Redirecting to OAuth provider",
        service="google",
        google_service=service,
        log_event="oauth_redirect",
    )

    return RedirectResponse(url=auth_url)


@router.get("/oauth/google/callback")
async def google_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Google OAuth callback

    Exchange authorization code for access/refresh tokens and store them.
    Redirects to N3 frontend on completion.
    """
    logger.info("OAuth callback received", service="google", log_event="oauth_callback_start")

    # Parse state first to get org_id for error redirects
    org_id: str | None = None
    service: str = "google"
    try:
        org_id, user_id, credential_type, service = parse_oauth_state_4parts(state, "google")
    except HTTPException:
        return build_oauth_error_redirect(
            service="google",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        # Exchange authorization code for tokens
        token_data, token_expiry = _exchange_google_tokens(code, org_id, user_id, service)

        # Store credentials in database
        _store_google_credential(
            org_id, user_id, token_data, token_expiry, credential_type, service
        )

        return build_oauth_success_redirect(service="google", org_id=org_id)

    except HTTPException:
        return build_oauth_error_redirect(
            service="google",
            error="token_exchange_failed",
            error_description="Token exchange failed",
            org_id=org_id,
        )
    except Exception as e:
        logger.error(
            "OAuth callback failed",
            service="google",
            google_service=service,
            error_type=type(e).__name__,
            log_event="oauth_callback_error",
            exc_info=True,
        )
        return build_oauth_error_redirect(
            service="google",
            error="callback_failed",
            error_description="An unexpected error occurred",
            org_id=org_id,
        )
