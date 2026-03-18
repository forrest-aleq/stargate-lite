"""
OAuth Routes Base Module

Common helper functions and utilities for OAuth flows.
"""

import hashlib
import hmac
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode

import requests
from fastapi import HTTPException
from fastapi.responses import RedirectResponse

from app.database import CredentialManager
from app.logging_config import get_logger

# Initialize structured logger
logger = get_logger(__name__)


def _get_state_signing_key() -> bytes:
    """Get the key used to sign OAuth state parameters."""
    key = os.getenv("OAUTH_STATE_SECRET") or os.getenv("ENCRYPTION_KEY")
    if not key:
        logger.error("No OAuth state signing key configured", log_event="oauth_state_key_missing")
        raise HTTPException(status_code=500, detail="OAuth state signing not configured")
    return key.encode("utf-8")


def _sign_state(payload: str) -> str:
    """Create HMAC-SHA256 signature for state payload."""
    key = _get_state_signing_key()
    signature = hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    # Use first 32 chars (128 bits) for CSRF protection
    return signature[:32]


def _verify_state_signature(payload: str, signature: str) -> bool:
    """Verify HMAC signature of state payload."""
    expected = _sign_state(payload)
    return hmac.compare_digest(expected, signature)


def build_signed_state_3parts(org_id: str, user_id: str, credential_type: str) -> str:
    """Build signed state: org_id:user_id:credential_type:signature."""
    payload = f"{org_id}:{user_id}:{credential_type}"
    signature = _sign_state(payload)
    return f"{payload}:{signature}"


def build_signed_state_4parts(
    org_id: str, user_id: str, credential_type: str, sub_service: str
) -> str:
    """Build signed state: org_id:user_id:credential_type:sub_service:signature."""
    payload = f"{org_id}:{user_id}:{credential_type}:{sub_service}"
    signature = _sign_state(payload)
    return f"{payload}:{signature}"


# Default redirect URLs (should be overridden by environment variables)
DEFAULT_SUCCESS_PATH = "/settings/integrations"
DEFAULT_ERROR_PATH = "/settings/integrations"


def get_n3_base_url() -> str:
    """Get N3 frontend base URL from environment."""
    return os.getenv("N3_FRONTEND_URL", "http://localhost:3000")


def _emit_connector_connected_event(
    service: str,
    org_id: str | None,
    user_id: str | None,
    source: str | None = None,
) -> None:
    """Best-effort connector lifecycle event for Baby MARS after OAuth success."""
    if not org_id:
        return

    webhook_url = os.getenv("BABY_MARS_WEBHOOK_URL", "").strip()
    api_key = os.getenv("API_SECRET_KEY", "").strip()
    if not webhook_url or not api_key:
        logger.debug(
            "Skipping connector event emit; webhook target not configured",
            service=service,
            org_id=org_id,
            log_event="oauth_connector_event_skip",
        )
        return

    now = datetime.now(UTC)
    raw_event_id = f"oauth:{service}:{org_id}:{user_id or 'unknown'}:{int(now.timestamp() * 1000)}"
    payload: dict[str, Any] = {
        "platform": service,
        "service": service,
        "status": "connected",
        "origin": "oauth_callback",
        "connected_at": now.isoformat(),
    }
    if user_id:
        payload["user_id"] = user_id
    if source:
        payload["source"] = source

    event_body = {
        "event_type": "connector.connected",
        "source_service": "stargate",
        "org_id": org_id,
        "timestamp": now.isoformat(),
        "raw_event_id": raw_event_id,
        "user_id": user_id,
        "payload": payload,
    }

    try:
        response = requests.post(
            webhook_url,
            json=event_body,
            headers={"X-API-Key": api_key},
            timeout=2,
        )
        if response.status_code >= 400:
            logger.warning(
                "Connector lifecycle event emit returned non-success",
                service=service,
                org_id=org_id,
                status_code=response.status_code,
                log_event="oauth_connector_event_emit_failed",
            )
            return

        logger.info(
            "Connector lifecycle event emitted",
            service=service,
            org_id=org_id,
            user_id=user_id,
            log_event="oauth_connector_event_emitted",
        )
    except Exception:
        logger.warning(
            "Connector lifecycle event emit failed",
            service=service,
            org_id=org_id,
            user_id=user_id,
            log_event="oauth_connector_event_exception",
            exc_info=True,
        )


