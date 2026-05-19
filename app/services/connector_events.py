"""Connector lifecycle event helpers."""

from datetime import UTC, datetime

from app.models_webhook import WebhookEvent
from app.routers.webhooks.base import forward_to_baby_mars


def build_connector_event_source(session_id: str | None) -> str | None:
    """Encode an originating chat session in the existing connector-event contract."""
    if not session_id:
        return None
    normalized = session_id.strip()
    if not normalized:
        return None
    return normalized if normalized.startswith("chat__") else f"chat__{normalized}"


async def emit_connector_lifecycle_event(
    *,
    service: str,
    org_id: str,
    user_id: str | None,
    status: str,
    origin: str,
    source: str | None = None,
    error_code: str | None = None,
    reason: str | None = None,
) -> bool:
    """Forward a normalized connector lifecycle event to Baby MARS."""
    now = datetime.now(UTC)
    payload: dict[str, str] = {
        "platform": service,
        "service": service,
        "status": status,
        "origin": origin,
        "changed_at": now.isoformat(),
    }
    if user_id:
        payload["user_id"] = user_id
    if source:
        payload["source"] = source
    if error_code:
        payload["error_code"] = error_code
    if reason:
        payload["reason"] = reason

    event = WebhookEvent(
        event_type=f"connector.{status}",
        source_service="stargate",
        org_id=org_id,
        timestamp=now,
        raw_event_id=(
            f"{origin}:{service}:{org_id}:{user_id or 'unknown'}:{status}:"
            f"{int(now.timestamp() * 1000)}"
        ),
        user_id=user_id,
        payload=payload,
    )
    return await forward_to_baby_mars(event)
