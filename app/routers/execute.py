"""
Tool execution routes for Stargate Lite.
"""

import time
from typing import Any

from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.errors import StargateError
from app.logging_config import bind_request_context, clear_request_context, get_logger
from app.models import ToolExecutionRequest
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


@router.post("/execute")
async def execute_tool(
    request: ToolExecutionRequest, _: bool = Depends(verify_api_key)
) -> dict[str, Any]:
    """
    Execute a tool based on capability_key.

    This is the MAIN endpoint that the Brain (MARS) calls.
    Supports idempotency via turn_id with 24-hour cache.
    """
    logs: list[str] = []
    capability: dict[str, Any] | None = None
    start_time = time.time()

    bind_request_context(
        org_id=request.org_id,
        user_id=request.user_id,
        capability_key=request.capability_key,
        turn_id=request.turn_id,
    )
    logger.info("Execute request received", log_event="execute_start")

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

        outputs, _duration = execute_handler(capability, request, logs)
        response = build_success_response(request, capability, outputs, logs)

        redis_client.cache_response(request.turn_id, request.capability_key, response)
        total_duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Execute request completed successfully",
            tool_name=capability["tool_name"],
            service=capability["service"],
            total_duration_ms=round(total_duration_ms, 2),
            log_event="execute_success",
        )
        return response

    except StargateError as e:
        return handle_stargate_error(e, request, capability, logs, start_time)
    except Exception as e:
        return handle_unexpected_error(e, request, capability, logs, start_time)
    finally:
        clear_request_context()