def build_oauth_success_redirect(
    service: str,
    org_id: str | None = None,
    extra_params: dict[str, str] | None = None,
    user_id: str | None = None,
) -> RedirectResponse:
    """Build redirect to N3 success page after OAuth completion."""
    source = extra_params.get("source") if isinstance(extra_params, dict) else None
    _emit_connector_connected_event(
        service=service,
        org_id=org_id,
        user_id=user_id,
        source=source,
    )

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
    """Build redirect to N3 error page after OAuth failure."""
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
    """Parse signed state → (org_id, user_id, credential_type)."""
    parts = state.split(":")

    # New signed format has 4 parts (3 data + 1 signature)
    if len(parts) == 4:
        org_id, user_id, credential_type, signature = parts
        payload = f"{org_id}:{user_id}:{credential_type}"

        if not _verify_state_signature(payload, signature):
            logger.warning(
                "OAuth state signature verification failed",
                service=service,
                log_event="oauth_state_signature_invalid",
            )
            raise HTTPException(
                status_code=400, detail="Invalid state parameter: signature mismatch"
            )
    elif len(parts) == 3:
        # Reject unsigned state — transition period is over
        logger.warning(
            "Rejected unsigned OAuth state",
            service=service,
            log_event="oauth_state_unsigned_rejected",
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter: signature required")
    else:
        logger.warning(
            "Invalid state parameter format", service=service, log_event="oauth_state_invalid"
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter")

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


def build_signed_state_5parts(
    org_id: str, user_id: str, credential_type: str, sub_service: str, extra: str
) -> str:
    """Build signed state: org_id:user_id:credential_type:sub_service:extra:signature."""
    payload = f"{org_id}:{user_id}:{credential_type}:{sub_service}:{extra}"
    signature = _sign_state(payload)
    return f"{payload}:{signature}"


def parse_oauth_state_5parts(state: str, service: str) -> tuple[str, str, str, str, str]:
    """Parse signed state → (org_id, user_id, credential_type, sub_service, extra)."""
    parts = state.split(":")

    # Signed format has 6 parts (5 data + 1 signature)
    if len(parts) != 6:
        logger.warning(
            "Invalid state parameter format", service=service, log_event="oauth_state_invalid"
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    org_id, user_id, credential_type, sub_service, extra, signature = parts
    payload = f"{org_id}:{user_id}:{credential_type}:{sub_service}:{extra}"

    if not _verify_state_signature(payload, signature):
        logger.warning(
            "OAuth state signature verification failed",
            service=service,
            log_event="oauth_state_signature_invalid",
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter: signature mismatch")

    if not org_id or not user_id or not credential_type:
        logger.warning(
            "OAuth state contains empty values",
            service=service,
            log_event="oauth_state_empty_values",
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter: empty values")

    return org_id, user_id, credential_type, sub_service, extra


def build_signed_state_6parts(
    org_id: str,
    user_id: str,
    credential_type: str,
    sub_service: str,
    extra: str,
    extra2: str,
) -> str:
    """Build signed state with 6 data parts + signature."""
    payload = f"{org_id}:{user_id}:{credential_type}:{sub_service}:{extra}:{extra2}"
    signature = _sign_state(payload)
    return f"{payload}:{signature}"


def parse_oauth_state_6parts(state: str, service: str) -> tuple[str, str, str, str, str, str]:
    """Parse signed state → (org_id, user_id, credential_type, sub_service, extra, extra2)."""
    parts = state.split(":")

    # Signed format has 7 parts (6 data + 1 signature)
    if len(parts) != 7:
        logger.warning(
            "Invalid state parameter format", service=service, log_event="oauth_state_invalid"
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    org_id, user_id, credential_type, sub_service, extra, extra2, signature = parts
    payload = f"{org_id}:{user_id}:{credential_type}:{sub_service}:{extra}:{extra2}"

    if not _verify_state_signature(payload, signature):
        logger.warning(
            "OAuth state signature verification failed",
            service=service,
            log_event="oauth_state_signature_invalid",
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter: signature mismatch")

    if not org_id or not user_id or not credential_type:
        logger.warning(
            "OAuth state contains empty values",
            service=service,
            log_event="oauth_state_empty_values",
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter: empty values")

    return org_id, user_id, credential_type, sub_service, extra, extra2


def parse_oauth_state_4parts(state: str, service: str) -> tuple[str, str, str, str]:
    """Parse signed state → (org_id, user_id, credential_type, sub_service)."""
    parts = state.split(":")

    # New signed format has 5 parts (4 data + 1 signature)
    if len(parts) == 5:
        org_id, user_id, credential_type, sub_service, signature = parts
        payload = f"{org_id}:{user_id}:{credential_type}:{sub_service}"

        if not _verify_state_signature(payload, signature):
            logger.warning(
                "OAuth state signature verification failed",
                service=service,
                log_event="oauth_state_signature_invalid",
            )
            raise HTTPException(
                status_code=400, detail="Invalid state parameter: signature mismatch"
            )
    elif len(parts) == 4:
        # Reject unsigned state — transition period is over
        logger.warning(
            "Rejected unsigned OAuth state",
            service=service,
            log_event="oauth_state_unsigned_rejected",
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter: signature required")
    else:
        logger.warning(
            "Invalid state parameter format", service=service, log_event="oauth_state_invalid"
        )
        raise HTTPException(status_code=400, detail="Invalid state parameter")

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
    """Exchange authorization code for tokens using HTTP Basic Auth."""
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
    """Exchange authorization code for tokens using form data."""
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
    """Store OAuth credentials with automatic expiry calculation."""
    expires_in = token_data.get("expires_in", default_expiry_seconds)
    token_expiry = datetime.now(UTC) + timedelta(seconds=expires_in)

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
    """Store OAuth credentials for tokens that don't expire."""
    # 100 years for tokens that don't expire
    token_expiry = datetime.now(UTC) + timedelta(days=36500)

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
    """Get environment variable or raise HTTPException."""
    value = os.getenv(var_name)
    if not value:
        raise HTTPException(status_code=500, detail=f"{service} OAuth not configured")
    return value
