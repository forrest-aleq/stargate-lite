"""
Twilio webhook receiver.

Verifies X-Twilio-Signature header (HMAC-SHA1 of URL + sorted POST params),
normalizes inbound SMS events, and forwards to Baby MARS.
Env: TWILIO_AUTH_TOKEN
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


def _verify_twilio_signature(
    url: str, params: dict[str, str], signature: str, auth_token: str
) -> bool:
    """Verify Twilio request signature (HMAC-SHA1).

    Twilio signs: URL + sorted POST params (key + value concatenated).
    The signature is base64-encoded HMAC-SHA1.
    """
    import base64

    # Build the data string: URL followed by sorted POST params
    data = url
    for key in sorted(params.keys()):
        data += key + params[key]

    expected = base64.b64encode(
        hmac.new(auth_token.encode(), data.encode(), hashlib.sha1).digest()
    ).decode()

    return hmac.compare_digest(expected, signature)


@router.post("/webhooks/twilio")
async def twilio_webhook(request: Request) -> Response:
    """Receive Twilio inbound SMS webhook.

    Twilio sends POST with form-encoded params for inbound SMS.
    Verifies X-Twilio-Signature, normalizes to sms.received event,
    and forwards to Baby MARS.
    """
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        logger.error("TWILIO_AUTH_TOKEN not set", log_event="twilio_webhook_not_configured")
        return Response(status_code=503, content="Webhook not configured")

    # Twilio sends form-encoded data
    form_data = await request.form()
    params: dict[str, str] = {k: str(v) for k, v in form_data.items()}

    signature = request.headers.get("X-Twilio-Signature", "")

    # Reconstruct the full URL Twilio used to sign
    # Use X-Forwarded-Proto/Host if behind a proxy
    url = str(request.url)

    if not _verify_twilio_signature(url, params, signature, auth_token):
        logger.warning("Invalid Twilio webhook signature", log_event="twilio_webhook_sig_invalid")
        return Response(status_code=401, content="Invalid signature")

    # Extract SMS fields
    from_number: str = params.get("From", "")
    to_number: str = params.get("To", "")
    body: str = params.get("Body", "")
    message_sid: str = params.get("MessageSid", "")
    account_sid: str = params.get("AccountSid", "")

    if not message_sid:
        return Response(status_code=400, content="Missing MessageSid")

    sms_payload: dict[str, Any] = {
        "from": from_number,
        "to": to_number,
        "body": body,
        "message_sid": message_sid,
        "account_sid": account_sid,
    }

    event = WebhookEvent(
        event_type="sms.received",
        source_service="twilio",
        org_id=account_sid,
        timestamp=datetime.now(UTC),
        payload=sms_payload,
        raw_event_id=message_sid,
        user_id=from_number,
    )

    await forward_to_baby_mars(event)

    # Twilio expects a TwiML response — empty response means "do nothing"
    return Response(
        status_code=200,
        content="<Response></Response>",
        media_type="application/xml",
    )
