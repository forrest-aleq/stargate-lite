"""
E-Signature OAuth Routes.

Handles OAuth authorization and callback for:
- DocuSign (e-signatures, envelopes, templates)

DocuSign OAuth Documentation:
https://developers.docusign.com/platform/auth/authcode/
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
    build_signed_state_3parts,
    get_env_or_raise,
    parse_oauth_state_3parts,
)

logger = get_logger(__name__)

router = APIRouter(tags=["oauth"])

# DocuSign OAuth endpoints
# Production: account.docusign.com
# Demo/Development: account-d.docusign.com
DOCUSIGN_AUTH_URL = "https://account.docusign.com/oauth/auth"
DOCUSIGN_TOKEN_URL = "https://account.docusign.com/oauth/token"
DOCUSIGN_USERINFO_URL = "https://account.docusign.com/oauth/userinfo"
DOCUSIGN_DEMO_AUTH_URL = "https://account-d.docusign.com/oauth/auth"
DOCUSIGN_DEMO_TOKEN_URL = "https://account-d.docusign.com/oauth/token"
DOCUSIGN_DEMO_USERINFO_URL = "https://account-d.docusign.com/oauth/userinfo"


def _get_docusign_urls() -> tuple[str, str, str]:
    """Get DocuSign OAuth URLs based on environment."""
    use_demo = os.getenv("DOCUSIGN_USE_DEMO", "false").lower() == "true"
    if use_demo:
        return DOCUSIGN_DEMO_AUTH_URL, DOCUSIGN_DEMO_TOKEN_URL, DOCUSIGN_DEMO_USERINFO_URL
    return DOCUSIGN_AUTH_URL, DOCUSIGN_TOKEN_URL, DOCUSIGN_USERINFO_URL


def _fetch_docusign_account_info(
    access_token: str, userinfo_url: str
) -> tuple[str | None, str | None]:
    """Fetch DocuSign account ID and base URI from userinfo endpoint."""
    response = requests.get(
        userinfo_url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if response.status_code != 200:
        return None, None

    userinfo = response.json()
    accounts = userinfo.get("accounts", [])
    if not accounts:
        return None, None

    # Prefer the default account, otherwise use first
    default_account = next((a for a in accounts if a.get("is_default")), accounts[0])
    return default_account.get("account_id"), default_account.get("base_uri")


@router.get("/oauth/docusign/authorize")
async def docusign_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate DocuSign OAuth flow.

    Redirects user to DocuSign authorization page to grant access to
    e-signature capabilities including sending, signing, and managing envelopes.

    Args:
        org_id: Organization identifier
        user_id: User identifier
        credential_type: Type of credential (customer/agent)

    Returns:
        Redirect to DocuSign authorization page
    """
    client_id = get_env_or_raise("DOCUSIGN_INTEGRATION_KEY", "DocuSign")
    redirect_uri = get_env_or_raise("DOCUSIGN_REDIRECT_URI", "DocuSign")

    auth_url, _, _ = _get_docusign_urls()

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_3parts(org_id, user_id, credential_type)

    # DocuSign OAuth scopes for eSignature API
    # https://developers.docusign.com/platform/auth/reference/scopes/
    scopes = " ".join(
        [
            "signature",  # eSignature REST API access
            "extended",  # Extended scope for additional features
            "impersonation",  # Required for sending on behalf of users
        ]
    )

    params = {
        "response_type": "code",
        "scope": scopes,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }

    authorization_url = f"{auth_url}?{urlencode(params)}"

    logger.info(
        "Initiating DocuSign OAuth flow",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_docusign_authorize_start",
    )

    return RedirectResponse(url=authorization_url)


@router.get("/oauth/docusign/callback")
async def docusign_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle DocuSign OAuth callback. Redirects to N3 on completion."""
    try:
        org_id, user_id, _credential_type = parse_oauth_state_3parts(state, "docusign")
    except HTTPException:
        return build_oauth_error_redirect(
            service="docusign",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        client_id = get_env_or_raise("DOCUSIGN_INTEGRATION_KEY", "DocuSign")
        client_secret = get_env_or_raise("DOCUSIGN_SECRET_KEY", "DocuSign")
        redirect_uri = get_env_or_raise("DOCUSIGN_REDIRECT_URI", "DocuSign")

        _, token_url, userinfo_url = _get_docusign_urls()

        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(client_id, client_secret),
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            timeout=30,
        )

        if response.status_code != 200:
            logger.error("DocuSign token exchange failed", status_code=response.status_code)
            return build_oauth_error_redirect(
                service="docusign",
                error="token_exchange_failed",
                error_description="Token exchange with DocuSign failed",
                org_id=org_id,
            )

        token_data = response.json()
        access_token = token_data["access_token"]
        account_id, base_uri = _fetch_docusign_account_info(access_token, userinfo_url)

        expires_in = token_data.get("expires_in", 28800)
        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="docusign",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.utcnow() + timedelta(seconds=expires_in),
            extra_data={"account_id": account_id, "base_uri": base_uri},
        )

        logger.info("DocuSign OAuth completed", org_id=org_id)
        return build_oauth_success_redirect(service="docusign", org_id=org_id)

    except HTTPException as e:
        return build_oauth_error_redirect(
            service="docusign",
            error="config_error",
            error_description=str(e.detail),
            org_id=org_id,
        )
    except Exception as e:
        logger.error("DocuSign OAuth callback failed", error=str(e), exc_info=True)
        return build_oauth_error_redirect(
            service="docusign",
            error="callback_failed",
            error_description=str(e),
            org_id=org_id,
        )
