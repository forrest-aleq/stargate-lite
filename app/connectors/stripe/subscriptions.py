"""
Stripe connector - Subscriptions module

Handles subscription CRUD and operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_init
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeSubscriptionsMixin:
    """Stripe subscription operations mixin"""

    @requires_stripe_init
    def create_subscription(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a subscription for a customer"""
        customer_id = args.get("customer_id")
        price_id = args.get("price_id")  # Stripe price ID
        metadata = args.get("metadata", {})

        if not isinstance(customer_id, str):
            raise ValueError("customer_id is required")
        if not isinstance(price_id, str):
            raise ValueError("price_id is required")

        logger.info(
            "Creating subscription",
            service="stripe",
            customer_id=customer_id,
            price_id=price_id,
            log_event="stripe_subscription_create",
        )

        metadata.update({"org_id": org_id, "user_id": user_id})

        subscription = stripe.Subscription.create(
            customer=customer_id, items=[{"price": price_id}], metadata=metadata
        )

        logger.info(
            "Subscription created",
            service="stripe",
            subscription_id=subscription.id,
            status=subscription.status,
            log_event="stripe_subscription_created",
        )

        return {
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
        }

    @requires_stripe_init
    def retrieve_subscription(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Retrieve a subscription"""
        subscription_id = args.get("subscription_id")
        if not isinstance(subscription_id, str):
            raise ValueError("subscription_id is required")
        sub = stripe.Subscription.retrieve(subscription_id)
        return {
            "subscription_id": sub.id,
            "customer": sub.customer,
            "status": sub.status,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "cancel_at_period_end": sub.cancel_at_period_end,
        }

    @requires_stripe_init
    def update_subscription(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a subscription"""
        subscription_id = args.get("subscription_id")
        price_id = args.get("price_id")
        metadata = args.get("metadata", {})

        update_params: dict[str, Any] = {}
        if price_id:
            update_params["items"] = [{"price": price_id}]
        if metadata:
            update_params["metadata"] = metadata

        sub = stripe.Subscription.modify(subscription_id, **update_params)
        return {
            "subscription_id": sub.id,
            "status": sub.status,
        }

    @requires_stripe_init
    def cancel_subscription(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Cancel a subscription"""
        subscription_id = args.get("subscription_id")
        if not subscription_id:
            raise ValueError("subscription_id is required")
        at_period_end = args.get("at_period_end", True)

        if at_period_end:
            # Schedule cancellation at period end using modify
            sub = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
        else:
            # Cancel immediately using delete
            sub = stripe.Subscription.delete(subscription_id)
        return {"subscription_id": sub.id, "status": sub.status}

    @requires_stripe_init
    def list_subscriptions(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List subscriptions"""
        limit = args.get("limit", 10)
        customer = args.get("customer_id")
        status = args.get("status")

        params: dict[str, Any] = {"limit": limit}
        if customer:
            params["customer"] = customer
        if status:
            params["status"] = status

        subs = stripe.Subscription.list(**params)
        return {
            "subscriptions": [
                {
                    "subscription_id": s.id,
                    "customer": s.customer,
                    "status": s.status,
                    "current_period_end": s.current_period_end,
                }
                for s in subs.data
            ],
            "has_more": subs.has_more,
        }
