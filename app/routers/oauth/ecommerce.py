"""
E-commerce OAuth Routes.

Handles OAuth authorization and callback for:
- Shopify (store management, orders, products)
- Square (payments, orders, customers)

Shopify OAuth Documentation:
https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/authorization-code-grant

Square OAuth Documentation:
https://developer.squareup.com/docs/oauth-api/overview
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.logging_config import get_logger
from app.routers.oauth.base import get_env_or_raise, parse_oauth_state_3parts

logger = get_logger(__name__)

router = APIRouter(tags=["oauth"])


def _parse_shopify_state(state: str) -> tuple[str, str, str, str]:
    """Parse Shopify OAuth state with format org_id:user_id:credential_type:shop."""
    parts = state.split(":")
    if len(parts) != 4:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    org_id, user_id, credential_type, shop = parts
    if not all([org_id, user_id, credential_type, shop]):
        raise HTTPException(status_code=400, detail="Invalid state parameter: empty values")
    return org_id, user_id, credential_type, shop


def _validate_shopify_hmac(
    code: str, shop: str, state: str, timestamp: str, hmac_param: str, client_secret: str
) -> None:
    """Validate Shopify HMAC signature."""
    query_params = f"code={code}&shop={shop}&state={state}&timestamp={timestamp}"
    computed_hmac = hmac.new(
        client_secret.encode("utf-8"),
        query_params.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(computed_hmac, hmac_param):
        raise HTTPException(status_code=400, detail="Invalid HMAC signature")


# Square OAuth endpoints
# Production: connect.squareup.com
# Sandbox: connect.squareupsandbox.com
SQUARE_AUTH_URL = "https://connect.squareup.com/oauth2/authorize"
SQUARE_TOKEN_URL = "https://connect.squareup.com/oauth2/token"
SQUARE_SANDBOX_AUTH_URL = "https://connect.squareupsandbox.com/oauth2/authorize"
SQUARE_SANDBOX_TOKEN_URL = "https://connect.squareupsandbox.com/oauth2/token"


def _get_square_urls() -> tuple[str, str]:
    """Get Square OAuth URLs based on environment."""
    use_sandbox = os.getenv("SQUARE_USE_SANDBOX", "false").lower() == "true"
    if use_sandbox:
        return SQUARE_SANDBOX_AUTH_URL, SQUARE_SANDBOX_TOKEN_URL
    return SQUARE_AUTH_URL, SQUARE_TOKEN_URL


# =============================================================================
# Shopify OAuth
# =============================================================================


@router.get("/oauth/shopify/authorize")
async def shopify_oauth_authorize(
    org_id: str,
    user_id: str,
    shop: str,
    credential_type: str = "customer",
) -> RedirectResponse:
    """
    Initiate Shopify OAuth flow.

    Shopify requires the shop name to construct OAuth URLs.
    The shop parameter should be the myshopify.com subdomain (e.g., 'my-store').

    Args:
        org_id: Organization identifier
        user_id: User identifier
        shop: Shopify store name (e.g., 'my-store' for my-store.myshopify.com)
        credential_type: Type of credential (customer/agent)

    Returns:
        Redirect to Shopify authorization page
    """
    client_id = get_env_or_raise("SHOPIFY_CLIENT_ID", "Shopify")
    redirect_uri = get_env_or_raise("SHOPIFY_REDIRECT_URI", "Shopify")

    # Validate shop name format (alphanumeric and hyphens only)
    if not shop or not all(c.isalnum() or c == "-" for c in shop):
        raise HTTPException(status_code=400, detail="Invalid shop name format")

    # State encodes org_id:user_id:credential_type:shop for the callback
    # We include shop in state to verify it matches on callback
    state = f"{org_id}:{user_id}:{credential_type}:{shop}"

    # Shopify scopes for e-commerce access
    # https://shopify.dev/docs/api/usage/access-scopes
    scopes = ",".join(
        [
            "read_orders",
            "write_orders",
            "read_products",
            "write_products",
            "read_customers",
            "write_customers",
            "read_inventory",
            "write_inventory",
            "read_fulfillments",
            "write_fulfillments",
            "read_shipping",
            "write_shipping",
        ]
    )

    params = {
        "client_id": client_id,
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "state": state,
    }

    # Shopify OAuth URL includes shop subdomain
    authorization_url = f"https://{shop}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"

    logger.info(
        "Initiating Shopify OAuth flow",
        org_id=org_id,
        user_id=user_id,
        shop=shop,
        log_event="oauth_shopify_authorize_start",
    )

    return RedirectResponse(url=authorization_url)


@router.get("/oauth/shopify/callback")
async def shopify_oauth_callback(
    code: str,
    state: str,
    shop: str,
    hmac_param: str = Query(alias="hmac"),
    timestamp: str = "",
) -> dict[str, Any]:
    """Handle Shopify OAuth callback with HMAC validation."""
    org_id, user_id, credential_type, state_shop = _parse_shopify_state(state)

    # Normalize and verify shop name
    callback_shop = shop.replace(".myshopify.com", "")
    if callback_shop != state_shop:
        logger.warning("Shopify shop mismatch", expected=state_shop, received=callback_shop)
        raise HTTPException(status_code=400, detail="Shop mismatch in callback")

    client_id = get_env_or_raise("SHOPIFY_CLIENT_ID", "Shopify")
    client_secret = get_env_or_raise("SHOPIFY_CLIENT_SECRET", "Shopify")

    # Validate HMAC signature
    _validate_shopify_hmac(code, shop, state, timestamp, hmac_param, client_secret)

    # Exchange code for access token
    token_url = f"https://{callback_shop}.myshopify.com/admin/oauth/access_token"
    response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"client_id": client_id, "client_secret": client_secret, "code": code},
        timeout=30,
    )

    if response.status_code != 200:
        logger.error("Shopify token exchange failed", status_code=response.status_code)
        raise HTTPException(status_code=500, detail="Token exchange failed")

    token_data = response.json()

    # Store credentials (Shopify offline tokens don't expire - set 10 year expiry)
    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="shopify",
        access_token=token_data["access_token"],
        refresh_token=None,
        token_expiry=datetime.utcnow() + timedelta(days=3650),
        extra_data={"shop": callback_shop},
    )

    logger.info("Shopify OAuth completed", org_id=org_id, shop=callback_shop)
    return {
        "success": True,
        "message": "Shopify OAuth completed successfully",
        "org_id": org_id,
        "user_id": user_id,
        "credential_type": credential_type,
        "service": "shopify",
        "shop": callback_shop,
    }


# =============================================================================
# Square OAuth
# =============================================================================


@router.get("/oauth/square/authorize")
async def square_oauth_authorize(
    org_id: str, user_id: str, credential_type: str = "customer"
) -> RedirectResponse:
    """
    Initiate Square OAuth flow.

    Redirects user to Square authorization page to grant access to
    payments, orders, customers, and inventory data.

    Args:
        org_id: Organization identifier
        user_id: User identifier
        credential_type: Type of credential (customer/agent)

    Returns:
        Redirect to Square authorization page
    """
    client_id = get_env_or_raise("SQUARE_APPLICATION_ID", "Square")
    # Note: redirect_uri is configured in Square Developer Dashboard
    # and validated during token exchange, not during authorization

    auth_url, _ = _get_square_urls()

    # State encodes org_id:user_id:credential_type for the callback
    state = f"{org_id}:{user_id}:{credential_type}"

    # Square OAuth scopes
    # https://developer.squareup.com/docs/oauth-api/square-permissions
    scopes = " ".join(
        [
            "MERCHANT_PROFILE_READ",
            "PAYMENTS_READ",
            "PAYMENTS_WRITE",
            "ORDERS_READ",
            "ORDERS_WRITE",
            "CUSTOMERS_READ",
            "CUSTOMERS_WRITE",
            "INVOICES_READ",
            "INVOICES_WRITE",
            "INVENTORY_READ",
            "INVENTORY_WRITE",
            "ITEMS_READ",
            "ITEMS_WRITE",
            "BANK_ACCOUNTS_READ",
        ]
    )

    params = {
        "client_id": client_id,
        "scope": scopes,
        "state": state,
        "response_type": "code",
    }

    authorization_url = f"{auth_url}?{urlencode(params)}"

    logger.info(
        "Initiating Square OAuth flow",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_square_authorize_start",
    )

    return RedirectResponse(url=authorization_url)


@router.get("/oauth/square/callback")
async def square_oauth_callback(code: str, state: str) -> dict[str, Any]:
    """
    Handle Square OAuth callback.

    Exchange authorization code for access/refresh tokens and store them.
    State format: {org_id}:{user_id}:{credential_type}

    Note: Square access tokens expire in 30 days.
    Refresh tokens don't expire (for standard code flow).

    Args:
        code: Authorization code from Square
        state: State parameter containing org_id, user_id, credential_type

    Returns:
        Success response with OAuth completion details
    """
    org_id, user_id, credential_type = parse_oauth_state_3parts(state, "square")

    client_id = get_env_or_raise("SQUARE_APPLICATION_ID", "Square")
    client_secret = get_env_or_raise("SQUARE_APPLICATION_SECRET", "Square")
    redirect_uri = get_env_or_raise("SQUARE_REDIRECT_URI", "Square")

    _, token_url = _get_square_urls()

    logger.info(
        "Exchanging Square authorization code",
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_square_token_exchange_start",
    )

    # Exchange code for tokens using ObtainToken endpoint
    # https://developer.squareup.com/reference/square/o-auth-api/obtain-token
    response = requests.post(
        token_url,
        headers={
            "Content-Type": "application/json",
            "Square-Version": "2024-01-18",
        },
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        timeout=30,
    )

    if response.status_code != 200:
        logger.error(
            "Square token exchange failed",
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            log_event="oauth_square_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail="Token exchange failed")

    token_data = response.json()

    # Square access tokens expire in 30 days
    # expires_at is ISO 8601 format
    if "expires_at" in token_data:
        token_expiry = datetime.fromisoformat(token_data["expires_at"].replace("Z", "+00:00"))
    else:
        # Fallback to 30 days from now
        token_expiry = datetime.utcnow() + timedelta(days=30)

    # Store credentials
    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service="square",
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=token_expiry,
        extra_data={"merchant_id": token_data.get("merchant_id")},
    )

    logger.info(
        "Square OAuth completed successfully",
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        merchant_id=token_data.get("merchant_id"),
        log_event="oauth_square_callback_success",
    )

    return {
        "success": True,
        "message": "Square OAuth completed successfully",
        "org_id": org_id,
        "user_id": user_id,
        "credential_type": credential_type,
        "service": "square",
        "merchant_id": token_data.get("merchant_id"),
    }
