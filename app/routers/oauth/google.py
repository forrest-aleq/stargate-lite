"""
Google OAuth Routes

Handles OAuth authorization and callback for Google Workspace (Gmail, Drive, Calendar, Sheets).
"""

import os
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager

router = APIRouter(tags=["oauth"])


@router.get("/oauth/google/authorize")
async def google_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", service: str = "gmail"
) -> RedirectResponse:
    """
    Initiate Google Workspace OAuth flow

    Redirects user to Google authorization page

    Args:
        service: gmail, drive, calendar, sheets (determines scopes)
        credential_type: "customer" or "agent"
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    # State encodes org_id:user_id:credential_type:service
    state = f"{org_id}:{user_id}:{credential_type}:{service}"

    # Service-specific scopes
    scope_map = {
        "gmail": (
            "https://www.googleapis.com/auth/gmail.send "
            "https://www.googleapis.com/auth/gmail.readonly "
            "https://www.googleapis.com/auth/gmail.modify"
        ),
        "drive": (
            "https://www.googleapis.com/auth/drive " "https://www.googleapis.com/auth/drive.file"
        ),
        "calendar": (
            "https://www.googleapis.com/auth/calendar "
            "https://www.googleapis.com/auth/calendar.events"
        ),
        "sheets": (
            "https://www.googleapis.com/auth/spreadsheets "
            "https://www.googleapis.com/auth/drive.file"
        ),
        "all": (
            "https://www.googleapis.com/auth/gmail.send "
            "https://www.googleapis.com/auth/gmail.readonly "
            "https://www.googleapis.com/auth/drive "
            "https://www.googleapis.com/auth/calendar "
            "https://www.googleapis.com/auth/spreadsheets"
        ),
    }

    scopes = scope_map.get(service, scope_map["all"])

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "access_type": "offline",  # Get refresh token
        "prompt": "consent",  # Force consent to get refresh token
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/oauth/google/callback")
async def google_oauth_callback(code: str, state: str) -> dict[str, Any]:
    """
    Handle Google OAuth callback

    Exchange authorization code for access/refresh tokens and store them
    State format: {org_id}:{user_id}:{credential_type}:{service}
    """
    try:
        # Parse state
        parts = state.split(":")
        if len(parts) != 4:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        org_id, user_id, credential_type, service = parts

        # Validate no empty values
        if not org_id or not user_id or not credential_type or not service:
            raise HTTPException(status_code=400, detail="Invalid state parameter: empty values")

        # Exchange code for tokens
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        if not client_id or not client_secret or not redirect_uri:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")

        token_url = "https://oauth2.googleapis.com/token"

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
            # Log the error details but don't expose them to the client
            raise HTTPException(status_code=500, detail="Token exchange with Google failed")

        token_data = response.json()

        # Store credentials (Google tokens typically expire after 1 hour)
        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="google",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),  # May not be present on re-auth
            token_expiry=datetime.utcnow() + timedelta(seconds=token_data["expires_in"]),
        )

        return {
            "success": True,
            "message": f"Google {service} OAuth completed successfully",
            "org_id": org_id,
            "user_id": user_id,
            "credential_type": credential_type,
            "service": service,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {e!s}") from e
