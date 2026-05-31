"""Org-scoped execution idempotency helpers."""

import asyncio
from typing import Any

from app.errors import ErrorCode
from app.logging_config import get_logger
from app.models import ToolExecutionRequest
from app.redis_client import get_cache_ttl, redis_client

logger = get_logger(__name__)


def is_idempotency_available() -> bool:
    """Return whether execute idempotency storage is currently usable."""
    return redis_client.is_available()


def build_idempotency_unavailable_response(request: ToolExecutionRequest) -> dict[str, Any]:
    """Build a fail-closed response when execution idempotency is unavailable."""
    return {
        "status": "error",
        "error_code": ErrorCode.NETWORK_ERROR.value,
        "error_message": (
            "Stargate idempotency storage is unavailable; refusing execution to prevent "
            "duplicate side effects."
        ),
        "retry_strategy": "backoff",
        "details": {"dependency": "redis", "reason": "idempotency_unavailable"},
        "capability_key": request.capability_key,
        "turn_id": request.turn_id,
    }


def build_execution_in_progress_response(request: ToolExecutionRequest) -> dict[str, Any]:
    """Build a duplicate-safe response when the same idempotency key is in flight."""
    return {
        "status": "error",
        "error_code": ErrorCode.NETWORK_ERROR.value,
        "error_message": (
            "Stargate is already executing this idempotency key; retry to read the cached result."
        ),
        "retry_strategy": "backoff",
        "details": {"reason": "execution_in_progress", "retry_after_seconds": 1},
        "capability_key": request.capability_key,
        "turn_id": request.turn_id,
    }


async def check_idempotency_cache(
    org_id: str, turn_id: str, capability_key: str
) -> dict[str, Any] | None:
    """Check the org-scoped Redis cache for an existing execution response."""
    cached = await asyncio.to_thread(
        redis_client.get_cached_execution_response,
        org_id=org_id,
        turn_id=turn_id,
        capability_key=capability_key,
    )
    if cached:
        logger.info("Returning cached response", log_event="cache_hit")
    return cached


async def acquire_idempotency_lock(request: ToolExecutionRequest) -> bool:
    """Acquire the org-scoped execution lock for this idempotency key."""
    return await asyncio.to_thread(
        redis_client.acquire_execution_lock,
        request.org_id,
        request.turn_id,
        request.capability_key,
    )


async def release_idempotency_lock(request: ToolExecutionRequest) -> None:
    """Release the org-scoped execution lock for this idempotency key."""
    await asyncio.to_thread(
        redis_client.release_execution_lock,
        request.org_id,
        request.turn_id,
        request.capability_key,
    )


async def cache_idempotency_response(
    request: ToolExecutionRequest, response: dict[str, Any]
) -> None:
    """Cache an execution response using the org-scoped idempotency key."""
    await asyncio.to_thread(
        redis_client.cache_execution_response,
        request.org_id,
        request.turn_id,
        request.capability_key,
        response,
        ttl_seconds=get_cache_ttl(response),
    )
