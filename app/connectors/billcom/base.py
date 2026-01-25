"""
Bill.com connector base with session-based authentication.

API Reference: https://developer.bill.com/reference/api-reference-overview
Authentication: Session-based (NOT OAuth 2.0)
  - Login with credentials to get sessionId
  - Use sessionId + devKey in headers for all API calls
  - Session expires after 35 minutes of inactivity

Base URLs:
  - Sandbox: https://gateway.stage.bill.com/connect/v3
  - Production: https://gateway.bill.com/connect/v3

Session caching: Uses Redis for horizontal scaling support.
"""

import contextlib
import json
import os
from datetime import datetime, timedelta
from typing import Any

from app.database import CredentialManager
from app.errors import (
    CredentialInvalidError,
    CredentialMissingError,
    ExternalAPIError,
    ValidationError,
)
from app.http_client import http_client
from app.logging_config import get_logger
from app.posthog_client import track_token_refreshed

logger = get_logger(__name__)

# Redis key prefix for Bill.com sessions
BILLCOM_SESSION_PREFIX = "stargate:billcom:session:"


def _get_redis() -> Any:
    """Get Redis client for session caching."""
    try:
        from app.redis_client import redis_client

        return redis_client._redis_client
    except Exception:
        return None


class BillComBase:
    """
    Bill.com v3 API base connector with session-based authentication.

    Implements automatic session management with re-login on expiry.
    Uses Redis for session caching to support horizontal scaling.
    """

    PRODUCTION_URL = "https://gateway.bill.com/connect/v3"
    SANDBOX_URL = "https://gateway.stage.bill.com/connect/v3"
    SESSION_TTL_SECONDS = 30 * 60  # 30 min buffer (actual: 35 min)

    def __init__(self) -> None:
        self.dev_key = os.getenv("BILLCOM_DEV_KEY", "")
        self.environment = os.getenv("BILLCOM_ENVIRONMENT", "sandbox")
        self.base_url = self.SANDBOX_URL if self.environment == "sandbox" else self.PRODUCTION_URL

    def _get_cached_session(self, cache_key: str) -> dict[str, Any] | None:
        """Get session from Redis cache."""
        redis = _get_redis()
        if not redis:
            return None

        try:
            cached_data = redis.get(f"{BILLCOM_SESSION_PREFIX}{cache_key}")
            if cached_data:
                session: dict[str, Any] = json.loads(cached_data)
                # Check if session is still valid
                expires_at = datetime.fromisoformat(session["expires_at"])
                if expires_at > datetime.utcnow():
                    return session
            return None
        except Exception as e:
            logger.warning(
                "Redis session cache read failed",
                error=str(e),
                log_event="billcom_cache_read_error",
            )
            return None

    def _cache_session(self, cache_key: str, session_data: dict[str, Any]) -> None:
        """Store session in Redis cache."""
        redis = _get_redis()
        if not redis:
            return

        try:
            # Convert datetime to ISO string for JSON serialization
            cache_data = {
                **session_data,
                "expires_at": session_data["expires_at"].isoformat(),
            }
            redis.setex(
                name=f"{BILLCOM_SESSION_PREFIX}{cache_key}",
                time=self.SESSION_TTL_SECONDS,
                value=json.dumps(cache_data),
            )
        except Exception as e:
            logger.warning(
                "Redis session cache write failed",
                error=str(e),
                log_event="billcom_cache_write_error",
            )

    def _invalidate_cached_session(self, cache_key: str) -> None:
        """Remove session from Redis cache."""
        redis = _get_redis()
        if not redis:
            return

        try:
            redis.delete(f"{BILLCOM_SESSION_PREFIX}{cache_key}")
        except Exception as e:
            logger.warning(
                "Redis session cache delete failed",
                error=str(e),
                log_event="billcom_cache_delete_error",
            )

    def _get_session(self, org_id: str, user_id: str) -> dict[str, Any]:
        """
        Get a valid session, creating or refreshing as needed.

        Credentials stored in DB:
        - access_token: Bill.com username (or sync token name)
        - refresh_token: Bill.com password (or sync token value)
        - realm_id: Bill.com organization ID
        """
        cache_key = f"{org_id}:{user_id}"

        # Check Redis cache first
        cached = self._get_cached_session(cache_key)
        if cached:
            # Reconstruct datetime object
            cached["expires_at"] = datetime.fromisoformat(cached["expires_at"])
            return cached

        cred = CredentialManager.get_credential(org_id, user_id, "billcom")
        if not cred:
            raise CredentialMissingError("billcom", org_id, user_id)

        username = cred.get("access_token")
        password = cred.get("refresh_token")
        organization_id = cred.get("realm_id")

        if not all([username, password, organization_id]):
            raise ValidationError(
                "credentials",
                "Bill.com credentials incomplete. Required: username, password, organization_id",
            )

        if not self.dev_key:
            raise ValidationError("configuration", "BILLCOM_DEV_KEY not set")

        logger.info(
            "Creating Bill.com session",
            service="billcom",
            org_id=org_id,
            log_event="session_create_start",
        )

        try:
            response = http_client.post(
                url=f"{self.base_url}/login",
                service="billcom",
                headers={"Content-Type": "application/json"},
                json={
                    "userName": username,
                    "password": password,
                    "orgId": organization_id,
                    "devKey": self.dev_key,
                },
            )

            session_id = response.get("sessionId")
            if not session_id:
                raise CredentialInvalidError("billcom", "Login response missing sessionId")

            session_data = {
                "session_id": session_id,
                "dev_key": self.dev_key,
                "expires_at": datetime.utcnow() + timedelta(seconds=self.SESSION_TTL_SECONDS),
                "org_id": organization_id,
            }

            # Cache in Redis
            self._cache_session(cache_key, session_data)

            logger.info(
                "Bill.com session created",
                service="billcom",
                org_id=org_id,
                log_event="session_create_success",
            )

            # Track session creation (analogous to token refresh for OAuth connectors)
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="billcom",
                success=True,
            )

            return session_data

        except Exception as e:
            logger.error(
                "Bill.com session creation failed",
                service="billcom",
                org_id=org_id,
                error_type=type(e).__name__,
                log_event="session_create_error",
                exc_info=True,
            )

            # Track failed session creation
            track_token_refreshed(
                user_id=user_id,
                org_id=org_id,
                service="billcom",
                success=False,
            )
            raise

    def _get_headers(self, session: dict[str, Any]) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "Content-Type": "application/json",
            "sessionId": session["session_id"],
            "devKey": session["dev_key"],
        }

    def _invalidate_session(self, org_id: str, user_id: str) -> None:
        """Invalidate cached session."""
        cache_key = f"{org_id}:{user_id}"
        self._invalidate_cached_session(cache_key)

    def _api_call(
        self,
        method: str,
        endpoint: str,
        org_id: str,
        user_id: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_on_auth_error: bool = True,
    ) -> dict[str, Any]:
        """Make an API call with automatic session management."""
        session = self._get_session(org_id, user_id)
        headers = self._get_headers(session)
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                return http_client.get(url=url, service="billcom", headers=headers, params=params)
            elif method.upper() == "POST":
                return http_client.post(url=url, service="billcom", headers=headers, json=json_data)
            elif method.upper() == "PATCH":
                return http_client.patch(
                    url=url, service="billcom", headers=headers, json=json_data
                )
            elif method.upper() == "DELETE":
                return http_client.delete(url=url, service="billcom", headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

        except ExternalAPIError as e:
            status_code = e.details.get("external_status_code")
            if retry_on_auth_error and status_code in (401, 403):
                logger.warning(
                    "Bill.com session expired, re-authenticating",
                    service="billcom",
                    log_event="session_expired",
                )
                self._invalidate_session(org_id, user_id)
                return self._api_call(
                    method,
                    endpoint,
                    org_id,
                    user_id,
                    json_data,
                    params,
                    retry_on_auth_error=False,
                )
            raise

    def logout(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Explicitly logout and invalidate the session."""
        with contextlib.suppress(Exception):
            self._api_call("POST", "/logout", org_id, user_id, json_data={})
        self._invalidate_session(org_id, user_id)
        return {"logged_out": True}
