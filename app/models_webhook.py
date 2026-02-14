"""
Webhook event models for Stargate Lite.

Defines the normalized event model that Stargate uses to forward
inbound webhook events from external providers to Baby MARS.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    """Normalized inbound event from any provider.

    This is the contract between Stargate and Baby MARS's /webhooks/stargate endpoint.
    Every provider's raw event is normalized into this shape before forwarding.
    """

    event_type: str = Field(
        ...,
        description="Normalized event type (e.g., 'stripe.payment.succeeded')",
    )
    source_service: str = Field(
        ...,
        description="Provider name (e.g., 'quickbooks', 'stripe', 'slack')",
    )
    org_id: str = Field(
        ...,
        description="Resolved org_id from webhook registration/credentials",
    )
    timestamp: datetime = Field(..., description="Event timestamp (UTC)")
    payload: dict[str, Any] = Field(
        ...,
        description="Provider-specific payload (preserved as-is)",
    )
    raw_event_id: str = Field(
        ...,
        description="Provider's event ID — REQUIRED for dedup",
    )
    user_id: str | None = Field(
        default=None,
        description="User ID if resolvable from event",
    )
