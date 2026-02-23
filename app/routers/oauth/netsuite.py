"""
NetSuite OAuth Routes

Handles OAuth authorization and callback for NetSuite ERP.
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.routers.oauth.base import (
    build_oauth_error_redirect,
    build_oauth_success_redirect,
    build_signed_state_3parts,
    build_signed_state_4parts,
    parse_oauth_state_3parts,
    parse_oauth_state_4parts,
)

router = APIRouter(tags=["oauth"])


@router.get("/oauth/netsuite/authorize")
async def netsuite_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """
    Initiate NetSuite OAuth 2.0 flow

    Redirects user to NetSuite authorization page
    Requires NETSUITE_ACCOUNT_ID in environment
    """
    account_id = os.getenv("NETSUITE_ACCOUNT_ID")
    redirect_uri = os.getenv(
        "NETSUITE_REDIRECT_URI", "http://localhost:8001/oauth/netsuite/callback"
    )
    client_id = os.getenv("NETSUITE_CONSUMER_KEY")  # Consumer key is client_id for OAuth 2.0

    if not account_id or not client_id:
        raise HTTPException(
            status_code=500,
            detail=(
                "NetSuite OAuth not configured (need NETSUITE_ACCOUNT_ID and NETSUITE_CONSUMER_KEY)"
            ),
        )

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # NetSuite OAuth 2.0 scopes (REST API access)
    scope = "restlets rest_webservices"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
    }

    # NetSuite auth URL includes account ID
    auth_url = (
        f"https://{account_id}.app.netsuite.com/app/login/oauth2/authorize.nl?{urlencode(params)}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/oauth/netsuite/callback")
async def netsuite_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle NetSuite OAuth callback

    Exchange authorization code for access/refresh tokens and store them.
    State is cryptographically signed to prevent CSRF/tampering.
    """
    source = ""
    try:
        # Parse and verify signed state (3-part or 4-part with source)
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, _credential_type, source = parse_oauth_state_4parts(state, "netsuite")
        else:
            org_id, user_id, _credential_type = parse_oauth_state_3parts(state, "netsuite")

        # Exchange code for tokens
        account_id = os.getenv("NETSUITE_ACCOUNT_ID")
        client_id = os.getenv("NETSUITE_CONSUMER_KEY")
        client_secret = os.getenv("NETSUITE_CONSUMER_SECRET")
        redirect_uri = os.getenv(
            "NETSUITE_REDIRECT_URI", "http://localhost:8001/oauth/netsuite/callback"
        )

        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="NetSuite OAuth not configured")

        # NetSuite token endpoint
        token_url = (
            f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"
        )

        response = await asyncio.to_thread(
            requests.post,
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(client_id, client_secret),  # HTTP Basic Auth
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            timeout=30,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

        token_data = response.json()

        # Store credentials (NetSuite refresh tokens expire after 7 days)
        await asyncio.to_thread(
            CredentialManager.store_credential,
            org_id=org_id,
            user_id=user_id,
            service="netsuite",
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(
            service="netsuite", org_id=org_id, extra_params=extra, user_id=user_id
        )

    except HTTPException:
        return build_oauth_error_redirect(
            service="netsuite",
            error="callback_failed",
            error_description="OAuth callback failed",
        )
    except Exception as e:
        return build_oauth_error_redirect(
            service="netsuite",
            error="callback_failed",
            error_description=str(e)[:200],
        )
