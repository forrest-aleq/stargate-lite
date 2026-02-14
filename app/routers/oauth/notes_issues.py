"""
Notes and Issue Tracking OAuth Routes

Handles OAuth authorization and callback for:
- Notion (workspace/docs)
- Linear (issue tracking)
"""

import asyncio
import base64
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


# ===== Notion OAuth =====


@router.get("/oauth/notion/authorize")
async def notion_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    """
    Initiate Notion OAuth 2.0 flow

    Note: Notion's authorization URL is unique per integration
    Must be configured in Notion integration settings
    """
    client_id = os.getenv("NOTION_CLIENT_ID")
    redirect_uri = os.getenv("NOTION_REDIRECT_URI", "http://localhost:8001/oauth/notion/callback")

    if not client_id:
        raise HTTPException(status_code=500, detail="Notion OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Notion uses capabilities instead of traditional scopes
    # Authorization URL is provided in Notion integration settings
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "owner": "user",
        "state": state,
    }

    # Note: This URL may vary based on your Notion integration
    auth_url = f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/notion/callback")
async def notion_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Notion OAuth callback"""
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, credential_type, source = parse_oauth_state_4parts(
                state, "notion"
            )
        else:
            org_id, user_id, credential_type = parse_oauth_state_3parts(state, "notion")

        client_id = os.getenv("NOTION_CLIENT_ID")
        client_secret = os.getenv("NOTION_CLIENT_SECRET")
        redirect_uri = os.getenv(
            "NOTION_REDIRECT_URI", "http://localhost:8001/oauth/notion/callback"
        )

        token_url = "https://api.notion.com/v1/oauth/token"

        # Notion requires Basic Auth (base64 encoded client_id:client_secret)
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        response = await asyncio.to_thread(
            requests.post,
            token_url,
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
            },
            json={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            timeout=30,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

        token_data = response.json()

        await asyncio.to_thread(
            CredentialManager.store_credential,
            org_id=org_id,
            user_id=user_id,
            service="notion",
            access_token=token_data["access_token"],
            refresh_token=None,
            token_expiry=datetime.now(UTC) + timedelta(days=36500),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="notion", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="notion", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="notion", error="callback_failed", error_description=str(e)[:200]
        )


# ===== Linear OAuth =====


@router.get("/oauth/linear/authorize")
async def linear_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "agent", source: str = ""
) -> RedirectResponse:
    """
    Initiate Linear OAuth flow with agent mode (actor=app)

    Creates a dedicated agent user in Linear workspace
    Agent can be assigned issues and @mentioned
    """
    client_id = os.getenv("LINEAR_CLIENT_ID")
    redirect_uri = os.getenv("LINEAR_REDIRECT_URI", "http://localhost:8001/oauth/linear/callback")

    if not client_id:
        raise HTTPException(status_code=500, detail="Linear OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    # Agent-optimized scopes for Linear
    # read,write - Basic permissions
    # issues:create - Create issues
    # comments:create - Comment on issues
    # app:assignable - Agent can be assigned issues
    # app:mentionable - Agent can be @mentioned
    scopes = "read,write,issues:create,comments:create,app:assignable,app:mentionable"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "actor": "app",  # CRITICAL: Creates agent user instead of user OAuth
    }

    auth_url = f"https://linear.app/oauth/authorize?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/linear/callback")
async def linear_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Linear OAuth callback

    Exchange authorization code for access/refresh tokens
    Linear tokens expire after 24 hours, refresh tokens auto-enabled (Oct 2025+)
    """
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, credential_type, source = parse_oauth_state_4parts(
                state, "linear"
            )
        else:
            org_id, user_id, credential_type = parse_oauth_state_3parts(state, "linear")

        client_id = os.getenv("LINEAR_CLIENT_ID")
        client_secret = os.getenv("LINEAR_CLIENT_SECRET")
        redirect_uri = os.getenv(
            "LINEAR_REDIRECT_URI", "http://localhost:8001/oauth/linear/callback"
        )

        token_url = "https://api.linear.app/oauth/token"

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
            service="linear",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(service="linear", org_id=org_id, extra_params=extra)

    except HTTPException:
        return build_oauth_error_redirect(service="linear", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="linear", error="callback_failed", error_description=str(e)[:200]
        )
