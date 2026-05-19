"""
Zoho Books OAuth routes.

Implements OAuth authorization and callback handling for Zoho Books, including:
- Signed OAuth state handling
- Region-aware accounts server support
- Access/refresh token storage
- Organization discovery (organization_id) for downstream API calls
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlparse

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.connectors.zoho_books import get_recommended_scopes
from app.database import CredentialManager
from app.logging_config import get_logger
from app.routers.oauth.base import (
    build_oauth_error_redirect,
    build_oauth_success_redirect,
    build_signed_state_3parts,
    build_signed_state_4parts,
    get_env_or_raise,
    parse_oauth_state_3parts,
    parse_oauth_state_4parts,
)

logger = get_logger(__name__)
router = APIRouter(tags=["oauth"])

DEFAULT_ACCOUNTS_SERVER = "https://accounts.zoho.com"

# Map Zoho callback location param to accounts server
LOCATION_TO_ACCOUNTS_SERVER = {
    "us": "https://accounts.zoho.com",
    "eu": "https://accounts.zoho.eu",
    "in": "https://accounts.zoho.in",
    "au": "https://accounts.zoho.com.au",
    "jp": "https://accounts.zoho.jp",
    "ca": "https://accounts.zohocloud.ca",
    "sa": "https://accounts.zoho.sa",
    "ae": "https://accounts.zoho.ae",
    "uk": "https://accounts.zoho.uk",
}


def _normalize_accounts_server(value: str | None) -> str:
    server = (value or "").strip()
    if not server:
        return DEFAULT_ACCOUNTS_SERVER
    if not server.startswith(("http://", "https://")):
        server = f"https://{server}"
    return server.rstrip("/")


def _derive_accounts_server_from_api_domain(api_domain: str | None) -> str:
    if not api_domain:
        return DEFAULT_ACCOUNTS_SERVER
    parsed = urlparse(api_domain)
    host = (parsed.netloc or parsed.path).lower().strip()
    if host.startswith("www."):
        host = host[4:]
    if not host.startswith("zohoapis."):
        return DEFAULT_ACCOUNTS_SERVER
    suffix = host[len("zohoapis.") :]
    if not suffix:
        return DEFAULT_ACCOUNTS_SERVER
    return f"https://accounts.zoho.{suffix}"


def _resolve_accounts_server(location: str | None) -> str:
    configured = _normalize_accounts_server(os.getenv("ZOHO_BOOKS_ACCOUNTS_SERVER"))
    if configured != DEFAULT_ACCOUNTS_SERVER:
        return configured
    if location:
        mapped = LOCATION_TO_ACCOUNTS_SERVER.get(location.lower().strip())
        if mapped:
            return mapped
    return configured


def _exchange_zoho_tokens(
    code: str, org_id: str, user_id: str, accounts_server: str
) -> tuple[dict[str, Any], datetime]:
    client_id = get_env_or_raise("ZOHO_BOOKS_CLIENT_ID", "Zoho Books")
    client_secret = get_env_or_raise("ZOHO_BOOKS_CLIENT_SECRET", "Zoho Books")
    redirect_uri = get_env_or_raise("ZOHO_BOOKS_REDIRECT_URI", "Zoho Books")

    token_url = f"{accounts_server}/oauth/v2/token"
    logger.info(
        "Exchanging code for Zoho Books tokens",
        service="zoho_books",
        org_id=org_id,
        user_id=user_id,
        token_url=token_url,
        log_event="oauth_token_exchange_start",
    )

    token_start = time.time()
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
    duration_ms = (time.time() - token_start) * 1000

    if response.status_code != 200:
        logger.error(
            "Zoho Books token exchange failed",
            service="zoho_books",
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            response_body=response.text,
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

    token_data = response.json()
    token_expiry = datetime.now(UTC) + timedelta(seconds=int(token_data.get("expires_in", 3600)))
    return token_data, token_expiry


def _fetch_primary_organization(access_token: str, api_domain: str) -> dict[str, str | None]:
    organizations_url = f"{api_domain.rstrip('/')}/books/v3/organizations"
    response = requests.get(
        organizations_url,
        headers={
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Accept": "application/json",
        },
        timeout=20,
    )
    if response.status_code != 200:
        logger.warning(
            "Failed to fetch Zoho Books organizations",
            service="zoho_books",
            status_code=response.status_code,
            log_event="zoho_books_org_lookup_failed",
        )
        return {"organization_id": None, "organization_name": None}

    payload = response.json()
    organizations = payload.get("organizations", [])
    if not isinstance(organizations, list) or not organizations:
        return {"organization_id": None, "organization_name": None}

    selected = None
    for organization in organizations:
        if not isinstance(organization, dict):
            continue
        if organization.get("is_default_org") or organization.get("is_default_organization"):
            selected = organization
            break
    if selected is None:
        selected = organizations[0] if isinstance(organizations[0], dict) else {}

    return {
        "organization_id": str(selected.get("organization_id") or "") or None,
        "organization_name": str(selected.get("name") or "") or None,
    }


def _store_zoho_books_credential(
    org_id: str,
    user_id: str,
    credential_type: str,
    token_data: dict[str, Any],
    token_expiry: datetime,
    accounts_server: str,
    location: str,
) -> None:
    api_domain = str(token_data.get("api_domain") or "https://www.zohoapis.com").rstrip("/")
    discovered = _fetch_primary_organization(token_data["access_token"], api_domain)
    organization_id = discovered["organization_id"]

    resolved_accounts_server = _normalize_accounts_server(
        token_data.get("accounts_server")
        or _derive_accounts_server_from_api_domain(api_domain)
        or accounts_server
    )

    extra_data = {
        "api_domain": api_domain,
        "accounts_server": resolved_accounts_server,
        "organization_id": organization_id,
        "organization_name": discovered["organization_name"],
        "location": location or None,
    }

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="zoho_books",
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=token_expiry,
        realm_id=organization_id,
        credential_type=credential_type,
        extra_data=extra_data,
    )


@router.get("/oauth/zoho_books/authorize")
async def zoho_books_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer", source: str = ""
) -> RedirectResponse:
    logger.info(
        "Zoho Books OAuth authorization initiated",
        service="zoho_books",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_authorize_start",
    )

    client_id = get_env_or_raise("ZOHO_BOOKS_CLIENT_ID", "Zoho Books")
    redirect_uri = get_env_or_raise("ZOHO_BOOKS_REDIRECT_URI", "Zoho Books")
    accounts_server = _normalize_accounts_server(os.getenv("ZOHO_BOOKS_ACCOUNTS_SERVER"))
    scopes = os.getenv("ZOHO_BOOKS_SCOPES", "").strip() or get_recommended_scopes()

    if not scopes:
        raise HTTPException(
            status_code=500,
            detail="Zoho Books OAuth scopes are not configured (ZOHO_BOOKS_SCOPES)",
        )

    if source:
        state = build_signed_state_4parts(org_id, user_id, credential_type, source)
    else:
        state = build_signed_state_3parts(org_id, user_id, credential_type)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes,
        "access_type": "offline",
        "state": state,
    }
    prompt = os.getenv("ZOHO_BOOKS_OAUTH_PROMPT", "").strip()
    if prompt:
        params["prompt"] = prompt

    auth_url = f"{accounts_server}/oauth/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/oauth/zoho_books/callback")
async def zoho_books_oauth_callback(
    code: str,
    state: str,
    location: str = "",
) -> RedirectResponse:
    logger.info(
        "Zoho Books OAuth callback received",
        service="zoho_books",
        log_event="oauth_callback_start",
    )

    org_id: str | None = None
    source = ""
    try:
        parts = state.split(":")
        if len(parts) == 5:
            org_id, user_id, credential_type, source = parse_oauth_state_4parts(state, "zoho_books")
        else:
            org_id, user_id, credential_type = parse_oauth_state_3parts(state, "zoho_books")
    except HTTPException:
        return build_oauth_error_redirect(
            service="zoho_books",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    accounts_server = _resolve_accounts_server(location)

    try:
        token_data, token_expiry = await asyncio.to_thread(
            _exchange_zoho_tokens, code, org_id, user_id, accounts_server
        )
        await asyncio.to_thread(
            _store_zoho_books_credential,
            org_id,
            user_id,
            credential_type,
            token_data,
            token_expiry,
            accounts_server,
            location,
        )

        extra_params = {"source": source} if source else None
        return build_oauth_success_redirect(
            service="zoho_books",
            org_id=org_id,
            extra_params=extra_params,
            user_id=user_id,
        )
    except HTTPException:
        return build_oauth_error_redirect(
            service="zoho_books",
            error="token_exchange_failed",
            error_description="Token exchange failed",
            org_id=org_id,
        )
    except Exception:
        logger.error(
            "Zoho Books OAuth callback failed",
            service="zoho_books",
            log_event="oauth_callback_error",
            exc_info=True,
        )
        return build_oauth_error_redirect(
            service="zoho_books",
            error="callback_failed",
            error_description="An unexpected error occurred",
            org_id=org_id,
        )
