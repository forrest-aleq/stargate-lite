"""
Bland AI webhook receiver.

Receives call completion events from Bland AI and forwards normalized
voice events to Baby MARS.

Auth: Bearer token verification against BLANDAI_WEBHOOK_SECRET env var.
Bland AI does not use HMAC signatures.
"""

import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Response

from app.logging_config import get_logger
from app.models_webhook import WebhookEvent
from app.routers.webhooks.base import forward_to_baby_mars

logger = get_logger(__name__)
router = APIRouter()

# Statuses that map to a "failed" event type
_FAILED_STATUSES = {"failed", "no-answer"}


def _extract_bearer_token(authorization: str) -> str:
    """Extract token from 'Bearer <token>' header value."""
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return ""


def _resolve_event_type(status: str) -> str:
    """Map Bland AI call status to normalized event type.

    completed / voicemail  -> voice.call.completed
    failed / no-answer     -> voice.call.failed
    """
    if status in _FAILED_STATUSES:
        return "voice.call.failed"
    return "voice.call.completed"


@router.post("/webhooks/blandai")
async def blandai_webhook(request: Request) -> Response:
    """Receive Bland AI call completion webhook.

    Bland AI sends a JSON POST when a call finishes. Verification is
    done via a shared secret sent as a Bearer token in the Authorization
    header — compared against the BLANDAI_WEBHOOK_SECRET env var.

    The payload is normalized to a WebhookEvent and forwarded to Baby MARS.
    """
    webhook_secret = os.getenv("BLANDAI_WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.error(
            "BLANDAI_WEBHOOK_SECRET not set",
            log_event="blandai_webhook_not_configured",
        )
        return Response(status_code=503, content="Webhook not configured")

    # Verify bearer token
    authorization = request.headers.get("Authorization", "")
    token = _extract_bearer_token(authorization)

    if not token or token != webhook_secret:
        logger.warning(
            "Invalid Bland AI webhook bearer token",
            log_event="blandai_webhook_auth_invalid",
        )
        return Response(status_code=401, content="Invalid authorization")

    # Parse JSON body
    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        logger.warning(
            "Bland AI webhook body is not valid JSON",
            log_event="blandai_webhook_bad_body",
        )
        return Response(status_code=400, content="Invalid JSON body")

    call_id: str = body.get("call_id", "")
    if not call_id:
        logger.warning(
            "Bland AI webhook missing call_id",
            log_event="blandai_webhook_missing_call_id",
        )
        return Response(status_code=400, content="Missing call_id")

    status: str = body.get("status", "completed")
    event_type = _resolve_event_type(status)

    event = WebhookEvent(
        event_type=event_type,
        source_service="blandai",
        org_id="ALEQ_SYSTEM",
        timestamp=datetime.now(UTC),
        payload=body,
        raw_event_id=call_id,
    )

    logger.info(
        "Bland AI webhook received",
        call_id=call_id,
        status=status,
        event_type=event_type,
        answered_by=body.get("answered_by", "unknown"),
        log_event="blandai_webhook_received",
    )

    await forward_to_baby_mars(event)

    return Response(status_code=200, content="OK")
