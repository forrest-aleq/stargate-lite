"""
Rate limiter for Stargate Lite using Redis.

Implements sliding window rate limiting per org_id to prevent abuse.
Production-critical: Protects against runaway clients and ensures fair usage.
"""

import asyncio
import os
import time
from typing import Any

from fastapi import HTTPException, Request

from app.logging_config import get_logger

logger = get_logger(__name__)

# Configuration from environment
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # Requests per window
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))  # Window size


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

    def check_rate_limit(self, org_id: str) -> tuple[bool, dict[str, Any]]:
        """
        Check if request is within rate limit.

        Args:
            org_id: Organization identifier

        Returns:
            Tuple of (is_allowed, rate_limit_info)
            rate_limit_info contains: limit, remaining, reset_at
        """
        redis = self._get_redis()
        if not redis:
            # Redis unavailable - allow request but log warning
            return True, {"limit": RATE_LIMIT_REQUESTS, "remaining": -1, "reset_at": 0}

        try:
            now = time.time()
            window_start = now - RATE_LIMIT_WINDOW_SECONDS
            key = f"stargate:ratelimit:{org_id}"

            # Use pipeline for atomic operations
            pipe = redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {f"{now}:{id(now)}": now})

            # Set expiry on key
            pipe.expire(key, RATE_LIMIT_WINDOW_SECONDS + 10)

            results = pipe.execute()
            current_count = results[1]  # zcard result

            remaining = max(0, RATE_LIMIT_REQUESTS - current_count - 1)
            reset_at = int(now + RATE_LIMIT_WINDOW_SECONDS)

            rate_info = {
                "limit": RATE_LIMIT_REQUESTS,
                "remaining": remaining,
                "reset_at": reset_at,
            }

            if current_count >= RATE_LIMIT_REQUESTS:
                logger.warning(
                    "Rate limit exceeded",
                    org_id=org_id,
                    current_count=current_count,
                    limit=RATE_LIMIT_REQUESTS,
                    log_event="rate_limit_exceeded",
                )
                return False, rate_info

            return True, rate_info

        except Exception as e:
            logger.error(
                "Rate limiter error, allowing request",
                org_id=org_id,
                error=str(e),
                log_event="rate_limiter_error",
            )
            # On error, allow request (fail open for availability)
            return True, {"limit": RATE_LIMIT_REQUESTS, "remaining": -1, "reset_at": 0}


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
    except Exception:
        org_id = "unknown"

    is_allowed, rate_info = await asyncio.to_thread(rate_limiter.check_rate_limit, org_id)

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
