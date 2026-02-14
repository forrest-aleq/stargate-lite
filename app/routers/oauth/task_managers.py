"""
Task Manager OAuth Routes

Handles OAuth authorization and callback for task management tools:
- Asana (project management)
- ClickUp (task management)
- Monday.com (work OS)
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from typing import Any
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


# ===== Asana OAuth =====


@router.get("/oauth/asana/authorize")
async def asana_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """
    Initiate Asana OAuth 2.0 flow

    Redirects user to Asana authorization page
    """
    client_id = os.getenv("ASANA_CLIENT_ID")
    redirect_uri = os.getenv("ASANA_REDIRECT_URI", "http://localhost:8001/oauth/asana/callback")

    if not client_id:
        raise HTTPException(status_code=500, detail="Asana OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Asana scopes (space-separated)
    # Full permissions, or use specific scopes like
    # "tasks:read tasks:write projects:read projects:write"
    scope = "default"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        "scope": scope,
    }

    auth_url = f"https://app.asana.com/-/oauth_authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/asana/callback")
async def asana_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Asana OAuth callback"""
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, credential_type, source = parse_oauth_state_4parts(state, "asana")
        else:
            org_id, user_id, credential_type = parse_oauth_state_3parts(state, "asana")

        client_id = os.getenv("ASANA_CLIENT_ID")
        client_secret = os.getenv("ASANA_CLIENT_SECRET")
        redirect_uri = os.getenv("ASANA_REDIRECT_URI", "http://localhost:8001/oauth/asana/callback")

        token_url = "https://app.asana.com/-/oauth_token"

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
            service="asana",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="asana", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="asana", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="asana", error="callback_failed", error_description=str(e)[:200]
        )


# ===== ClickUp OAuth =====


@router.get("/oauth/clickup/authorize")
async def clickup_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """
    Initiate ClickUp OAuth 2.0 flow

    ClickUp is used by finance teams for process management and workflows
    """
    client_id = os.getenv("CLICKUP_CLIENT_ID")
    redirect_uri = os.getenv("CLICKUP_REDIRECT_URI", "http://localhost:8001/oauth/clickup/callback")

    if not client_id:
        raise HTTPException(status_code=500, detail="ClickUp OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Build authorization URL
    # Note: ClickUp uses a simple OAuth flow without explicit scopes
    params = {"client_id": client_id, "redirect_uri": redirect_uri, "state": state}

    auth_url = f"https://app.clickup.com/api?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/clickup/callback")
async def clickup_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle ClickUp OAuth callback

    Exchange authorization code for access token
    Note: Current ClickUp tokens do not expire (subject to change)
    """
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, credential_type, source = parse_oauth_state_4parts(
                state, "clickup"
            )
        else:
            org_id, user_id, credential_type = parse_oauth_state_3parts(state, "clickup")

        client_id = os.getenv("CLICKUP_CLIENT_ID")
        client_secret = os.getenv("CLICKUP_CLIENT_SECRET")

        token_url = "https://api.clickup.com/api/v2/oauth/token"

        response = await asyncio.to_thread(
            requests.post,
            token_url,
            data={"client_id": client_id, "client_secret": client_secret, "code": code},
            timeout=30,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

        token_data = response.json()

        await asyncio.to_thread(
            CredentialManager.store_credential,
            org_id=org_id,
            user_id=user_id,
            service="clickup",
            access_token=token_data["access_token"],
            refresh_token=None,
            token_expiry=None,
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="clickup", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="clickup", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="clickup", error="callback_failed", error_description=str(e)[:200]
        )


# ===== Monday.com OAuth =====


@router.get("/oauth/monday/authorize")
async def monday_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """
    Initiate Monday.com OAuth 2.0 flow

    Monday.com is used by finance/operations teams for task management
    """
    client_id = os.getenv("MONDAY_CLIENT_ID")
    redirect_uri = os.getenv("MONDAY_REDIRECT_URI", "http://localhost:8001/oauth/monday/callback")

    if not client_id:
        raise HTTPException(status_code=500, detail="Monday.com OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Monday.com OAuth scopes:
    # boards:read - Read board data
    # boards:write - Create/update items
    # users:read - Get user information
    # Note: Monday.com doesn't require explicit scope parameter in authorize URL

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
    }

    auth_url = f"https://auth.monday.com/oauth2/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/monday/callback")
async def monday_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Monday.com OAuth callback

    Exchange authorization code for access token
    Monday.com tokens don't expire
    """
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, credential_type, source = parse_oauth_state_4parts(
                state, "monday"
            )
        else:
            org_id, user_id, credential_type = parse_oauth_state_3parts(state, "monday")

        client_id = os.getenv("MONDAY_CLIENT_ID")
        client_secret = os.getenv("MONDAY_CLIENT_SECRET")
        redirect_uri = os.getenv(
            "MONDAY_REDIRECT_URI", "http://localhost:8001/oauth/monday/callback"
        )

        token_url = "https://auth.monday.com/oauth2/token"

        response = await asyncio.to_thread(
            requests.post,
            token_url,
            json={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
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
            service="monday",
            access_token=token_data["access_token"],
            refresh_token=None,
            token_expiry=None,
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="monday", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="monday", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="monday", error="callback_failed", error_description=str(e)[:200]
        )
