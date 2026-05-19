"""
QuickBooks Online webhook receiver.

Verifies HMAC-SHA256 signature, handles verification challenge,
normalizes entity change events, and forwards to Baby MARS.
Env: QBO_WEBHOOK_VERIFIER_TOKEN
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
from app.routers.webhooks.tenant_resolution import resolve_webhook_identity

logger = get_logger(__name__)
router = APIRouter()


def _verify_qbo_signature(payload: bytes, signature: str, verifier_token: str) -> bool:
    """Verify QuickBooks webhook HMAC-SHA256 signature."""
    expected = hmac.new(verifier_token.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhooks/quickbooks")
async def quickbooks_webhook(request: Request) -> Response:
    """Receive QuickBooks Online webhook events.

    Handles two cases:
    1. Verification challenge: QBO sends a challenge on registration.
       Respond with HMAC of the payload.
    2. Entity change notifications: normalize and forward.
    """
    verifier_token = os.getenv("QBO_WEBHOOK_VERIFIER_TOKEN", "")
    if not verifier_token:
        logger.error("QBO_WEBHOOK_VERIFIER_TOKEN not set", log_event="qbo_webhook_not_configured")
        return Response(status_code=503, content="Webhook not configured")

    body = await request.body()

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return Response(status_code=400, content="Invalid JSON")

    # Case 1: Verification challenge
    # QBO sends {"verifier_token": "..."} — respond with HMAC to prove we own the endpoint
    if "verifier_token" in payload:
        challenge_token: str = payload["verifier_token"]
        response_hash = hmac.new(
            verifier_token.encode(), challenge_token.encode(), hashlib.sha256
        ).hexdigest()
        logger.info("QBO verification challenge responded", log_event="qbo_challenge_response")
        return Response(status_code=200, content=response_hash)

    # Case 2: Event notification — verify signature
    sig_header = request.headers.get("intuit-signature", "")
    if not _verify_qbo_signature(body, sig_header, verifier_token):
        logger.warning("Invalid QBO webhook signature", log_event="qbo_webhook_sig_invalid")
        return Response(status_code=401, content="Invalid signature")

    # Parse eventNotifications — each contains realmId and entity changes
    notifications: list[dict[str, Any]] = payload.get("eventNotifications", [])

    for notification in notifications:
        realm_id: str = notification.get("realmId", "")
        fallback_org_id = realm_id or "default"
        org_id, user_id = await resolve_webhook_identity(
            "quickbooks",
            fallback_org_id=fallback_org_id,
            realm_id=realm_id or None,
        )
        entities: list[dict[str, Any]] = notification.get("dataChangeEvent", {}).get("entities", [])

        for entity in entities:
            entity_name: str = entity.get("name", "unknown").lower()
            entity_id: str = entity.get("id", "")
            operation: str = entity.get("operation", "unknown").lower()

            event = WebhookEvent(
                event_type=f"qbo.{entity_name}.{operation}",
                source_service="quickbooks",
                org_id=org_id,
                timestamp=datetime.now(UTC),
                payload=entity,
                raw_event_id=f"{realm_id}:{entity_name}:{entity_id}:{operation}",
                user_id=user_id,
            )

            await forward_to_baby_mars(event)

    return Response(status_code=200, content="ok")
