"""
Webhook forwarding infrastructure.

Handles forwarding normalized webhook events from Stargate to Baby MARS's
/webhooks/stargate endpoint with dedup, retry, and graceful degradation.

Auth: X-API-Key header (same shared key as /api/v1/execute).
"""

import asyncio
import os
import time
from typing import Any

import requests

from app.logging_config import get_logger
from app.models_webhook import WebhookEvent
from app.observability import increment_metric
from app.redis_client import redis_client

from fastapi import APIRouter

logger = get_logger(__name__)
router = APIRouter()

# Baby MARS target — points to /webhooks/stargate on the Baby MARS instance
BABY_MARS_WEBHOOK_URL = os.getenv("BABY_MARS_WEBHOOK_URL", "")
BABY_MARS_API_KEY = os.getenv("API_SECRET_KEY", "")

# Dedup TTL: 24 hours
_DEDUP_TTL_SECONDS = 86400

# HTTP session for forwarding (reuse connections)
_forward_session: requests.Session | None = None


def _get_forward_session() -> requests.Session:
    """Lazy-init a requests session for forwarding."""
    global _forward_session  # noqa: PLW0603
    if _forward_session is None:
        _forward_session = requests.Session()
    return _forward_session


async def forward_to_baby_mars(event: WebhookEvent) -> bool:
    """Forward normalized event to Baby MARS.

    1. Dedup by raw_event_id (skip if already forwarded).
    2. Forward via HTTP POST with X-API-Key auth.
    3. Retry 3x with exponential backoff (1s, 2s, 4s).
    4. Returns True on success or dedup, False on exhausted retries.

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
    already_seen = await asyncio.to_thread(
        redis_client.get_cached_response, dedup_key, ""
    )
    if already_seen:
        logger.info(
            "Duplicate webhook event, skipping",
            raw_event_id=event.raw_event_id,
            source_service=event.source_service,
            log_event="webhook_dedup",
        )
        return True

    # 2. Forward with X-API-Key (same auth as /api/v1/execute)
    session = _get_forward_session()
    body = event.model_dump(mode="json")

    for attempt in range(3):
        try:
            resp = await asyncio.to_thread(
                session.post,
                BABY_MARS_WEBHOOK_URL,
                json=body,
                headers={"X-API-Key": BABY_MARS_API_KEY},
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
                    tags=[f"source_service:{event.source_service}", f"event_type:{event.event_type}"],
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

        if attempt < 2:
            await asyncio.sleep(2**attempt)

    # Exhausted retries
    increment_metric(
        "stargate_lite.webhook.dead_letter",
        tags=[f"source_service:{event.source_service}"],
    )
    logger.error(
        "Webhook forward exhausted retries, dead letter",
        event_type=event.event_type,
        raw_event_id=event.raw_event_id,
        source_service=event.source_service,
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
