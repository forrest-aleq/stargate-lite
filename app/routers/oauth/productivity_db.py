"""
Productivity & Database OAuth Routes.

Handles OAuth authorization and callback for:
- Airtable (spreadsheet-database hybrid, bases, records)

Airtable OAuth Documentation:
https://airtable.com/developers/web/api/oauth-reference
https://airtable.com/developers/web/guides/oauth-integrations

Note: Airtable requires PKCE (Proof Key for Code Exchange) for OAuth.
"""

import base64
import hashlib
import secrets
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
    build_signed_state_3parts,
    get_env_or_raise,
    parse_oauth_state_3parts,
)

logger = get_logger(__name__)

router = APIRouter(tags=["oauth"])

# Airtable OAuth endpoints
AIRTABLE_AUTH_URL = "https://airtable.com/oauth2/v1/authorize"
AIRTABLE_TOKEN_URL = "https://airtable.com/oauth2/v1/token"

# In-memory PKCE verifier store
# In production, use Redis or database with TTL
# Key: state, Value: (code_verifier, timestamp)
_pkce_store: dict[str, tuple[str, float]] = {}
PKCE_TTL_SECONDS = 600  # 10 minutes


def _cleanup_expired_pkce() -> None:
    """Remove expired PKCE verifiers from the store."""
    now = time.time()
    expired = [k for k, (_, ts) in _pkce_store.items() if now - ts > PKCE_TTL_SECONDS]
    for k in expired:
        del _pkce_store[k]


def _generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code verifier and challenge (S256 method)."""
    code_verifier = secrets.token_urlsafe(32)
    sha256_hash = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def _get_pkce_verifier(state: str) -> str:
    """Retrieve and remove PKCE verifier for state, or raise HTTPException."""
    _cleanup_expired_pkce()
    if state not in _pkce_store:
        raise HTTPException(
            status_code=400, detail="PKCE verification failed: authorization expired"
        )
    code_verifier, _ = _pkce_store.pop(state)
    return code_verifier


@router.get("/oauth/airtable/authorize")
async def airtable_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate Airtable OAuth flow with PKCE.

    Airtable requires PKCE (Proof Key for Code Exchange) for security.
    Generates a code verifier/challenge pair and stores the verifier
    for use in the callback.

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

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Store code_verifier for callback
    # Clean up old entries first
    _cleanup_expired_pkce()
    _pkce_store[state] = (code_verifier, time.time())

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
async def airtable_oauth_callback(code: str, state: str) -> dict[str, Any]:
    """Handle Airtable OAuth callback with PKCE verification."""
    org_id, user_id, credential_type = parse_oauth_state_3parts(state, "airtable")
    code_verifier = _get_pkce_verifier(state)

    client_id = get_env_or_raise("AIRTABLE_CLIENT_ID", "Airtable")
    client_secret = get_env_or_raise("AIRTABLE_CLIENT_SECRET", "Airtable")
    redirect_uri = get_env_or_raise("AIRTABLE_REDIRECT_URI", "Airtable")

    # Exchange code for tokens (Airtable uses HTTP Basic Auth)
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
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

    if response.status_code != 200:
        logger.error("Airtable token exchange failed", status_code=response.status_code)
        raise HTTPException(status_code=500, detail="Token exchange failed")

    token_data = response.json()

    # Store credentials (tokens expire in 60 days)
    expires_in = token_data.get("expires_in", 5184000)
    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="airtable",
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=datetime.utcnow() + timedelta(seconds=expires_in),
    )

    logger.info("Airtable OAuth completed", org_id=org_id)
    return {
        "success": True,
        "message": "Airtable OAuth completed successfully",
        "org_id": org_id,
        "user_id": user_id,
        "credential_type": credential_type,
        "service": "airtable",
    }
