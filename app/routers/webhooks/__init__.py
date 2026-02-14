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
from app.routers.webhooks.quickbooks import router as quickbooks_router
from app.routers.webhooks.slack import router as slack_router
from app.routers.webhooks.stripe import router as stripe_router
from app.routers.webhooks.twilio import router as twilio_router
from app.routers.webhooks.xero import router as xero_router

router = APIRouter(tags=["webhooks"])
router.include_router(base_router)
router.include_router(stripe_router)
router.include_router(quickbooks_router)
router.include_router(xero_router)
router.include_router(slack_router)
router.include_router(twilio_router)

__all__ = ["router"]
