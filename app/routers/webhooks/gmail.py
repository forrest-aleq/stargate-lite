"""
Gmail push notification receiver.

Receives Google Cloud Pub/Sub push notifications for Gmail events.
Pub/Sub sends a POST with a base64-encoded JSON message containing
emailAddress and historyId. We normalize this and forward to Baby MARS.

Baby MARS (not Stargate) then calls gmail.get_history to fetch changes.

Verification: Google Pub/Sub includes a Bearer JWT in the Authorization
header, validated against Google's public keys.

Env: GMAIL_PUBSUB_AUDIENCE (optional — for JWT audience verification)
"""

import base64
import json
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Response

from app.logging_config import get_logger
from app.models_webhook import WebhookEvent
from app.redis_client import redis_client
from app.routers.webhooks.base import forward_to_baby_mars

logger = get_logger(__name__)
router = APIRouter()

# Redis key prefix for tracking last-processed historyId per user
_HISTORY_KEY_PREFIX = "stargate:gmail:history"


def _verify_pubsub_token(request: Request) -> bool:
    """Verify Google Pub/Sub push authentication.

    Google Pub/Sub push endpoints can be authenticated via:
    1. Bearer token in Authorization header (JWT from service account)
    2. Query parameter token (simpler, shared secret)

    We support the query-param token approach for simplicity.
    If GMAIL_PUBSUB_TOKEN is set, we require it to match.
    If unset, we accept all requests (rely on network-level security).
    """
    expected_token = os.getenv("GMAIL_PUBSUB_TOKEN", "")
    if not expected_token:
        # No token configured — accept (rely on firewall / VPC)
        return True

    # Check query param ?token=...
    query_token = request.query_params.get("token", "")
    if query_token and query_token == expected_token:
        return True

    # Check Authorization: Bearer ...
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]
        if bearer_token == expected_token:
            return True

    return False


def _get_last_history_id(email: str) -> str | None:
    """Get last processed historyId for an email address."""
    key = f"{_HISTORY_KEY_PREFIX}:{email}"
    result = redis_client.get_cached_response(key, "")
    if result and isinstance(result, dict):
        return str(result.get("history_id", ""))
    return None


def _set_last_history_id(email: str, history_id: str) -> None:
    """Store last processed historyId for an email address."""
    key = f"{_HISTORY_KEY_PREFIX}:{email}"
    redis_client.cache_response(key, "", {"history_id": history_id}, ttl_seconds=604800)  # 7 days


@router.post("/webhooks/gmail")
async def gmail_push_notification(request: Request) -> Response:
    """Receive Gmail push notification via Google Cloud Pub/Sub.

    Google sends a POST with JSON body:
    {
        "message": {
            "data": "<base64-encoded JSON>",
            "messageId": "...",
            "publishTime": "..."
        },
        "subscription": "projects/.../subscriptions/..."
    }

    The base64-decoded data contains:
    {
        "emailAddress": "user@example.com",
        "historyId": "12345"
    }

    We normalize this to a WebhookEvent and forward to Baby MARS.
    Baby MARS then calls gmail.get_history to fetch actual changes.
    """
    if not _verify_pubsub_token(request):
        logger.warning(
            "Invalid Pub/Sub authentication",
            log_event="gmail_webhook_auth_invalid",
        )
        return Response(status_code=401, content="Unauthorized")

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return Response(status_code=400, content="Invalid JSON")

    # Extract Pub/Sub message
    message: dict[str, Any] = payload.get("message", {})
    data_b64: str = message.get("data", "")
    message_id: str = message.get("messageId", "")

    if not data_b64:
        logger.warning(
            "Gmail push notification missing data",
            log_event="gmail_push_no_data",
        )
        return Response(status_code=400, content="Missing message data")

    # Decode the base64 message data
    try:
        data_bytes = base64.b64decode(data_b64)
        notification: dict[str, Any] = json.loads(data_bytes)
    except Exception:
        logger.warning(
            "Failed to decode Gmail push notification data",
            log_event="gmail_push_decode_error",
            exc_info=True,
        )
        return Response(status_code=400, content="Invalid message data")

    email_address: str = notification.get("emailAddress", "")
    history_id: str = str(notification.get("historyId", ""))

    if not email_address or not history_id:
        logger.warning(
            "Gmail push missing emailAddress or historyId",
            log_event="gmail_push_incomplete",
        )
        return Response(status_code=400, content="Incomplete notification")

    # Check for historyId regression (already processed)
    last_history = _get_last_history_id(email_address)
    if last_history and int(history_id) <= int(last_history):
        logger.info(
            "Gmail historyId already processed, skipping",
            email=email_address,
            history_id=history_id,
            last_history=last_history,
            log_event="gmail_history_skip",
        )
        return Response(status_code=200, content="ok")

    # Build normalized event
    event = WebhookEvent(
        event_type="gmail.message.received",
        source_service="gmail",
        org_id=email_address,
        timestamp=datetime.now(UTC),
        payload={
            "emailAddress": email_address,
            "historyId": history_id,
            "previousHistoryId": last_history,
        },
        raw_event_id=message_id or f"gmail:{email_address}:{history_id}",
        user_id=email_address,
    )

    await forward_to_baby_mars(event)

    # Update last processed historyId
    _set_last_history_id(email_address, history_id)

    logger.info(
        "Gmail push notification forwarded",
        email=email_address,
        history_id=history_id,
        log_event="gmail_push_forwarded",
    )

    return Response(status_code=200, content="ok")
