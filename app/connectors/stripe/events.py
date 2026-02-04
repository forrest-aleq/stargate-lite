"""
Stripe connector - Events module

Handles event retrieval and listing.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_config
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeEventsMixin:
    """Stripe event operations mixin"""

    @requires_stripe_config
    def list_events(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List events (webhook events log)"""
        limit = args.get("limit", 10)
        event_type = args.get("type")

        params: dict[str, Any] = {"limit": limit}
        if event_type:
            params["type"] = event_type
        if stripe_config and stripe_config.get("stripe_account"):
            params["stripe_account"] = stripe_config["stripe_account"]

        events = stripe.Event.list(**params)
        return {
            "events": [
                {
                    "event_id": e.id,
                    "type": e.type,
                    "created": e.created,
                    "livemode": e.livemode,
                }
                for e in events.data
            ],
            "has_more": events.has_more,
        }

    @requires_stripe_config
    def retrieve_event(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a specific event"""
        event_id = args.get("event_id")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        event = stripe.Event.retrieve(event_id, **retrieve_kwargs)
        return {
            "event_id": event.id,
            "type": event.type,
            "created": event.created,
            "livemode": event.livemode,
            "data": dict(event.data) if event.data else {},
        }
