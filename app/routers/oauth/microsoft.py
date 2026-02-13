"""
Microsoft OAuth Routes

Handles OAuth authorization and callback for Microsoft 365 (Excel, OneDrive, Outlook, Power BI).
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.routers.oauth.base import build_signed_state_4parts, parse_oauth_state_4parts

router = APIRouter(tags=["oauth"])


@router.get("/oauth/microsoft/authorize")
async def microsoft_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", service: str = "excel"
) -> RedirectResponse:
    """
    Initiate Microsoft 365 OAuth flow

    Redirects user to Microsoft authorization page
    Supports: Excel, OneDrive, Outlook Calendar, Power BI

    Args:
        service: excel, onedrive, outlook, powerbi (determines scopes)
        credential_type: "customer" or "agent"
    """
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
    tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")

    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="Microsoft OAuth not configured")

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_4parts(org_id, user_id, credential_type, service)

    # Service-specific scopes
    scope_map = {
        "excel": "Files.ReadWrite.All offline_access",
        "onedrive": "Files.ReadWrite.All offline_access",
        "outlook": "Calendars.ReadWrite Mail.ReadWrite offline_access",
        "powerbi": (
            "https://analysis.windows.net/powerbi/api/Dataset.ReadWrite.All "
            "https://analysis.windows.net/powerbi/api/Report.ReadWrite.All "
            "offline_access"
        ),
        "all": "Files.ReadWrite.All Calendars.ReadWrite Mail.ReadWrite offline_access",
    }

    scopes = scope_map.get(service, scope_map["all"])

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "response_mode": "query",
    }

    auth_url = (
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?{urlencode(params)}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/oauth/microsoft/callback")
async def microsoft_oauth_callback(code: str, state: str) -> dict[str, Any]:
    """
    Handle Microsoft 365 OAuth callback

    Exchange authorization code for access/refresh tokens and store them
    State format: {org_id}:{user_id}:{credential_type}:{service}
    """
    try:
        # Parse and verify signed state
        org_id, user_id, credential_type, service = parse_oauth_state_4parts(state, "microsoft")

        # Exchange code for tokens
        client_id = os.getenv("MICROSOFT_CLIENT_ID")
        client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
        tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

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

        # Store credentials (Microsoft tokens typically expire after 1 hour)
        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="microsoft",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        return {
            "success": True,
            "message": f"Microsoft {service} OAuth completed successfully",
            "org_id": org_id,
            "user_id": user_id,
            "credential_type": credential_type,
            "service": service,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {e!s}") from e


# Power BI uses Microsoft OAuth (same endpoints, different scopes)
@router.get("/oauth/powerbi/authorize")
async def powerbi_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """Redirect to Microsoft OAuth with Power BI scopes"""
    return await microsoft_oauth_authorize(org_id, user_id, credential_type, service="powerbi")


@router.get("/oauth/powerbi/callback")
async def powerbi_oauth_callback(code: str, state: str) -> dict[str, Any]:
    """Handle Power BI OAuth callback (uses Microsoft OAuth)"""
    return await microsoft_oauth_callback(code, state)
