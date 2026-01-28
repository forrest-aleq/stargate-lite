"""
Notes and Issue Tracking OAuth Routes

Handles OAuth authorization and callback for:
- Notion (workspace/docs)
- Linear (issue tracking)
"""

import base64
import os
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.routers.oauth.base import build_signed_state_3parts, parse_oauth_state_3parts

router = APIRouter(tags=["oauth"])


# ===== Notion OAuth =====


@router.get("/oauth/notion/authorize")
async def notion_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
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
async def notion_oauth_callback(code: str, state: str) -> dict[str, Any]:
    """Handle Notion OAuth callback"""
    try:
        # Parse and verify signed state
        org_id, user_id, credential_type = parse_oauth_state_3parts(state, "notes_issues")

        client_id = os.getenv("NOTION_CLIENT_ID")
        client_secret = os.getenv("NOTION_CLIENT_SECRET")
        redirect_uri = os.getenv(
            "NOTION_REDIRECT_URI", "http://localhost:8001/oauth/notion/callback"
        )

        token_url = "https://api.notion.com/v1/oauth/token"

        # Notion requires Basic Auth (base64 encoded client_id:client_secret)
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        response = requests.post(
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

        # Notion tokens don't expire
        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="notion",
            access_token=token_data["access_token"],
            refresh_token=None,  # Notion tokens don't expire/refresh
            token_expiry=datetime.utcnow() + timedelta(days=36500),  # 100 years (doesn't expire)
        )

        return {
            "success": True,
            "message": "Notion OAuth completed successfully",
            "org_id": org_id,
            "user_id": user_id,
            "credential_type": credential_type,
            "workspace_name": token_data.get("workspace_name"),
            "workspace_id": token_data.get("workspace_id"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {e!s}") from e


# ===== Linear OAuth =====


@router.get("/oauth/linear/authorize")
async def linear_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "agent"
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
async def linear_oauth_callback(code: str, state: str) -> dict[str, Any]:
    """
    Handle Linear OAuth callback

    Exchange authorization code for access/refresh tokens
    Linear tokens expire after 24 hours, refresh tokens auto-enabled (Oct 2025+)
    """
    try:
        # Parse and verify signed state
        org_id, user_id, credential_type = parse_oauth_state_3parts(state, "notes_issues")

        client_id = os.getenv("LINEAR_CLIENT_ID")
        client_secret = os.getenv("LINEAR_CLIENT_SECRET")
        redirect_uri = os.getenv(
            "LINEAR_REDIRECT_URI", "http://localhost:8001/oauth/linear/callback"
        )

        token_url = "https://api.linear.app/oauth/token"

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
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

        token_data = response.json()

        # Linear access tokens expire after 24 hours
        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="linear",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.utcnow() + timedelta(seconds=token_data["expires_in"]),
        )

        return {
            "success": True,
            "message": "Linear OAuth completed successfully - Agent user created",
            "org_id": org_id,
            "user_id": user_id,
            "credential_type": credential_type,
            "agent_mode": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {e!s}") from e
