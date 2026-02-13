"""
Execution service - Helper functions for tool execution.
"""

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from app.constants.services import build_connect_url
from app.errors import CapabilityNotFoundError, ErrorCode, StargateError, classify_exception
from app.logging_config import get_logger
from app.models import ToolExecutionRequest
from app.posthog_client import track_capability_called, track_connector_error
from app.redis_client import CACHE_TTL_PERMANENT, get_cache_ttl, redis_client
from app.sentry_config import (
    add_breadcrumb,
    capture_connector_error as sentry_capture_connector_error,
    set_capability_context,
    set_user_context,
)

logger = get_logger(__name__)


async def check_idempotency_cache(turn_id: str, capability_key: str) -> dict[str, Any] | None:
    """Check Redis cache for existing response. Returns cached response or None."""
    cached = await asyncio.to_thread(
        redis_client.get_cached_response, turn_id=turn_id, capability_key=capability_key
    )
    if cached:
        logger.info("Returning cached response", log_event="cache_hit")
    return cached


async def handle_capability_not_found(request: ToolExecutionRequest) -> dict[str, Any]:
    """Build and cache error response for missing capability."""
    logger.warning("Capability not found in registry", log_event="capability_not_found")
    error = CapabilityNotFoundError(request.capability_key)
    response: dict[str, Any] = {
        **error.to_dict(),
        "logs": [f"Capability '{request.capability_key}' not found in registry"],
    }
    await asyncio.to_thread(
        redis_client.cache_response,
        request.turn_id,
        request.capability_key,
        response,
        ttl_seconds=CACHE_TTL_PERMANENT,
    )
    return response


async def execute_handler(
    capability: dict[str, Any],
    request: ToolExecutionRequest,
    logs: list[str],
    session_id: str | None = None,
) -> tuple[dict[str, Any], float]:
    """Execute the capability handler and return outputs with duration."""
    handler = capability["handler"]
    tool_name = capability["tool_name"]
    service = capability["service"]

    # Set Sentry context for this execution
    set_user_context(request.org_id, request.user_id)
    set_capability_context(request.capability_key, service, tool_name)

    # Add breadcrumb for debugging
    add_breadcrumb(
        f"Executing {tool_name}",
        category="execution",
        data={"service": service, "capability": request.capability_key},
    )

    logger.info(
        "Executing handler", tool_name=tool_name, service=service, log_event="handler_start"
    )
    logs.append(f"Executing {tool_name} for org_id={request.org_id}, user_id={request.user_id}")

    handler_start = time.time()
    outputs = await asyncio.to_thread(
        handler, org_id=request.org_id, user_id=request.user_id, args=request.args
    )
    handler_duration_ms = (time.time() - handler_start) * 1000

    logs.append(f"Successfully executed {tool_name}")
    logger.info(
        "Handler execution successful",
        tool_name=tool_name,
        service=service,
        handler_duration_ms=round(handler_duration_ms, 2),
        log_event="handler_success",
    )

    # Track successful capability execution to PostHog
    await asyncio.to_thread(
        track_capability_called,
        user_id=request.user_id,
        org_id=request.org_id,
        capability_key=request.capability_key,
        service=service,
        tool_name=tool_name,
        session_id=session_id,
        duration_ms=handler_duration_ms,
        success=True,
    )

    return outputs, handler_duration_ms


