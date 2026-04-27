"""
Redis client for idempotency caching
Prevents duplicate tool executions on retries (critical for production safety)
"""

import json
import os
from typing import Any, cast

import redis

from app.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Cache TTL constants (seconds)
CACHE_TTL_SUCCESS = 86400  # 24 hours — success responses are safe to cache long
CACHE_TTL_TRANSIENT = 300  # 5 minutes — transient errors (rate limits, timeouts)
CACHE_TTL_PERMANENT = 86400  # 24 hours — permanent errors (not found, auth)


def get_cache_ttl(response: dict[str, Any]) -> int:
    """Return appropriate cache TTL based on response retry_strategy.

    Transient errors (retry_strategy == "backoff") get a short TTL so the client
    can retry after the backoff period.  Everything else caches for 24 hours.
    """
    if response.get("retry_strategy") == "backoff":
        return CACHE_TTL_TRANSIENT
    return CACHE_TTL_SUCCESS


class RedisClient:
    """Redis client singleton for idempotency caching"""

    _instance: "RedisClient | None" = None
    _redis_client: "redis.Redis[str] | None" = None

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize Redis connection (supports Upstash via REDIS_URL)"""
        # Prefer REDIS_URL (Upstash/Railway format) over individual vars
        redis_url = os.getenv("REDIS_URL")

        try:
            if redis_url:
                # Use URL format (e.g., rediss://default:token@host:port)
                # Upstash uses rediss:// (TLS) by default
                logger.info(
                    "Initializing Redis via URL",
                    redis_url=redis_url[:30] + "...",  # Truncate for security
                    log_event="redis_init_start",
                )
                self._redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
            else:
                # Fall back to individual env vars (local dev)
                redis_host = os.getenv("REDIS_HOST", "localhost")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                redis_db = int(os.getenv("REDIS_DB", "0"))
                redis_password = os.getenv("REDIS_PASSWORD", None)

                logger.info(
                    "Initializing Redis via host/port",
                    redis_host=redis_host,
                    redis_port=redis_port,
                    redis_db=redis_db,
                    log_event="redis_init_start",
                )
                self._redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )

            # Test connection
            self._redis_client.ping()
            logger.info(
                "Redis connected successfully",
                log_event="redis_init_success",
            )
        except redis.RedisError as e:
            self._redis_client = None
            logger.error(
                "Redis connection unavailable; continuing without idempotency cache",
                error_type=type(e).__name__,
                log_event="redis_init_error",
                exc_info=True,
            )

    def get_cached_response(self, turn_id: str, capability_key: str) -> dict[str, Any] | None:
        """
        Get cached response for a turn_id + capability_key combination

        Args:
            turn_id: Turn ID from MARS
            capability_key: Capability being executed

        Returns:
            Cached response dict or None if not found
        """
        if not self._redis_client:
            return None

        try:
            # Cache key includes capability_key to handle turn_id reuse edge case
            cache_key = f"stargate:idempotency:{turn_id}:{capability_key}"
            cached_data = self._redis_client.get(cache_key)

            if cached_data:
                logger.info(
                    "Cache hit - returning cached response",
                    turn_id=turn_id,
                    capability_key=capability_key,
                    log_event="cache_hit",
                )
                return cast(dict[str, Any], json.loads(cached_data))

            logger.debug(
                "Cache miss", turn_id=turn_id, capability_key=capability_key, log_event="cache_miss"
            )
            return None
        except Exception as e:
            logger.error(
                "Redis get error",
                turn_id=turn_id,
                capability_key=capability_key,
                error_type=type(e).__name__,
                log_event="cache_get_error",
                exc_info=True,
            )
            return None

    def cache_response(
        self,
        turn_id: str,
        capability_key: str,
        response: dict[str, Any],
        ttl_seconds: int = 86400,  # 24 hours default
    ) -> bool:
        """
        Cache a response for a turn_id + capability_key combination

        Args:
            turn_id: Turn ID from MARS
            capability_key: Capability that was executed
            response: Response dict to cache
            ttl_seconds: Time to live in seconds (default 24 hours)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self._redis_client:
            return False

        try:
            cache_key = f"stargate:idempotency:{turn_id}:{capability_key}"
            serialized = json.dumps(response)

            self._redis_client.setex(name=cache_key, time=ttl_seconds, value=serialized)

            logger.info(
                "Response cached successfully",
                turn_id=turn_id,
                capability_key=capability_key,
                ttl_seconds=ttl_seconds,
                response_size_bytes=len(serialized),
                log_event="cache_set_success",
            )
            return True
        except Exception as e:
            logger.error(
                "Redis set error",
                turn_id=turn_id,
                capability_key=capability_key,
                error_type=type(e).__name__,
                log_event="cache_set_error",
                exc_info=True,
            )
            return False

    def xadd_event(self, stream_key: str, fields: dict[str, Any]) -> str | None:
        """Write event to Redis stream for durability.

        Returns the stream entry ID on success, None on failure.
        """
        if not self._redis_client:
            return None

        try:
            # Serialize any non-string values to JSON strings for Redis streams
            serialized: dict[str, str] = {
                k: v if isinstance(v, str) else json.dumps(v) for k, v in fields.items()
            }
            entry_id: str = self._redis_client.xadd(stream_key, serialized)
            logger.debug(
                "Event written to stream",
                stream_key=stream_key,
                entry_id=entry_id,
                log_event="stream_xadd_success",
            )
            return entry_id
        except Exception as e:
            logger.error(
                "Redis stream write failed",
                stream_key=stream_key,
                error_type=type(e).__name__,
                log_event="stream_xadd_error",
                exc_info=True,
            )
            return None

    def lpush_event(self, list_key: str, data: dict[str, Any]) -> bool:
        """Push event to a Redis list (used for dead letter queue)."""
        if not self._redis_client:
            return False

        try:
            serialized = json.dumps(data)
            self._redis_client.lpush(list_key, serialized)
            logger.debug(
                "Event pushed to list",
                list_key=list_key,
                log_event="list_lpush_success",
            )
            return True
        except Exception as e:
            logger.error(
                "Redis list push failed",
                list_key=list_key,
                error_type=type(e).__name__,
                log_event="list_lpush_error",
                exc_info=True,
            )
            return False

    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self._redis_client is not None


# Global singleton instance
redis_client = RedisClient()
