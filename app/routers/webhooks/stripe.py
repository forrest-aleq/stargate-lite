"""
Stripe webhook receiver.

Verifies Stripe-Signature header, normalizes events, and forwards to Baby MARS.
Env: STRIPE_WEBHOOK_SECRET
"""

import hashlib
import hmac
import os
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Response

from app.logging_config import get_logger
from app.models_webhook import WebhookEvent
from app.routers.webhooks.base import forward_to_baby_mars

logger = get_logger(__name__)
router = APIRouter()


def _verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verify Stripe webhook signature.

    Stripe-Signature format: t=timestamp,v1=signature[,v0=legacy]
    Signed payload = "{timestamp}.{body}"
    """
    try:
        elements = dict(item.split("=", 1) for item in sig_header.split(","))
        timestamp = elements.get("t", "")
        signature = elements.get("v1", "")

        if not timestamp or not signature:
            return False

        # Reject timestamps older than 5 minutes (replay protection)
        if abs(time.time() - int(timestamp)) > 300:
            logger.warning("Stripe webhook timestamp too old", log_event="stripe_webhook_replay")
            return False

        signed_payload = f"{timestamp}.".encode() + payload
        expected = hmac.new(
            secret.encode(), signed_payload, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
    except Exception:
        logger.warning("Stripe signature parsing failed", log_event="stripe_sig_parse_error", exc_info=True)
        return False


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request) -> Response:
    """Receive Stripe webhook events.

    1. Verify Stripe-Signature (HMAC-SHA256 with timestamp).
    2. Extract event type + event ID.
    3. Resolve org_id from Stripe Connect account field.
    4. Normalize to WebhookEvent.
    5. Forward to Baby MARS.
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not set", log_event="stripe_webhook_not_configured")
        return Response(status_code=503, content="Webhook not configured")

    body = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    if not _verify_stripe_signature(body, sig_header, webhook_secret):
        logger.warning("Invalid Stripe webhook signature", log_event="stripe_webhook_sig_invalid")
        return Response(status_code=401, content="Invalid signature")

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return Response(status_code=400, content="Invalid JSON")

    event_type = payload.get("type", "unknown")
    event_id = payload.get("id", "")

    if not event_id:
        return Response(status_code=400, content="Missing event ID")

    # Resolve org_id from Connect account or default
    # In Connect events, payload.account contains the connected account ID
    stripe_account = payload.get("account", "")
    org_id = stripe_account or "default"

    event = WebhookEvent(
        event_type=f"stripe.{event_type}",
        source_service="stripe",
        org_id=org_id,
        timestamp=datetime.now(UTC),
        payload=payload,
        raw_event_id=event_id,
    )

    await forward_to_baby_mars(event)

    return Response(status_code=200, content="ok")
