"""
Webhook Routes Package

Receives inbound events from external services and forwards normalized
events to Baby MARS's /webhooks/stargate endpoint.

Provider modules:
- stripe: Stripe payment events
- quickbooks: QuickBooks Online accounting events
- xero: Xero accounting events
- slack: Slack messaging events
- twilio: Twilio SMS events
- gmail: Gmail push notifications (Pub/Sub)
"""

from fastapi import APIRouter

from app.routers.webhooks.base import router as base_router

router = APIRouter(tags=["webhooks"])
router.include_router(base_router)

# Provider-specific routers are included as they're built (commits 5-7)

__all__ = ["router"]
