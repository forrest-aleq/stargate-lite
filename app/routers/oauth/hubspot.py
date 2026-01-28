"""
HubSpot OAuth Routes

Handles OAuth authorization and callback for HubSpot CRM.
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
    parse_oauth_state_3parts,
)

logger = get_logger(__name__)
router = APIRouter(tags=["oauth"])


@router.get("/oauth/hubspot/authorize")
async def hubspot_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate HubSpot OAuth flow

    Redirects user to HubSpot authorization page
    """
    client_id = os.getenv("HUBSPOT_CLIENT_ID")
    redirect_uri = os.getenv("HUBSPOT_REDIRECT_URI")

    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="HubSpot OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_3parts(org_id, user_id, credential_type)

    # HubSpot OAuth scopes for CRM access
    scopes = (
        "crm.objects.contacts.read crm.objects.contacts.write "
        "crm.objects.deals.read crm.objects.deals.write "
        "crm.objects.companies.read crm.objects.companies.write"
    )

    params = {"client_id": client_id, "redirect_uri": redirect_uri, "scope": scopes, "state": state}

    auth_url = f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/hubspot/callback")
async def hubspot_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle HubSpot OAuth callback

    Exchange authorization code for access/refresh tokens and store them.
    State format: {org_id}:{user_id}:{credential_type}
    Redirects to N3 frontend on completion.
    """
    # Parse and verify signed state
    try:
        org_id, user_id, credential_type = parse_oauth_state_3parts(state, "hubspot")
    except Exception:
        return build_oauth_error_redirect(
            service="hubspot",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        # Exchange code for tokens
        client_id = os.getenv("HUBSPOT_CLIENT_ID")
        client_secret = os.getenv("HUBSPOT_CLIENT_SECRET")
        redirect_uri = os.getenv("HUBSPOT_REDIRECT_URI")

        token_url = "https://api.hubapi.com/oauth/v1/token"

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
            logger.error("HubSpot token exchange failed", status_code=response.status_code)
            return build_oauth_error_redirect(
                service="hubspot",
                error="token_exchange_failed",
                error_description="Token exchange with HubSpot failed",
                org_id=org_id,
            )

        token_data = response.json()

        # Store credentials (HubSpot tokens expire after 30 minutes)
        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="hubspot",
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_expiry=datetime.utcnow() + timedelta(seconds=token_data["expires_in"]),
        )

        return build_oauth_success_redirect(service="hubspot", org_id=org_id)

    except Exception as e:
        logger.error("HubSpot OAuth callback failed", error=str(e), exc_info=True)
        return build_oauth_error_redirect(
            service="hubspot",
            error="callback_failed",
            error_description=str(e),
            org_id=org_id,
        )
