"""
OAuth Routes Base Module

Common helper functions and utilities for OAuth flows.
"""

import os
import time
from datetime import datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode

import requests
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.logging_config import get_logger

# Initialize structured logger
logger = get_logger(__name__)

# Default redirect URLs (should be overridden by environment variables)
DEFAULT_SUCCESS_PATH = "/settings/integrations"
DEFAULT_ERROR_PATH = "/settings/integrations"


def get_n3_base_url() -> str:
    """Get N3 frontend base URL from environment."""
    return os.getenv("N3_FRONTEND_URL", "http://localhost:3000")


def build_oauth_success_redirect(
    service: str,
    org_id: str | None = None,
    extra_params: dict[str, str] | None = None,
) -> RedirectResponse:
    """Build redirect response for successful OAuth completion.

    Args:
        service: Service name (e.g., "quickbooks")
        org_id: Organization ID (optional, for logging)
        extra_params: Additional query parameters

    Returns:
        RedirectResponse to N3 success page
    """
    base_url = get_n3_base_url()
    params: dict[str, str] = {"connected": service}
    if extra_params:
        params.update(extra_params)

    redirect_url = f"{base_url}{DEFAULT_SUCCESS_PATH}?{urlencode(params)}"

    logger.info(
        "OAuth success, redirecting to N3",
        service=service,
        org_id=org_id,
        redirect_url=redirect_url,
        log_event="oauth_redirect_success",
    )

    return RedirectResponse(url=redirect_url, status_code=302)


def build_oauth_error_redirect(
    service: str,
    error: str,
    error_description: str | None = None,
    org_id: str | None = None,
) -> RedirectResponse:
    """Build redirect response for failed OAuth.

    Args:
        service: Service name (e.g., "quickbooks")
        error: Error code (e.g., "token_exchange_failed")
        error_description: Human-readable error description
        org_id: Organization ID (optional, for logging)

    Returns:
        RedirectResponse to N3 error page
    """
    base_url = get_n3_base_url()
    params: dict[str, str] = {
        "error": error,
        "provider": service,
    }
    if error_description:
        params["error_description"] = error_description

    redirect_url = f"{base_url}{DEFAULT_ERROR_PATH}?{urlencode(params)}"

    logger.warning(
        "OAuth failed, redirecting to N3 with error",
        service=service,
        org_id=org_id,
        error=error,
        redirect_url=redirect_url,
        log_event="oauth_redirect_error",
    )

    return RedirectResponse(url=redirect_url, status_code=302)


