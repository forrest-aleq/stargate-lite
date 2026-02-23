"""
Microsoft OAuth Routes

Handles OAuth authorization and callback for Microsoft 365 (Excel, OneDrive, Outlook, Power BI).
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
    build_signed_state_4parts,
    build_signed_state_5parts,
    parse_oauth_state_4parts,
    parse_oauth_state_5parts,
)

router = APIRouter(tags=["oauth"])


@router.get("/oauth/microsoft/authorize")
async def microsoft_oauth_authorize(
    org_id: str,
    user_id: str,
    credential_type: str = "customer",
    service: str = "excel",
    source: str = "",
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
    # Microsoft uses 4-part for sub_service; with source, use 5-part
    if source:
        state = build_signed_state_5parts(org_id, user_id, credential_type, service, source)
    else:
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
async def microsoft_oauth_callback(code: str, state: str) -> RedirectResponse:
    """
    Handle Microsoft 365 OAuth callback

    Exchange authorization code for access/refresh tokens and store them.
    State format: 4-part (org:user:cred_type:service) or 5-part (...:source).
    """
    source = ""
    try:
        # Parse state: 6 segments = 5-part with source, 5 segments = 4-part legacy
        parts = state.split(":")
        if len(parts) == 6:
            org_id, user_id, _credential_type, _service, source = parse_oauth_state_5parts(
                state, "microsoft"
            )
        else:
            org_id, user_id, _credential_type, _service = parse_oauth_state_4parts(
                state, "microsoft"
            )

        # Exchange code for tokens
        client_id = os.getenv("MICROSOFT_CLIENT_ID")
        client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
        tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

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
            service="microsoft",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=datetime.now(UTC) + timedelta(seconds=token_data["expires_in"]),
        )

        extra = {"source": source} if source else None
        return build_oauth_success_redirect(
            service="microsoft", org_id=org_id, extra_params=extra, user_id=user_id
        )

    except HTTPException:
        return build_oauth_error_redirect(service="microsoft", error="callback_failed")
    except Exception as e:
        return build_oauth_error_redirect(
            service="microsoft", error="callback_failed", error_description=str(e)[:200]
        )


# Power BI uses Microsoft OAuth (same endpoints, different scopes)
@router.get("/oauth/powerbi/authorize")
async def powerbi_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """Redirect to Microsoft OAuth with Power BI scopes"""
    return await microsoft_oauth_authorize(org_id, user_id, credential_type, service="powerbi")


@router.get("/oauth/powerbi/callback")
async def powerbi_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Power BI OAuth callback (uses Microsoft OAuth)"""
    return await microsoft_oauth_callback(code, state)