def build_success_response(
    request: ToolExecutionRequest,
    capability: dict[str, Any],
    outputs: dict[str, Any],
    logs: list[str],
) -> dict[str, Any]:
    """Build success response dictionary."""
    return {
        "status": "success",
        "capability_key": request.capability_key,
        "tool_used": capability["tool_name"],
        "outputs": outputs,
        "logs": logs,
        "credential_type": capability.get("credential_type"),
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def handle_stargate_error(
    e: StargateError,
    request: ToolExecutionRequest,
    capability: dict[str, Any] | None,
    logs: list[str],
    start_time: float,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Handle StargateError and return error response."""
    logs.append(f"Stargate error: {e.message}")
    error_dict = e.to_dict()
    error_dict["logs"] = logs
    error_dict["capability_key"] = request.capability_key
    error_dict["tool_used"] = capability["tool_name"] if capability else "unknown"
    error_dict["credential_type"] = capability.get("credential_type") if capability else None
    error_dict["timestamp"] = datetime.now(UTC).isoformat()

    # Enrich CREDENTIALS_MISSING with connect_url so Aleq can send the user to OAuth
    if e.error_code == ErrorCode.CREDENTIALS_MISSING:
        service = capability["service"] if capability else e.details.get("service", "")
        connect_url = build_connect_url(service, request.org_id, request.user_id)
        if connect_url:
            error_dict["connect_url"] = connect_url

    total_duration_ms = (time.time() - start_time) * 1000

    # Capture to Sentry with full context
    service = capability["service"] if capability else "unknown"
    await asyncio.to_thread(
        sentry_capture_connector_error,
        error=e,
        service=service,
        operation=request.capability_key,
        org_id=request.org_id,
        user_id=request.user_id,
        extra={
            "error_code": (
                e.error_code.value if hasattr(e.error_code, "value") else str(e.error_code)
            ),
            "duration_ms": round(total_duration_ms, 2),
        },
    )

    # Track error to PostHog
    error_code_str = e.error_code.value if hasattr(e.error_code, "value") else str(e.error_code)
    await asyncio.to_thread(
        track_connector_error,
        user_id=request.user_id,
        org_id=request.org_id,
        service=service,
        error_code=error_code_str,
        error_message=e.message,
        session_id=session_id,
        capability_key=request.capability_key,
    )

    logger.error(
        "Execute request failed with StargateError",
        error_code=error_code_str,
        error_message=e.message,
        total_duration_ms=round(total_duration_ms, 2),
        log_event="execute_error",
    )
    await asyncio.to_thread(
        redis_client.cache_response,
        request.turn_id,
        request.capability_key,
        error_dict,
        ttl_seconds=get_cache_ttl(error_dict),
    )
    return error_dict


async def handle_unexpected_error(
    e: Exception,
    request: ToolExecutionRequest,
    capability: dict[str, Any] | None,
    logs: list[str],
    start_time: float,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Handle unexpected exceptions and return classified error response."""
    logs.append(f"Unexpected error: {e!s}")
    service = capability["service"] if capability else "unknown"
    classified_error = classify_exception(e, service)

    error_dict = classified_error.to_dict()
    error_dict["logs"] = logs
    error_dict["capability_key"] = request.capability_key
    error_dict["tool_used"] = capability["tool_name"] if capability else "unknown"
    error_dict["credential_type"] = capability.get("credential_type") if capability else None
    error_dict["timestamp"] = datetime.now(UTC).isoformat()

    total_duration_ms = (time.time() - start_time) * 1000

    # Capture to Sentry with full context - unexpected errors are high priority
    await asyncio.to_thread(
        sentry_capture_connector_error,
        error=e,
        service=service,
        operation=request.capability_key,
        org_id=request.org_id,
        user_id=request.user_id,
        extra={
            "error_type": type(e).__name__,
            "classified_code": classified_error.error_code.value
            if hasattr(classified_error.error_code, "value")
            else str(classified_error.error_code),
            "duration_ms": round(total_duration_ms, 2),
        },
    )

    # Track error to PostHog
    error_code_str = (
        classified_error.error_code.value
        if hasattr(classified_error.error_code, "value")
        else str(classified_error.error_code)
    )
    await asyncio.to_thread(
        track_connector_error,
        user_id=request.user_id,
        org_id=request.org_id,
        service=service,
        error_code=error_code_str,
        error_message=str(e)[:200],
        session_id=session_id,
        capability_key=request.capability_key,
    )

    logger.error(
        "Execute request failed with unexpected error",
        error_type=type(e).__name__,
        error_message=str(e)[:200],
        total_duration_ms=round(total_duration_ms, 2),
        log_event="execute_unexpected_error",
        exc_info=True,
    )
    await asyncio.to_thread(
        redis_client.cache_response,
        request.turn_id,
        request.capability_key,
        error_dict,
        ttl_seconds=get_cache_ttl(error_dict),
    )
    return error_dict
