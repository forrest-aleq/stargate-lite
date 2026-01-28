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
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

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

    # State is cryptographically signed to prevent CSRF/tampering
    # We include shop as sub_service to verify it matches on callback
    state = build_signed_state_4parts(org_id, user_id, credential_type, shop)

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
) -> RedirectResponse:
    """Handle Shopify OAuth callback with HMAC validation. Redirects to N3."""
    try:
        org_id, user_id, _credential_type, state_shop = parse_oauth_state_4parts(state, "shopify")
    except HTTPException:
        return build_oauth_error_redirect(
            service="shopify",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    # Normalize and verify shop name
    callback_shop = shop.replace(".myshopify.com", "")
    if callback_shop != state_shop:
        logger.warning("Shopify shop mismatch", expected=state_shop, received=callback_shop)
        return build_oauth_error_redirect(
            service="shopify",
            error="shop_mismatch",
            error_description="Shop mismatch in callback",
            org_id=org_id,
        )

    try:
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
            return build_oauth_error_redirect(
                service="shopify",
                error="token_exchange_failed",
                error_description="Token exchange with Shopify failed",
                org_id=org_id,
            )

        token_data = response.json()

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
        return build_oauth_success_redirect(service="shopify", org_id=org_id)

    except HTTPException as e:
        return build_oauth_error_redirect(
            service="shopify",
            error="validation_failed",
            error_description=str(e.detail),
            org_id=org_id,
        )
    except Exception as e:
        logger.error("Shopify OAuth callback failed", error=str(e), exc_info=True)
        return build_oauth_error_redirect(
            service="shopify",
            error="callback_failed",
            error_description=str(e),
            org_id=org_id,
        )


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

    # State is cryptographically signed to prevent CSRF/tampering
    state = build_signed_state_3parts(org_id, user_id, credential_type)

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
async def square_oauth_callback(code: str, state: str) -> RedirectResponse:
    """Handle Square OAuth callback. Redirects to N3 on completion."""
    # Parse state first
    try:
        org_id, user_id, _credential_type = parse_oauth_state_3parts(state, "square")
    except HTTPException:
        return build_oauth_error_redirect(
            service="square",
            error="invalid_state",
            error_description="Invalid OAuth state parameter",
        )

    try:
        client_id = get_env_or_raise("SQUARE_APPLICATION_ID", "Square")
        client_secret = get_env_or_raise("SQUARE_APPLICATION_SECRET", "Square")
        redirect_uri = get_env_or_raise("SQUARE_REDIRECT_URI", "Square")

        _, token_url = _get_square_urls()

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
            logger.error("Square token exchange failed", status_code=response.status_code)
            return build_oauth_error_redirect(
                service="square",
                error="token_exchange_failed",
                error_description="Token exchange with Square failed",
                org_id=org_id,
            )

        token_data = response.json()

        if "expires_at" in token_data:
            token_expiry = datetime.fromisoformat(token_data["expires_at"].replace("Z", "+00:00"))
        else:
            token_expiry = datetime.utcnow() + timedelta(days=30)

        CredentialManager.store_credential(
            org_id=org_id,
            user_id=user_id,
            service="square",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=token_expiry,
            extra_data={"merchant_id": token_data.get("merchant_id")},
        )

        logger.info("Square OAuth completed", org_id=org_id)
        return build_oauth_success_redirect(service="square", org_id=org_id)

    except HTTPException as e:
        return build_oauth_error_redirect(
            service="square",
            error="config_error",
            error_description=str(e.detail),
            org_id=org_id,
        )
    except Exception as e:
        logger.error("Square OAuth callback failed", error=str(e), exc_info=True)
        return build_oauth_error_redirect(
            service="square",
            error="callback_failed",
            error_description=str(e),
            org_id=org_id,
        )
