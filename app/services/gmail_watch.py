"""
Gmail watch management.

Tracks watch expiry in Redis and provides helpers to check if renewal
is needed. The actual watch setup is done via the email.setup_watch
capability (already in registry).

Watch lifecycle:
1. Baby MARS calls email.setup_watch → Gmail API → returns expiration
2. Stargate stores expiry in Redis: stargate:gmail:watch:{org_id}:{user_id}
3. Baby MARS (or cron) calls check_watch_renewal_needed to know if renewal
   is due (watches expire after 7 days, renew at 6 days)
4. If needed, Baby MARS calls email.setup_watch again

The push notification receiver (webhooks/gmail.py) handles inbound events.
"""

from typing import Any

from app.logging_config import get_logger
from app.redis_client import redis_client

logger = get_logger(__name__)

# Redis key prefix for watch expiry tracking
_WATCH_KEY_PREFIX = "stargate:gmail:watch"

# Renew watches 1 day before expiry (6 days into 7-day window)
_RENEWAL_BUFFER_MS = 86_400_000  # 24 hours in milliseconds


def store_watch_expiry(org_id: str, user_id: str, expiration_ms: int) -> None:
    """Store Gmail watch expiry timestamp in Redis.

    Called after a successful email.setup_watch execution.

    Args:
        org_id: Organization ID.
        user_id: User ID.
        expiration_ms: Watch expiration timestamp in epoch milliseconds
                       (as returned by Gmail API).
    """
    key = f"{_WATCH_KEY_PREFIX}:{org_id}:{user_id}"
    redis_client.cache_response(
        key,
        "",
        {"expiration_ms": expiration_ms},
        ttl_seconds=604800,  # 7 days — same as watch lifetime
    )
    logger.info(
        "Stored Gmail watch expiry",
        org_id=org_id,
        user_id=user_id,
        expiration_ms=expiration_ms,
        log_event="gmail_watch_expiry_stored",
    )


def check_watch_renewal_needed(org_id: str, user_id: str, current_time_ms: int) -> dict[str, Any]:
    """Check if a Gmail watch needs renewal.

    Returns a dict with:
    - needs_renewal: True if watch is expired or near expiry
    - expiration_ms: Current stored expiry (0 if not found)
    - reason: Why renewal is needed (or "active" if not)
    """
    key = f"{_WATCH_KEY_PREFIX}:{org_id}:{user_id}"
    result = redis_client.get_cached_response(key, "")

    if not result or not isinstance(result, dict):
        return {
            "needs_renewal": True,
            "expiration_ms": 0,
            "reason": "no_watch_found",
        }

    expiration_ms = int(result.get("expiration_ms", 0))

    if current_time_ms >= expiration_ms:
        return {
            "needs_renewal": True,
            "expiration_ms": expiration_ms,
            "reason": "expired",
        }

    if current_time_ms >= expiration_ms - _RENEWAL_BUFFER_MS:
        return {
            "needs_renewal": True,
            "expiration_ms": expiration_ms,
            "reason": "near_expiry",
        }

    return {
        "needs_renewal": False,
        "expiration_ms": expiration_ms,
        "reason": "active",
    }
