"""
Webhook forwarding infrastructure.

Handles forwarding normalized webhook events from Stargate to Baby MARS's
/webhooks/stargate endpoint with dedup, retry, and graceful degradation.

Auth: X-API-Key header (same shared key as /api/v1/execute).
Durability: Redis stream write BEFORE forwarding, DLQ on exhausted retries.
"""

import asyncio
import os

import requests
from fastapi import APIRouter

from app.logging_config import get_logger
from app.models_webhook import WebhookEvent
from app.observability import increment_metric
from app.redis_client import redis_client

logger = get_logger(__name__)
router = APIRouter()

# Baby MARS target — points to /webhooks/stargate on the Baby MARS instance
BABY_MARS_WEBHOOK_URL = os.getenv("BABY_MARS_WEBHOOK_URL", "")


def _get_baby_mars_api_key() -> str:
    """Resolve explicit Baby MARS webhook auth key with safe fallback."""
    return (
        os.getenv("BABY_MARS_WEBHOOK_API_KEY", "")
        or os.getenv("API_SECRET_KEY", "")
    )

# Dedup TTL: 24 hours
_DEDUP_TTL_SECONDS = 86400

# Redis keys
_STREAM_KEY = "stargate:webhooks:outbound"
_DLQ_KEY = "stargate:dlq:webhooks"

# Retry backoff schedule: 1s, 2s, 4s (contract v1.0)
_BACKOFF_SECONDS = [1, 2, 4]

# HTTP session for forwarding (reuse connections)
_forward_session: requests.Session | None = None


def _get_forward_session() -> requests.Session:
    """Lazy-init a requests session for forwarding."""
    global _forward_session
    if _forward_session is None:
        _forward_session = requests.Session()
    return _forward_session


async def forward_to_baby_mars(event: WebhookEvent) -> bool:
    """Forward normalized event to Baby MARS.

    1. Dedup by raw_event_id (skip if already forwarded).
    2. Write to Redis stream (durability — survives restart).
    3. Forward via HTTP POST with X-API-Key auth.
    4. Retry 3x with backoff (1s, 2s, 4s) = 4 total attempts.
    5. Dead letter queue on exhausted retries.

    Graceful no-op if BABY_MARS_WEBHOOK_URL is not set.
    """
    if not BABY_MARS_WEBHOOK_URL:
        logger.warning(
            "BABY_MARS_WEBHOOK_URL not set, event logged only",
            event_type=event.event_type,
            source_service=event.source_service,
            raw_event_id=event.raw_event_id,
            log_event="webhook_forward_skip",
        )
        return False

    # 1. Dedup check
    dedup_key = f"stargate:webhook:seen:{event.source_service}:{event.raw_event_id}"
    already_seen = await asyncio.to_thread(redis_client.get_cached_response, dedup_key, "")
    if already_seen:
        logger.info(
            "Duplicate webhook event, skipping",
            raw_event_id=event.raw_event_id,
            source_service=event.source_service,
            log_event="webhook_dedup",
        )
        return True

    # 2. Write to Redis stream BEFORE forwarding (durability)
    body = event.model_dump(mode="json")
    await asyncio.to_thread(redis_client.xadd_event, _STREAM_KEY, body)

    # 3. Forward with X-API-Key (same auth as /api/v1/execute)
    # 1 initial attempt + 3 retries = 4 total attempts, backoff 1s/2s/4s
    session = _get_forward_session()
    max_attempts = len(_BACKOFF_SECONDS) + 1

    for attempt in range(max_attempts):
        try:
            resp = await asyncio.to_thread(
                session.post,
                BABY_MARS_WEBHOOK_URL,
                json=body,
                headers={"X-API-Key": _get_baby_mars_api_key()},
                timeout=10,
            )

            if resp.status_code < 500:
                # Mark as processed (even 4xx — don't retry client errors)
                await asyncio.to_thread(
                    redis_client.cache_response,
                    dedup_key,
                    "",
                    {"seen": True},
                    ttl_seconds=_DEDUP_TTL_SECONDS,
                )
                increment_metric(
                    "stargate_lite.webhook.forwarded",
                    tags=[
                        f"source_service:{event.source_service}",
                        f"event_type:{event.event_type}",
                    ],
                )
                logger.info(
                    "Webhook forwarded to Baby MARS",
                    event_type=event.event_type,
                    source_service=event.source_service,
                    raw_event_id=event.raw_event_id,
                    status_code=resp.status_code,
                    log_event="webhook_forward_success",
                )
                return True

            # 5xx — retry
            logger.warning(
                "Baby MARS returned server error, retrying",
                status_code=resp.status_code,
                attempt=attempt + 1,
                log_event="webhook_forward_retry",
            )
        except Exception:
            logger.warning(
                "Webhook forward attempt failed",
                attempt=attempt + 1,
                event_type=event.event_type,
                log_event="webhook_forward_attempt_failed",
                exc_info=True,
            )

        # Backoff before next attempt (skip after final attempt)
        if attempt < len(_BACKOFF_SECONDS):
            await asyncio.sleep(_BACKOFF_SECONDS[attempt])

    # 4. Exhausted retries — push to dead letter queue
    await asyncio.to_thread(redis_client.lpush_event, _DLQ_KEY, body)

    increment_metric(
        "stargate_lite.webhook.dead_letter",
        tags=[f"source_service:{event.source_service}"],
    )
    logger.error(
        "Webhook forward exhausted retries, pushed to DLQ",
        event_type=event.event_type,
        raw_event_id=event.raw_event_id,
        source_service=event.source_service,
        dlq_key=_DLQ_KEY,
        log_event="webhook_forward_dead_letter",
    )
    return False


async def emit_delivery_event(event: WebhookEvent) -> None:
    """Fire-and-forget delivery event to Baby MARS.

    Used by Tier 3 execution to report sent/failed status.
    Failure to emit does NOT fail the execution.
    """
    try:
        await forward_to_baby_mars(event)
    except Exception:
        logger.error(
            "Failed to emit delivery event",
            event_type=event.event_type,
            raw_event_id=event.raw_event_id,
            log_event="delivery_event_emit_failed",
            exc_info=True,
        )
