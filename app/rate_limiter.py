"""
Rate limiter for Stargate Lite using Redis.

Implements sliding window rate limiting per org_id to prevent abuse.
Production-critical: Protects against runaway clients and ensures fair usage.
"""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request

from app.logging_config import get_logger
from app.schemas import get_schema

logger = get_logger(__name__)

# Configuration from environment
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # Requests per window
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))  # Window size
RATE_LIMIT_READ_REQUESTS = int(
    os.getenv("RATE_LIMIT_READ_REQUESTS", str(max(RATE_LIMIT_REQUESTS, 240)))
)
RATE_LIMIT_READ_WINDOW_SECONDS = int(
    os.getenv("RATE_LIMIT_READ_WINDOW_SECONDS", str(RATE_LIMIT_WINDOW_SECONDS))
)


@dataclass(frozen=True)
class RateLimitPolicy:
    """Resolved rate-limit policy for a request."""

    bucket: str
    limit: int
    window_seconds: int


class RateLimiter:
    """
    Redis-based sliding window rate limiter.

    Limits requests per org_id to prevent abuse and ensure fair usage.
    Uses Redis sorted sets for efficient sliding window implementation.
    """

    def __init__(self) -> None:
        self._redis: Any = None
        self._initialized = False

    def _get_redis(self) -> Any:
        """Lazy initialization of Redis connection."""
        if not self._initialized:
            try:
                from app.redis_client import redis_client

                self._redis = redis_client._redis_client
                self._initialized = True
            except Exception as e:
                logger.warning(
                    "Rate limiter Redis unavailable, rate limiting disabled",
                    error=str(e),
                    log_event="rate_limiter_redis_unavailable",
                )
                self._initialized = True
        return self._redis

    def _resolve_policy(
        self,
        capability_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RateLimitPolicy:
        """Choose the appropriate rate-limit bucket for a request."""
        if capability_key:
            schema = get_schema(capability_key)
            if schema and schema.idempotent and not schema.has_side_effects:
                return RateLimitPolicy(
                    bucket="read",
                    limit=RATE_LIMIT_READ_REQUESTS,
                    window_seconds=RATE_LIMIT_READ_WINDOW_SECONDS,
                )

        verb_tier = (metadata or {}).get("verb_tier")
        if verb_tier == 0:
            return RateLimitPolicy(
                bucket="read",
                limit=RATE_LIMIT_READ_REQUESTS,
                window_seconds=RATE_LIMIT_READ_WINDOW_SECONDS,
            )

        return RateLimitPolicy(
            bucket="default",
            limit=RATE_LIMIT_REQUESTS,
            window_seconds=RATE_LIMIT_WINDOW_SECONDS,
        )

    @staticmethod
    def _compute_reset_at(
        redis: Any,
        key: str,
        now: float,
        window_seconds: int,
    ) -> int:
        """Compute reset time from the oldest item still in the window."""
        try:
            oldest_entries = redis.zrange(key, 0, 0, withscores=True)
        except Exception:
            return int(now + window_seconds)

        if not oldest_entries:
            return int(now + window_seconds)

        oldest_score = oldest_entries[0][1]
        try:
            return int(max(now, float(oldest_score) + window_seconds))
        except (TypeError, ValueError):
            return int(now + window_seconds)

    def check_rate_limit(
        self,
        org_id: str,
        capability_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if request is within rate limit.

        Args:
            org_id: Organization identifier
            capability_key: Capability being executed
            metadata: Execution metadata from caller

        Returns:
            Tuple of (is_allowed, rate_limit_info)
            rate_limit_info contains: limit, remaining, reset_at, bucket
        """
        redis = self._get_redis()
        policy = self._resolve_policy(capability_key=capability_key, metadata=metadata)
        if not redis:
            # Redis unavailable - allow request but log warning
            return True, {
                "bucket": policy.bucket,
                "limit": policy.limit,
                "remaining": -1,
                "reset_at": 0,
            }

        try:
            now = time.time()
            window_start = now - policy.window_seconds
            key = f"stargate:ratelimit:{org_id}:{policy.bucket}"

            # Prune before evaluating. Denied requests must NOT extend the window.
            redis.zremrangebyscore(key, 0, window_start)
            current_count = int(redis.zcard(key))

            if current_count >= policy.limit:
                reset_at = self._compute_reset_at(redis, key, now, policy.window_seconds)
                rate_info = {
                    "bucket": policy.bucket,
                    "limit": policy.limit,
                    "remaining": 0,
                    "reset_at": reset_at,
                }
                logger.warning(
                    "Rate limit exceeded",
                    org_id=org_id,
                    capability_key=capability_key,
                    bucket=policy.bucket,
                    current_count=current_count,
                    limit=policy.limit,
                    log_event="rate_limit_exceeded",
                )
                return False, rate_info

            request_token = f"{now}:{time.monotonic_ns()}"
            redis.zadd(key, {request_token: now})
            redis.expire(key, policy.window_seconds + 10)

            remaining = max(0, policy.limit - current_count - 1)
            reset_at = self._compute_reset_at(redis, key, now, policy.window_seconds)

            rate_info = {
                "bucket": policy.bucket,
                "limit": policy.limit,
                "remaining": remaining,
                "reset_at": reset_at,
            }

            return True, rate_info

        except Exception as e:
            logger.error(
                "Rate limiter error, allowing request",
                org_id=org_id,
                capability_key=capability_key,
                bucket=policy.bucket,
                error=str(e),
                log_event="rate_limiter_error",
            )
            # On error, allow request (fail open for availability)
            return True, {
                "bucket": policy.bucket,
                "limit": policy.limit,
                "remaining": -1,
                "reset_at": 0,
            }


# Global singleton
rate_limiter = RateLimiter()


async def check_rate_limit_dependency(request: Request) -> None:
    """
    FastAPI dependency for rate limiting.

    Extracts org_id from request body and checks rate limit.
    Raises HTTPException(429) if rate limit exceeded.
    """
    try:
        # Parse body to get org_id
        body = await request.json()
        org_id = body.get("org_id", "unknown")
        capability_key = body.get("capability_key")
        metadata = body.get("metadata")
    except Exception:
        org_id = "unknown"
        capability_key = None
        metadata = None

    is_allowed, rate_info = await asyncio.to_thread(
        rate_limiter.check_rate_limit,
        org_id,
        capability_key,
        metadata,
    )

    # Add rate limit headers to response (will be picked up by middleware or response)
    request.state.rate_limit_info = rate_info

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "error_code": "RATE_LIMIT",
                "retry_after_seconds": rate_info["reset_at"] - int(time.time()),
                "limit": rate_info["limit"],
            },
            headers={
                "Retry-After": str(rate_info["reset_at"] - int(time.time())),
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset_at"]),
            },
        )
