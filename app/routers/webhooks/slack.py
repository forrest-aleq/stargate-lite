"""
Slack webhook receiver.

Verifies X-Slack-Signature header (HMAC-SHA256), handles URL verification
challenge, normalizes message events, and forwards to Baby MARS.
Env: SLACK_SIGNING_SECRET
"""

import hashlib
import hmac
import os
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.logging_config import get_logger
from app.models_webhook import WebhookEvent
from app.routers.webhooks.base import forward_to_baby_mars

logger = get_logger(__name__)
router = APIRouter()


def _verify_slack_signature(
    body: bytes, timestamp: str, signature: str, signing_secret: str
) -> bool:
    """Verify Slack request signature.

    Slack signs: v0:{timestamp}:{body}
    Header format: X-Slack-Signature: v0=<hex-digest>
    """
    # Reject requests older than 5 minutes (replay protection)
    try:
        if abs(time.time() - float(timestamp)) > 300:
            return False
    except ValueError:
        return False

    base_string = f"v0:{timestamp}:".encode() + body
    expected = "v0=" + hmac.new(
        signing_secret.encode(), base_string, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("/webhooks/slack")
async def slack_webhook(request: Request) -> Response:
    """Receive Slack Events API webhook.

    Handles:
    1. URL verification: {"type": "url_verification"} → respond with challenge.
    2. Event callbacks: {"type": "event_callback"} → normalize + forward.
    """
    signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")
    if not signing_secret:
        logger.error("SLACK_SIGNING_SECRET not set", log_event="slack_webhook_not_configured")
        return Response(status_code=503, content="Webhook not configured")

    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    # URL verification doesn't need signature check (Slack sends it during setup)
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return Response(status_code=400, content="Invalid JSON")

    # Case 1: URL verification challenge
    if payload.get("type") == "url_verification":
        challenge: str = payload.get("challenge", "")
        logger.info("Slack URL verification challenge", log_event="slack_url_verification")
        return JSONResponse(content={"challenge": challenge})

    # For all other events, verify signature
    if not _verify_slack_signature(body, timestamp, signature, signing_secret):
        logger.warning("Invalid Slack webhook signature", log_event="slack_webhook_sig_invalid")
        return Response(status_code=401, content="Invalid signature")

    # Case 2: Event callback
    if payload.get("type") == "event_callback":
        slack_event: dict[str, Any] = payload.get("event", {})
        event_type: str = slack_event.get("type", "unknown")
        team_id: str = payload.get("team_id", "")
        event_id: str = payload.get("event_id", "")

        # Determine normalized event type
        if event_type == "message" and slack_event.get("channel_type") == "im":
            normalized_type = "slack.message.received"
        elif event_type == "app_mention":
            normalized_type = "slack.mention"
        else:
            normalized_type = f"slack.{event_type}"

        user_id = slack_event.get("user")

        event = WebhookEvent(
            event_type=normalized_type,
            source_service="slack",
            org_id=team_id,
            timestamp=datetime.now(UTC),
            payload=slack_event,
            raw_event_id=event_id,
            user_id=user_id,
        )

        await forward_to_baby_mars(event)

    return Response(status_code=200, content="ok")
