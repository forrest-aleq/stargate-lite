"""
Execution service - Helper functions for tool execution.
"""

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from app.circuit_breaker import is_open, record_failure, record_success
from app.constants.services import build_connect_url
from app.errors import (
    CapabilityNotFoundError,
    ErrorCode,
    NetworkError,
    ServiceUnavailableError,
    StargateError,
    classify_exception,
)
from app.logging_config import get_logger
from app.models import ToolExecutionRequest
from app.models_webhook import WebhookEvent
from app.observability import increment_metric
from app.posthog_client import track_capability_called, track_connector_error
from app.redis_client import CACHE_TTL_PERMANENT, get_cache_ttl, redis_client
from app.routers.webhooks.base import emit_delivery_event
from app.sentry_config import (
    add_breadcrumb,
    capture_connector_error as sentry_capture_connector_error,
    set_capability_context,
    set_user_context,
)

logger = get_logger(__name__)

# 5s buffer before Baby MARS's 30s client timeout
HANDLER_TIMEOUT_SECONDS = 25.0

# Background task references — prevents garbage collection of fire-and-forget tasks
_background_tasks: set[asyncio.Task[None]] = set()


async def maybe_emit_delivery_event(
    request: ToolExecutionRequest,
    status: str,
    duration_ms: float,
    error_code: str | None = None,
) -> None:
    """Emit a delivery event for Tier 3 actions (fire-and-forget).

    Called after execution completes (success or failure) when
    verb_tier == 3 in the request metadata.

    Args:
        request: The original execution request.
        status: "sent" for success, "failed" for errors.
        duration_ms: Handler execution duration in ms.
        error_code: Error code string (only for failures).
    """
    verb_tier = (request.metadata or {}).get("verb_tier")
    if verb_tier != 3:
        return

    payload: dict[str, Any] = {
        "capability_key": request.capability_key,
        "status": status,
        "duration_ms": round(duration_ms),
        "proactive": (request.metadata or {}).get("proactive", False),
        "trigger_id": (request.metadata or {}).get("trigger_id"),
        "turn_id": request.turn_id,
    }
    if error_code:
        payload["error_code"] = error_code

    event = WebhookEvent(
        event_type=f"delivery.{request.capability_key}",
        source_service="stargate",
        org_id=request.org_id,
        timestamp=datetime.now(UTC),
        raw_event_id=f"{request.turn_id}:{request.capability_key}",
        user_id=request.user_id,
        payload=payload,
    )

    # Fire-and-forget — delivery event failure doesn't fail execution
    task = asyncio.create_task(emit_delivery_event(event))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


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

    # Extract verb_tier from metadata for metrics tagging
    verb_tier = (request.metadata or {}).get("verb_tier")
    verb_tier_tag = f"verb_tier:{verb_tier if verb_tier is not None else 'unknown'}"

    # Add breadcrumb for debugging
    add_breadcrumb(
        f"Executing {tool_name}",
        category="execution",
        data={"service": service, "capability": request.capability_key, "verb_tier": verb_tier},
    )

    # Circuit breaker check — fast-fail if service is known-bad
    if await asyncio.to_thread(is_open, service):
        raise ServiceUnavailableError(service=service)

    logger.info(
        "Executing handler", tool_name=tool_name, service=service, log_event="handler_start"
    )
    logs.append(f"Executing {tool_name} for org_id={request.org_id}, user_id={request.user_id}")

    handler_start = time.time()
    try:
        outputs = await asyncio.wait_for(
            asyncio.to_thread(
                handler, org_id=request.org_id, user_id=request.user_id, args=request.args
            ),
            timeout=HANDLER_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        handler_duration_ms = (time.time() - handler_start) * 1000
        logger.error(
            "Handler execution timed out",
            tool_name=tool_name,
            service=service,
            handler_duration_ms=round(handler_duration_ms, 2),
            timeout_seconds=HANDLER_TIMEOUT_SECONDS,
            log_event="handler_timeout",
        )
        await asyncio.to_thread(record_failure, service)
        raise NetworkError(service=service) from None
    except StargateError as e:
        if e.error_code in (ErrorCode.NETWORK_ERROR, ErrorCode.RATE_LIMIT):
            await asyncio.to_thread(record_failure, service)
        raise
    handler_duration_ms = (time.time() - handler_start) * 1000

    # Record success to reset circuit breaker
    await asyncio.to_thread(record_success, service)

    logs.append(f"Successfully executed {tool_name}")
    logger.info(
        "Handler execution successful",
        tool_name=tool_name,
        service=service,
        handler_duration_ms=round(handler_duration_ms, 2),
        log_event="handler_success",
    )

    # Track successful capability execution
    increment_metric("stargate_lite.execution.success", tags=[f"service:{service}", verb_tier_tag])
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

    # Track error metrics and PostHog
    error_code_str = e.error_code.value if hasattr(e.error_code, "value") else str(e.error_code)
    verb_tier = (request.metadata or {}).get("verb_tier")
    verb_tier_tag = f"verb_tier:{verb_tier if verb_tier is not None else 'unknown'}"
    increment_metric(
        "stargate_lite.execution.error",
        tags=[f"service:{service}", f"error_code:{error_code_str}", verb_tier_tag],
    )
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
        verb_tier=verb_tier,
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

    # Emit delivery event for Tier 3 failures
    await maybe_emit_delivery_event(request, "failed", total_duration_ms, error_code=error_code_str)

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

    # Track error metrics and PostHog
    error_code_str = (
        classified_error.error_code.value
        if hasattr(classified_error.error_code, "value")
        else str(classified_error.error_code)
    )
    verb_tier = (request.metadata or {}).get("verb_tier")
    verb_tier_tag = f"verb_tier:{verb_tier if verb_tier is not None else 'unknown'}"
    increment_metric(
        "stargate_lite.execution.error",
        tags=[f"service:{service}", f"error_code:{error_code_str}", verb_tier_tag],
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
        verb_tier=verb_tier,
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

    # Emit delivery event for Tier 3 failures
    await maybe_emit_delivery_event(request, "failed", total_duration_ms, error_code=error_code_str)

    return error_dict
