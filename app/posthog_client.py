"""
PostHog analytics integration for Stargate Lite.

Tracks capability executions, connector errors, token refreshes, and FCI aggregations.
Events are joined across the stack via session_id:

Frontend (posthog-js) → Baby MARS (posthog-python) → Stargate (posthog-python)
       ↓                        ↓                          ↓
  user actions           cognitive events            API/connector events
                  ↘            ↓            ↙
                       session_id joins all
"""

import atexit
import contextlib
import os
from typing import Any

import posthog

from app.logging_config import get_logger

logger = get_logger(__name__)

# Configuration
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY")
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")

# Initialize PostHog
_initialized = False


def init_posthog() -> bool:
    """
    Initialize PostHog client.

    Returns True if initialized, False if skipped (no API key).
    """
    global _initialized

    if _initialized:
        return True

    if not POSTHOG_API_KEY:
        logger.info(
            "PostHog API key not configured, analytics disabled",
            log_event="posthog_skip",
        )
        return False

    # posthog-python v7 requires `api_key` for capture/identify. Keep
    # `project_api_key` in sync as well for any legacy/internal access.
    posthog.api_key = POSTHOG_API_KEY
    posthog.project_api_key = POSTHOG_API_KEY
    posthog.host = POSTHOG_HOST

    # Disable debug mode in production
    posthog.debug = os.getenv("POSTHOG_DEBUG", "false").lower() == "true"

    # Ensure events are flushed on shutdown
    atexit.register(posthog.shutdown)

    _initialized = True
    logger.info(
        "PostHog initialized",
        host=POSTHOG_HOST,
        log_event="posthog_init",
    )
    return True


def track(
    event: str,
    user_id: str,
    org_id: str,
    session_id: str | None = None,
    properties: dict[str, Any] | None = None,
) -> None:
    """
    Track an event to PostHog.

    Args:
        event: Event name (e.g., "capability_called", "connector_error")
        user_id: User identifier (distinct_id in PostHog)
        org_id: Organization identifier
        session_id: Session ID that joins events across the stack
        properties: Additional event properties
    """
    if not _initialized and not init_posthog():
        return

    try:
        posthog.capture(
            distinct_id=f"{org_id}:{user_id}",
            event=event,
            properties={
                "org_id": org_id,
                "user_id": user_id,
                **({"session_id": session_id} if session_id else {}),
                "$lib": "stargate-lite",
                **(properties or {}),
            },
        )
    except Exception as e:
        # Never let analytics break the main flow
        logger.warning(
            "PostHog tracking failed",
            posthog_event=event,
            error=str(e),
            log_event="posthog_error",
        )


def track_capability_called(
    user_id: str,
    org_id: str,
    capability_key: str,
    service: str,
    tool_name: str,
    session_id: str | None = None,
    duration_ms: float | None = None,
    success: bool = True,
) -> None:
    """Track a capability execution."""
    track(
        event="capability_called",
        user_id=user_id,
        org_id=org_id,
        session_id=session_id,
        properties={
            "capability_key": capability_key,
            "service": service,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "success": success,
        },
    )


def track_connector_error(
    user_id: str,
    org_id: str,
    service: str,
    error_code: str,
    error_message: str,
    session_id: str | None = None,
    status_code: int | None = None,
    capability_key: str | None = None,
) -> None:
    """Track a connector/API error."""
    track(
        event="connector_error",
        user_id=user_id,
        org_id=org_id,
        session_id=session_id,
        properties={
            "service": service,
            "error_code": error_code,
            "error_message": error_message[:200],  # Truncate for safety
            "status_code": status_code,
            "capability_key": capability_key,
        },
    )


def track_token_refreshed(
    user_id: str,
    org_id: str,
    service: str,
    session_id: str | None = None,
    success: bool = True,
) -> None:
    """Track an OAuth token refresh."""
    track(
        event="token_refreshed",
        user_id=user_id,
        org_id=org_id,
        session_id=session_id,
        properties={
            "service": service,
            "success": success,
        },
    )


def track_fci_aggregation(
    user_id: str,
    org_id: str,
    fci_type: str,
    sources: list[str],
    session_id: str | None = None,
    duration_ms: float | None = None,
    partial: bool = False,
) -> None:
    """Track an FCI aggregation execution."""
    track(
        event="fci_aggregation",
        user_id=user_id,
        org_id=org_id,
        session_id=session_id,
        properties={
            "fci_type": fci_type,
            "sources": sources,
            "source_count": len(sources),
            "duration_ms": duration_ms,
            "partial": partial,
        },
    )


def identify_user(
    user_id: str,
    org_id: str,
    properties: dict[str, Any] | None = None,
) -> None:
    """
    Identify a user with properties for PostHog profiles.

    Call this when user info changes or on first capability call.
    """
    if not _initialized and not init_posthog():
        return

    try:
        posthog.identify(
            distinct_id=f"{org_id}:{user_id}",
            properties={
                "org_id": org_id,
                "user_id": user_id,
                **(properties or {}),
            },
        )
    except Exception as e:
        logger.warning(
            "PostHog identify failed",
            error=str(e),
            log_event="posthog_error",
        )


def flush() -> None:
    """Force flush all pending events. Useful before shutdown."""
    if _initialized:
        with contextlib.suppress(Exception):
            posthog.flush()
