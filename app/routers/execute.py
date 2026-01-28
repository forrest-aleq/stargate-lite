"""
Tool execution routes for Stargate Lite.
"""

import time
from typing import Any

from fastapi import APIRouter, Depends, Header, Response

from app.auth import verify_api_key
from app.errors import StargateError
from app.logging_config import bind_request_context, clear_request_context, get_logger
from app.models import ErrorResponse, ToolExecutionRequest
from app.rate_limiter import rate_limiter
from app.redis_client import redis_client
from app.registry import get_capability
from app.services.execution import (
    build_success_response,
    check_idempotency_cache,
    execute_handler,
    handle_capability_not_found,
    handle_stargate_error,
    handle_unexpected_error,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["execute"])

# Response models for OpenAPI documentation
EXECUTE_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Successful execution or error (Stargate always returns 200)",
        "content": {
            "application/json": {
                "schema": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/ToolExecutionResponse"},
                        {"$ref": "#/components/schemas/ErrorResponse"},
                    ],
                    "discriminator": {
                        "propertyName": "status",
                        "mapping": {
                            "success": "#/components/schemas/ToolExecutionResponse",
                            "error": "#/components/schemas/ErrorResponse",
                        },
                    },
                }
            }
        },
    },
    429: {
        "description": "Rate limit exceeded",
        "model": ErrorResponse,
    },
}


@router.post("/execute", responses=EXECUTE_RESPONSES)
async def execute_tool(
    request: ToolExecutionRequest,
    response: Response,
    _: bool = Depends(verify_api_key),
    x_session_id: str | None = Header(None, alias="X-Session-ID"),
) -> dict[str, Any]:
    """
    Execute a tool based on capability_key.

    This is the MAIN endpoint that the Brain (MARS) calls.
    Supports idempotency via turn_id with 24-hour cache.
    Session ID can be passed via X-Session-ID header or session_id body field.

    **Response Format (Contract v1.0):**
    - Success: `{"status": "success", "capability_key": "...", "outputs": {...}}`
    - Error: `{"status": "error", "error_code": "...", "error_message": "..."}`

    Rate limited: 100 requests per minute per org_id (configurable via env vars).
    """
    logs: list[str] = []
    capability: dict[str, Any] | None = None
    start_time = time.time()

    # Use header if provided, else fall back to body field
    session_id = x_session_id or request.session_id

    bind_request_context(
        org_id=request.org_id,
        user_id=request.user_id,
        capability_key=request.capability_key,
        turn_id=request.turn_id,
        session_id=session_id,
    )
    logger.info("Execute request received", log_event="execute_start")

    # Rate limiting check
    is_allowed, rate_info = rate_limiter.check_rate_limit(request.org_id)

    # Add rate limit headers to response
    response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(rate_info["reset_at"])

    if not is_allowed:
        retry_after = max(1, rate_info["reset_at"] - int(time.time()))
        response.headers["Retry-After"] = str(retry_after)
        response.status_code = 429
        logger.warning(
            "Rate limit exceeded",
            org_id=request.org_id,
            log_event="rate_limit_rejected",
        )
        return {
            "status": "error",
            "error_code": "RATE_LIMIT",
            "error_message": f"Rate limit exceeded. Retry after {retry_after} seconds.",
            "retry_strategy": "backoff",
            "details": {
                "limit": rate_info["limit"],
                "retry_after_seconds": retry_after,
            },
            "capability_key": request.capability_key,
            "turn_id": request.turn_id,
        }

    try:
        cached = check_idempotency_cache(request.turn_id, request.capability_key)
        if cached:
            return cached

        capability = get_capability(request.capability_key)
        if not capability:
            return handle_capability_not_found(request)

        logs.append(
            f"Resolved capability '{request.capability_key}' to tool '{capability['tool_name']}'"
        )

        outputs, _duration = execute_handler(capability, request, logs, session_id)
        response_data = build_success_response(request, capability, outputs, logs)

        redis_client.cache_response(request.turn_id, request.capability_key, response_data)
        total_duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Execute request completed successfully",
            tool_name=capability["tool_name"],
            service=capability["service"],
            total_duration_ms=round(total_duration_ms, 2),
            log_event="execute_success",
        )
        return response_data

    except StargateError as e:
        return handle_stargate_error(e, request, capability, logs, start_time, session_id)
    except Exception as e:
        return handle_unexpected_error(e, request, capability, logs, start_time, session_id)
    finally:
        clear_request_context()