def parse_oauth_state_3parts(state: str, service: str) -> tuple[str, str, str]:
    """Parse OAuth state parameter with format org_id:user_id:credential_type.

    Args:
        state: The state parameter from OAuth callback
        service: Service name for logging

    Returns:
        Tuple of (org_id, user_id, credential_type)

    Raises:
        HTTPException: If state is invalid or contains empty values
    """
    parts = state.split(":")
    if len(parts) != 3:
        logger.warning(
            "Invalid state parameter format", service=service, log_event="oauth_state_invalid"
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    org_id, user_id, credential_type = parts

    if not org_id or not user_id or not credential_type:
        logger.warning(
            "OAuth state contains empty values",
            service=service,
            log_event="oauth_state_empty_values",
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter: empty values")

    logger.debug(
        "OAuth state decoded",
        service=service,
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_state_decoded",
    )

    return org_id, user_id, credential_type


def parse_oauth_state_4parts(state: str, service: str) -> tuple[str, str, str, str]:
    """Parse OAuth state parameter with format org_id:user_id:credential_type:service.

    Args:
        state: The state parameter from OAuth callback
        service: Service name for logging

    Returns:
        Tuple of (org_id, user_id, credential_type, sub_service)

    Raises:
        HTTPException: If state is invalid or contains empty values
    """
    parts = state.split(":")
    if len(parts) != 4:
        logger.warning(
            "Invalid state parameter format", service=service, log_event="oauth_state_invalid"
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    org_id, user_id, credential_type, sub_service = parts

    if not org_id or not user_id or not credential_type or not sub_service:
        logger.warning(
            "OAuth state contains empty values",
            service=service,
            log_event="oauth_state_empty_values",
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter: empty values")

    return org_id, user_id, credential_type, sub_service


def exchange_tokens_basic_auth(
    token_url: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
    service: str,
    org_id: str,
    user_id: str,
    extra_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exchange authorization code for tokens using HTTP Basic Auth.

    Args:
        token_url: Token endpoint URL
        code: Authorization code
        redirect_uri: Redirect URI used in authorization
        client_id: OAuth client ID
        client_secret: OAuth client secret
        service: Service name for logging
        org_id: Organization ID for logging
        user_id: User ID for logging
        extra_data: Additional data to include in request

    Returns:
        Token data from OAuth provider

    Raises:
        HTTPException: If token exchange fails
    """
    logger.info(
        "Exchanging code for tokens",
        service=service,
        org_id=org_id,
        user_id=user_id,
        log_event="oauth_token_exchange_start",
    )

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    if extra_data:
        data.update(extra_data)

    token_start = time.time()
    response = requests.post(
        token_url,
        auth=(client_id, client_secret),
        data=data,
        timeout=30,
    )
    token_duration_ms = (time.time() - token_start) * 1000

    if response.status_code != 200:
        logger.error(
            "Token exchange failed",
            service=service,
            org_id=org_id,
            user_id=user_id,
            status_code=response.status_code,
            duration_ms=round(token_duration_ms, 2),
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

    logger.info(
        "Token exchange successful",
        service=service,
        org_id=org_id,
        user_id=user_id,
        duration_ms=round(token_duration_ms, 2),
        log_event="oauth_token_exchange_success",
    )

    return cast(dict[str, Any], response.json())


def exchange_tokens_form_data(
    token_url: str,
    code: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
    service: str,
    org_id: str,
    user_id: str,
) -> dict[str, Any]:
    """Exchange authorization code for tokens using form data.

    Args:
        token_url: Token endpoint URL
        code: Authorization code
        redirect_uri: Redirect URI used in authorization
        client_id: OAuth client ID
        client_secret: OAuth client secret
        service: Service name for logging
        org_id: Organization ID for logging
        user_id: User ID for logging

    Returns:
        Token data from OAuth provider

    Raises:
        HTTPException: If token exchange fails
    """
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
        logger.error(
            "Token exchange failed",
            service=service,
            status_code=response.status_code,
            log_event="oauth_token_exchange_error",
        )
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {response.text}")

    return cast(dict[str, Any], response.json())


def store_credential_with_expiry(
    org_id: str,
    user_id: str,
    service: str,
    token_data: dict[str, Any],
    credential_type: str,
    default_expiry_seconds: int = 3600,
) -> None:
    """Store OAuth credentials with automatic expiry calculation.

    Args:
        org_id: Organization ID
        user_id: User ID
        service: Service name
        token_data: Token data from OAuth provider
        credential_type: Type of credential (customer/agent)
        default_expiry_seconds: Default expiry if not in token_data
    """
    expires_in = token_data.get("expires_in", default_expiry_seconds)
    token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service=service,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=token_expiry,
    )

    logger.info(
        "OAuth flow completed successfully",
        service=service,
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_callback_success",
    )


def store_credential_no_expiry(
    org_id: str,
    user_id: str,
    service: str,
    token_data: dict[str, Any],
    credential_type: str,
) -> None:
    """Store OAuth credentials for tokens that don't expire.

    Args:
        org_id: Organization ID
        user_id: User ID
        service: Service name
        token_data: Token data from OAuth provider
        credential_type: Type of credential (customer/agent)
    """
    # 100 years for tokens that don't expire
    token_expiry = datetime.utcnow() + timedelta(days=36500)

    CredentialManager.store_credential(
        org_id=org_id,
        user_id=user_id,
        service=service,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=token_expiry,
    )

    logger.info(
        "OAuth flow completed successfully",
        service=service,
        org_id=org_id,
        user_id=user_id,
        credential_type=credential_type,
        log_event="oauth_callback_success",
    )


def get_env_or_raise(var_name: str, service: str) -> str:
    """Get environment variable or raise HTTPException.

    Args:
        var_name: Environment variable name
        service: Service name for error message

    Returns:
        Environment variable value

    Raises:
        HTTPException: If environment variable is not set
    """
    value = os.getenv(var_name)
    if not value:
        raise HTTPException(status_code=500, detail=f"{service} OAuth not configured")
    return value
