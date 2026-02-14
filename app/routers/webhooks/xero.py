"""
Xero webhook receiver.

Verifies HMAC-SHA256 signature, handles intent-to-receive validation,
normalizes events, and forwards to Baby MARS.
Env: XERO_WEBHOOK_KEY
"""

import hashlib
import hmac
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Response

from app.logging_config import get_logger
from app.models_webhook import WebhookEvent
from app.routers.webhooks.base import forward_to_baby_mars

logger = get_logger(__name__)
router = APIRouter()


def _verify_xero_signature(payload: bytes, signature: str, webhook_key: str) -> bool:
    """Verify Xero webhook HMAC-SHA256 signature."""
    expected = hmac.new(webhook_key.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhooks/xero")
async def xero_webhook(request: Request) -> Response:
    """Receive Xero webhook events.

    Intent-to-receive: Xero sends a validation request on registration.
    We MUST respond 200 with correct HMAC for valid payloads, or 401 for
    intentionally invalid ones (Xero tests both).

    Normal events: verify signature, normalize, forward.
    """
    webhook_key = os.getenv("XERO_WEBHOOK_KEY", "")
    if not webhook_key:
        logger.error("XERO_WEBHOOK_KEY not set", log_event="xero_webhook_not_configured")
        return Response(status_code=503, content="Webhook not configured")

    body = await request.body()
    sig_header = request.headers.get("x-xero-signature", "")

    # Xero intent-to-receive validation:
    # Xero sends requests with both valid and intentionally invalid signatures.
    # We must return 200 for valid, 401 for invalid — proving we actually check.
    if not _verify_xero_signature(body, sig_header, webhook_key):
        return Response(status_code=401, content="Invalid signature")

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return Response(status_code=200, content="ok")

    # Parse Xero events
    events: list[dict[str, Any]] = payload.get("events", [])

    if not events:
        # Empty payload = intent-to-receive validation (valid sig, empty body)
        logger.info("Xero intent-to-receive validation passed", log_event="xero_validation_pass")
        return Response(status_code=200, content="ok")

    for xero_event in events:
        resource_url: str = xero_event.get("resourceUrl", "")
        event_category: str = xero_event.get("eventCategory", "unknown").lower()
        event_type_raw: str = xero_event.get("eventType", "unknown").lower()
        tenant_id: str = xero_event.get("tenantId", "")
        event_id: str = xero_event.get("eventId", "")

        event = WebhookEvent(
            event_type=f"xero.{event_category}.{event_type_raw}",
            source_service="xero",
            org_id=tenant_id,
            timestamp=datetime.now(UTC),
            payload=xero_event,
            raw_event_id=event_id or f"{tenant_id}:{resource_url}",
        )

        await forward_to_baby_mars(event)

    return Response(status_code=200, content="ok")
