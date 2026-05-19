"""
Redis-backed circuit breaker for external service calls.

Prevents cascading failures when a downstream service is down by fast-failing
requests once a failure threshold is reached.

State machine:
  CLOSED  -> requests pass; failures counted in rolling window
  OPEN    -> fast-fail with ServiceUnavailableError
  HALF_OPEN -> allow 1 probe; success -> CLOSED, failure -> OPEN
"""

import os
import time

from app.logging_config import get_logger
from app.redis_client import redis_client

logger = get_logger(__name__)

# Configurable thresholds (env vars with sensible defaults)
FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_FAILURE_THRESHOLD", "5"))
FAILURE_WINDOW = int(os.getenv("CIRCUIT_FAILURE_WINDOW", "60"))
RECOVERY_TIMEOUT = int(os.getenv("CIRCUIT_RECOVERY_TIMEOUT", "30"))

# Circuit states
STATE_CLOSED = "closed"
STATE_OPEN = "open"
STATE_HALF_OPEN = "half_open"


def _key(service: str) -> str:
    return f"stargate:circuit:{service}"


def is_open(service: str) -> bool:
    """Check if circuit is open (should fast-fail).

    Returns False (allow request) if Redis is unavailable — fail open.
    """
    client = redis_client._redis_client
    if not client:
        return False

    try:
        data = client.hgetall(_key(service))
        if not data:
            return False

        state = data.get("state", STATE_CLOSED)

        if state == STATE_OPEN:
            opened_at = float(data.get("opened_at", "0"))
            if time.time() - opened_at >= RECOVERY_TIMEOUT:
                # Transition to half-open: allow one probe
                client.hset(_key(service), "state", STATE_HALF_OPEN)
                logger.info(
                    "Circuit transitioning to half-open",
                    service=service,
                    log_event="circuit_half_open",
                )
                return False
            return True

        return False
    except Exception:
        # Redis error — fail open (allow the request)
        return False


def record_failure(service: str) -> None:
    """Record a failure for a service. Opens circuit if threshold exceeded."""
    client = redis_client._redis_client
    if not client:
        return

    try:
        key = _key(service)
        now = time.time()
        pipe = client.pipeline()

        # Increment failure count and update timestamp
        pipe.hincrby(key, "failure_count", 1)
        pipe.hset(key, "last_failure_at", str(now))
        results = pipe.execute()

        failure_count = int(results[0])

        # Check window — only count failures within the window
        data = client.hgetall(key)
        state = data.get("state", STATE_CLOSED)

        if state == STATE_HALF_OPEN:
            # Probe failed — re-open
            client.hset(
                key,
                mapping={
                    "state": STATE_OPEN,
                    "opened_at": str(now),
                },
            )
            # TTL = window + recovery + buffer
            client.expire(key, FAILURE_WINDOW + RECOVERY_TIMEOUT + 60)
            logger.warning(
                "Circuit re-opened after half-open probe failure",
                service=service,
                log_event="circuit_reopened",
            )
            return

        if failure_count >= FAILURE_THRESHOLD:
            # Open the circuit
            client.hset(
                key,
                mapping={
                    "state": STATE_OPEN,
                    "opened_at": str(now),
                },
            )
            # TTL = window + recovery + buffer
            client.expire(key, FAILURE_WINDOW + RECOVERY_TIMEOUT + 60)
            logger.warning(
                "Circuit opened for service",
                service=service,
                failure_count=failure_count,
                log_event="circuit_opened",
            )
        else:
            # Keep the key alive for the failure window
            client.expire(key, FAILURE_WINDOW)
    except Exception:
        # Redis error — don't affect request flow
        logger.debug("Circuit breaker record_failure redis error", exc_info=True)


def record_success(service: str) -> None:
    """Record a success. Resets circuit to closed."""
    client = redis_client._redis_client
    if not client:
        return

    try:
        key = _key(service)
        data = client.hgetall(key)
        if not data:
            return

        state = data.get("state", STATE_CLOSED)
        if state in (STATE_HALF_OPEN, STATE_OPEN):
            # Reset to closed
            client.delete(key)
            logger.info(
                "Circuit closed after successful request",
                service=service,
                previous_state=state,
                log_event="circuit_closed",
            )
        elif state == STATE_CLOSED:
            # Decrement failure count on success to keep window accurate
            current = int(data.get("failure_count", "0"))
            if current > 0:
                client.hincrby(key, "failure_count", -1)
    except Exception:
        logger.debug("Circuit breaker record_success redis error", exc_info=True)
