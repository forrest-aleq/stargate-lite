"""
Productivity & Database OAuth Routes.

Handles OAuth authorization and callback for:
- Airtable (spreadsheet-database hybrid, bases, records)

Airtable OAuth Documentation:
https://airtable.com/developers/web/api/oauth-reference
https://airtable.com/developers/web/guides/oauth-integrations

Note: Airtable requires PKCE (Proof Key for Code Exchange) for OAuth.
"""

import asyncio
import base64
import hashlib
import secrets
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.logging_config import get_logger
from app.routers.oauth.base import (
    build_oauth_error_redirect,
    build_oauth_success_redirect,
    build_signed_state_5parts,
    get_env_or_raise,
    parse_oauth_state_5parts,
)

logger = get_logger(__name__)

router = APIRouter(tags=["oauth"])

# Airtable OAuth endpoints
AIRTABLE_AUTH_URL = "https://airtable.com/oauth2/v1/authorize"
AIRTABLE_TOKEN_URL = "https://airtable.com/oauth2/v1/token"


def _generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code verifier and challenge (S256 method)."""
    code_verifier = secrets.token_urlsafe(32)
    sha256_hash = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


@router.get("/oauth/airtable/authorize")
async def airtable_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate Airtable OAuth flow with PKCE.

    Airtable requires PKCE (Proof Key for Code Exchange) for security.
    The code_verifier is embedded in the signed state parameter, making
    this flow completely stateless and compatible with multi-worker deployments.

    Args:
        org_id: Organization identifier
        user_id: User identifier
        credential_type: Type of credential (customer/agent)

    Returns:
        Redirect to Airtable authorization page
    """
    client_id = get_env_or_raise("AIRTABLE_CLIENT_ID", "Airtable")
    redirect_uri = get_env_or_raise("AIRTABLE_REDIRECT_URI", "Airtable")

    # Generate PKCE pair
    code_verifier, code_challenge = _generate_pkce_pair()

    # State is cryptographically signed and includes code_verifier
    # This is stateless - no in-memory or database storage needed
    # Format: org_id:user_id:credential_type:airtable:code_verifier:signature
    state = build_signed_state_5parts(org_id, user_id, credential_type, "airtable", code_verifier)

    # Airtable OAuth scopes
    # https://airtable.com/developers/web/api/scopes
    scopes = " ".join(
        [
            "data.records:read",  # Read records from tables
            "data.records:write",  # Create, update, delete records
            "schema.bases:read",  # Read base schema (tables, fields)
            "schema.bases:write",  # Modify base schema
            "webhook:manage",  # Create and manage webhooks
        ]
    )

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        "scope": scopes,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    authorization_url = f"{AIRTABLE_AUTH_URL}?{urlencode(params)}"

    logger.info(
        "Initiating Airtable OAuth flow with PKCE",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_airtable_authorize_start",
    )

    return RedirectResponse(url=authorization_url)


@router.get("/oauth/airtable/callback")
async def airtable_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Airtable OAuth callback with PKCE verification. Redirects to N3 on completion."""
    # Parse state to get org_id, user_id, and code_verifier
    # The code_verifier is embedded in the signed state (stateless PKCE)
    org_id: str | None = None
    try:
        org_id, user_id, credential_type, _sub_service, code_verifier = parse_oauth_state_5parts(
            state, "airtable"
        )
    except HTTPException:
        return build_oauth_error_redirect(
            service="airtable",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        client_id = get_env_or_raise("AIRTABLE_CLIENT_ID", "Airtable")
        client_secret = get_env_or_raise("AIRTABLE_CLIENT_SECRET", "Airtable")
        redirect_uri = get_env_or_raise("AIRTABLE_REDIRECT_URI", "Airtable")

        logger.info(
            "Exchanging code for tokens",
            service="airtable",
            org_id=org_id,
            user_id=user_id,
            log_event="oauth_token_exchange_start",
        )

        token_start = time.time()

        # Exchange code for tokens (Airtable uses HTTP Basic Auth)
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        response = await asyncio.to_thread(
            requests.post,
            AIRTABLE_TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_header}",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
            timeout=30,
        )

        token_duration_ms = (time.time() - token_start) * 1000

        if response.status_code != 200:
            logger.error(
                "Token exchange failed",
                service="airtable",
                org_id=org_id,
                user_id=user_id,
                status_code=response.status_code,
                duration_ms=round(token_duration_ms, 2),
                log_event="oauth_token_exchange_error",
            )
            return build_oauth_error_redirect(
                service="airtable",
                error="token_exchange_failed",
                error_description="Token exchange with Airtable failed",
                org_id=org_id,
            )

        token_data = response.json()

        logger.info(
            "Token exchange successful",
            service="airtable",
            org_id=org_id,
            user_id=user_id,
            duration_ms=round(token_duration_ms, 2),
            has_refresh_token=bool(token_data.get("refresh_token")),
            log_event="oauth_token_exchange_success",
        )

        # Validate required token field
        access_token = token_data.get("access_token")
        if not access_token:
            logger.error(
                "Missing access_token in Airtable response",
                service="airtable",
                org_id=org_id,
                user_id=user_id,
                log_event="oauth_token_missing_field",
            )
            return build_oauth_error_redirect(
                service="airtable",
                error="invalid_token_response",
                error_description="Missing access token in Airtable response",
                org_id=org_id,
            )

        # Store credentials (tokens expire in 60 days)
        expires_in = token_data.get("expires_in", 5184000)
        await asyncio.to_thread(
            CredentialManager.store_credential,
            org_id=org_id,
            user_id=user_id,
            service="airtable",
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=expires_in),
            credential_type=credential_type,
        )

        logger.info(
            "OAuth flow completed successfully",
            service="airtable",
            org_id=org_id,
            user_id=user_id,
            log_event="oauth_callback_success",
        )
        return build_oauth_success_redirect(service="airtable", org_id=org_id)

    except HTTPException:
        return build_oauth_error_redirect(
            service="airtable",
            error="config_error",
            error_description="Service configuration error",
            org_id=org_id,
        )
    except Exception:
        logger.error(
            "OAuth callback failed",
            service="airtable",
            org_id=org_id,
            log_event="oauth_callback_error",
            exc_info=True,
        )
        return build_oauth_error_redirect(
            service="airtable",
            error="callback_failed",
            error_description="An unexpected error occurred",
            org_id=org_id,
        )
