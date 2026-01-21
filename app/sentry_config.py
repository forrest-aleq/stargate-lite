"""
Sentry error tracking configuration for Stargate Lite.

Provides deep error tracking with full context for debugging API failures.
Captures connector errors, token refresh failures, timeouts, and unexpected exceptions.
"""

import os
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.logging_config import get_logger

logger = get_logger(__name__)

# Environment config
SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("ENVIRONMENT", os.getenv("DD_ENV", "development"))
RELEASE = os.getenv("RELEASE_VERSION", os.getenv("GIT_SHA", "unknown"))


def init_sentry() -> bool:
    """
    Initialize Sentry error tracking.

    Returns True if Sentry was initialized, False if skipped (no DSN).
    """
    if not SENTRY_DSN:
        logger.info(
            "Sentry DSN not configured, error tracking disabled",
            log_event="sentry_skip",
        )
        return False

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        release=RELEASE,
        # Capture 100% of errors, sample 10% of transactions for performance
        traces_sample_rate=0.1,
        # Send all errors
        sample_rate=1.0,
        # Integrations
        integrations=[
            # FastAPI/Starlette - auto-capture request context
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            # HTTP client calls - capture outbound API calls
            HttpxIntegration(),
            # SQLAlchemy - capture DB queries
            SqlalchemyIntegration(),
            # Logging - capture error logs as breadcrumbs
            LoggingIntegration(
                level=None,  # Capture all levels as breadcrumbs
                event_level=None,  # Don't create events from logs (we do it manually)
            ),
        ],
        # Scrub sensitive data
        send_default_pii=False,
        # Add tags to all events
        default_integrations=True,
        # Before send hook for additional scrubbing
        before_send=_before_send,
        # Before breadcrumb hook
        before_breadcrumb=_before_breadcrumb,
    )

    # Set global tags
    sentry_sdk.set_tag("service", "stargate-lite")

    logger.info(
        "Sentry initialized",
        environment=ENVIRONMENT,
        release=RELEASE,
        log_event="sentry_init",
    )
    return True


def _before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """
    Process event before sending to Sentry.

    - Scrub sensitive data
    - Add additional context
    - Filter out noise
    """
    # Scrub sensitive headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        sensitive_headers = ["authorization", "x-api-key", "cookie", "x-auth-token"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[REDACTED]"

    # Scrub tokens from exception messages
    if "exception" in event:
        for exc in event["exception"].get("values", []):
            if "value" in exc:
                exc["value"] = _scrub_tokens(exc["value"])

    return event


def _before_breadcrumb(
    breadcrumb: dict[str, Any], hint: dict[str, Any]
) -> dict[str, Any] | None:
    """Filter/modify breadcrumbs before they're added."""
    # Skip noisy breadcrumbs
    if breadcrumb.get("category") == "httpx" and "health" in str(
        breadcrumb.get("data", {}).get("url", "")
    ):
        return None

    return breadcrumb


def _scrub_tokens(message: str) -> str:
    """Scrub OAuth tokens and API keys from error messages."""
    import re

    # Patterns for common token formats
    patterns = [
        (r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[JWT_REDACTED]"),
        (r"Bearer\s+[A-Za-z0-9_-]+", "Bearer [REDACTED]"),
        (r"access_token['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]+", "access_token=[REDACTED]"),
        (r"refresh_token['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]+", "refresh_token=[REDACTED]"),
        (r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]+", "api_key=[REDACTED]"),
        (r"sk_live_[A-Za-z0-9]+", "[STRIPE_KEY_REDACTED]"),
        (r"sk_test_[A-Za-z0-9]+", "[STRIPE_KEY_REDACTED]"),
    ]

    for pattern, replacement in patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

    return message


def set_user_context(org_id: str, user_id: str) -> None:
    """Set user context for Sentry events."""
    sentry_sdk.set_user({"id": f"{org_id}:{user_id}", "org_id": org_id})
    sentry_sdk.set_tag("org_id", org_id)
    sentry_sdk.set_tag("user_id", user_id)


def set_capability_context(capability_key: str, service: str, tool_name: str) -> None:
    """Set capability context for Sentry events."""
    sentry_sdk.set_tag("capability_key", capability_key)
    sentry_sdk.set_tag("service", service)
    sentry_sdk.set_tag("tool_name", tool_name)
    sentry_sdk.set_context(
        "capability",
        {
            "key": capability_key,
            "service": service,
            "tool_name": tool_name,
        },
    )


def capture_connector_error(
    error: Exception,
    service: str,
    operation: str,
    org_id: str,
    user_id: str,
    extra: dict[str, Any] | None = None,
) -> str | None:
    """
    Capture a connector error with full context.

    Returns the Sentry event ID if captured, None if Sentry is not configured.
    """
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_source", "connector")
        scope.set_tag("service", service)
        scope.set_tag("operation", operation)
        scope.set_tag("org_id", org_id)
        scope.set_tag("user_id", user_id)

        scope.set_context(
            "connector",
            {
                "service": service,
                "operation": operation,
                "org_id": org_id,
                "user_id": user_id,
                **(extra or {}),
            },
        )

        # Fingerprint by service + error type for grouping
        scope.fingerprint = [service, type(error).__name__, operation]

        return sentry_sdk.capture_exception(error)


def capture_api_error(
    error: Exception,
    service: str,
    endpoint: str,
    status_code: int | None = None,
    response_body: str | None = None,
) -> str | None:
    """
    Capture an external API error with response details.

    For when QuickBooks/Stripe/etc returns an error.
    """
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_source", "external_api")
        scope.set_tag("service", service)
        scope.set_tag("endpoint", endpoint)
        if status_code:
            scope.set_tag("status_code", str(status_code))

        scope.set_context(
            "api_response",
            {
                "service": service,
                "endpoint": endpoint,
                "status_code": status_code,
                "response_preview": (response_body[:500] if response_body else None),
            },
        )

        # Fingerprint by service + status code for grouping
        scope.fingerprint = [service, str(status_code), type(error).__name__]

        return sentry_sdk.capture_exception(error)


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb for debugging context."""
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data,
    )
