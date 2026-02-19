"""
Fintech OAuth Routes

Handles OAuth authorization and callback for financial services:
- Brex (corporate cards)
- Ramp (expense management)
- Chase (commercial banking)
- Schwab (brokerage)
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


# ===== Brex OAuth =====


@router.get("/oauth/brex/authorize")
async def brex_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """
    Initiate Brex OAuth 2.0 flow

    Redirects user to Brex authorization page
    Supports PKCE (optional but not required)
    """
    client_id = os.getenv("BREX_CLIENT_ID")
    redirect_uri = os.getenv("BREX_REDIRECT_URI", "http://localhost:8001/oauth/brex/callback")

    if not client_id:
        raise HTTPException(status_code=500, detail="Brex OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Brex scopes (must include offline_access for refresh token)
    scope = "cards:read cards:write transactions:read statements:read offline_access"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
    }

    auth_url = f"https://accounts.brex.com/oauth2/v1/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/brex/callback")
async def brex_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Brex OAuth callback"""
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, _credential_type, source = parse_oauth_state_4parts(state, "brex")
        else:
            org_id, user_id, _credential_type = parse_oauth_state_3parts(state, "brex")

        client_id = os.getenv("BREX_CLIENT_ID")
        client_secret = os.getenv("BREX_CLIENT_SECRET")
        redirect_uri = os.getenv("BREX_REDIRECT_URI", "http://localhost:8001/oauth/brex/callback")

        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="Brex OAuth not configured")

        token_url = "https://accounts.brex.com/oauth2/v1/token"

        response = await asyncio.to_thread(
            requests.post,
            token_url,
            auth=(client_id, client_secret),
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            timeout=30,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

        token_data = response.json()

        await asyncio.to_thread(
            CredentialManager.store_credential,
            org_id=org_id,
            user_id=user_id,
            service="brex",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="brex", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="brex", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="brex", error="callback_failed", error_description=str(e)[:200]
        )


# ===== Ramp OAuth =====


@router.get("/oauth/ramp/authorize")
async def ramp_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """Initiate Ramp OAuth 2.0 flow"""
    client_id = os.getenv("RAMP_CLIENT_ID")
    redirect_uri = os.getenv("RAMP_REDIRECT_URI", "http://localhost:8001/oauth/ramp/callback")

    if not client_id:
        raise HTTPException(status_code=500, detail="Ramp OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Ramp scopes — read-only across all resource types
    scope = (
        "accounting:read bank_accounts:read bills:read cards:read cashbacks:read "
        "departments:read entities:read item_receipts:read limits:read locations:read "
        "memos:read merchants:read offline_access purchase_orders:read "
        "receipt_integrations:read receipts:read reimbursements:read repayments:read "
        "spend_programs:read statements:read transactions:read transfers:read "
        "treasury:read users:read vendors:read"
    )

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
    }

    auth_url = f"https://app.ramp.com/v1/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/ramp/callback")
async def ramp_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Ramp OAuth callback"""
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, _credential_type, source = parse_oauth_state_4parts(state, "ramp")
        else:
            org_id, user_id, _credential_type = parse_oauth_state_3parts(state, "ramp")

        client_id = os.getenv("RAMP_CLIENT_ID")
        client_secret = os.getenv("RAMP_CLIENT_SECRET")
        redirect_uri = os.getenv("RAMP_REDIRECT_URI", "http://localhost:8001/oauth/ramp/callback")

        token_url = "https://api.ramp.com/developer/v1/token"

        response = await asyncio.to_thread(
            requests.post,
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
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

        token_data = response.json()

        await asyncio.to_thread(
            CredentialManager.store_credential,
            org_id=org_id,
            user_id=user_id,
            service="ramp",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="ramp", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="ramp", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="ramp", error="callback_failed", error_description=str(e)[:200]
        )


# ===== Chase OAuth =====


@router.get("/oauth/chase/authorize")
async def chase_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """Initiate Chase/J.P. Morgan OAuth 2.0 flow"""
    client_id = os.getenv("CHASE_CLIENT_ID")
    redirect_uri = os.getenv("CHASE_REDIRECT_URI", "http://localhost:8001/oauth/chase/callback")

    if not client_id:
        raise HTTPException(status_code=500, detail="Chase OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Chase commercial banking scopes
    scope = "accounts:read transactions:read payments:read"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
    }

    auth_url = f"https://developer.chase.com/oauth/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/chase/callback")
async def chase_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Chase OAuth callback"""
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, _credential_type, source = parse_oauth_state_4parts(state, "chase")
        else:
            org_id, user_id, _credential_type = parse_oauth_state_3parts(state, "chase")

        client_id = os.getenv("CHASE_CLIENT_ID")
        client_secret = os.getenv("CHASE_CLIENT_SECRET")
        redirect_uri = os.getenv("CHASE_REDIRECT_URI", "http://localhost:8001/oauth/chase/callback")

        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="Chase OAuth not configured")

        token_url = "https://api.chase.com/oauth/token"

        response = await asyncio.to_thread(
            requests.post,
            token_url,
            auth=(client_id, client_secret),
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            timeout=30,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

        token_data = response.json()

        await asyncio.to_thread(
            CredentialManager.store_credential,
            org_id=org_id,
            user_id=user_id,
            service="chase",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="chase", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="chase", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="chase", error="callback_failed", error_description=str(e)[:200]
        )


# ===== Schwab OAuth =====


@router.get("/oauth/schwab/authorize")
async def schwab_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """Initiate Charles Schwab OAuth 2.0 flow"""
    client_id = os.getenv("SCHWAB_CLIENT_ID")
    # Schwab recommends localhost for redirect
    redirect_uri = os.getenv("SCHWAB_REDIRECT_URI", "https://127.0.0.1")

    if not client_id:
        raise HTTPException(status_code=500, detail="Schwab OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    params = {"client_id": client_id, "redirect_uri": redirect_uri, "state": state}

    auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/schwab/callback")
async def schwab_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Schwab OAuth callback"""
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, _credential_type, source = parse_oauth_state_4parts(state, "schwab")
        else:
            org_id, user_id, _credential_type = parse_oauth_state_3parts(state, "schwab")

        client_id = os.getenv("SCHWAB_CLIENT_ID")
        client_secret = os.getenv("SCHWAB_CLIENT_SECRET")
        redirect_uri = os.getenv("SCHWAB_REDIRECT_URI", "https://127.0.0.1")

        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="Schwab OAuth not configured")

        token_url = "https://api.schwabapi.com/v1/oauth/token"

        response = await asyncio.to_thread(
            requests.post,
            token_url,
            auth=(client_id, client_secret),
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            timeout=30,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

        token_data = response.json()

        await asyncio.to_thread(
            CredentialManager.store_credential,
            org_id=org_id,
            user_id=user_id,
            service="schwab",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="schwab", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="schwab", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="schwab", error="callback_failed", error_description=str(e)[:200]
        )
