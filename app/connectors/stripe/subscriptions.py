"""
Stripe connector - Subscriptions module

Handles subscription CRUD and operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_config
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeSubscriptionsMixin:
    """Stripe subscription operations mixin"""

    @requires_stripe_config
    def create_subscription(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
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

        create_kwargs: dict[str, Any] = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "metadata": metadata,
        }
        if stripe_config and stripe_config.get("stripe_account"):
            create_kwargs["stripe_account"] = stripe_config["stripe_account"]

        subscription = stripe.Subscription.create(**create_kwargs)

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

    @requires_stripe_config
    def retrieve_subscription(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a subscription"""
        subscription_id = args.get("subscription_id")
        if not isinstance(subscription_id, str):
            raise ValueError("subscription_id is required")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        sub = stripe.Subscription.retrieve(subscription_id, **retrieve_kwargs)
        return {
            "subscription_id": sub.id,
            "customer": sub.customer,
            "status": sub.status,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "cancel_at_period_end": sub.cancel_at_period_end,
        }

    @requires_stripe_config
    def update_subscription(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
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
        if stripe_config and stripe_config.get("stripe_account"):
            update_params["stripe_account"] = stripe_config["stripe_account"]

        sub = stripe.Subscription.modify(subscription_id, **update_params)
        return {
            "subscription_id": sub.id,
            "status": sub.status,
        }

    @requires_stripe_config
    def cancel_subscription(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Cancel a subscription"""
        subscription_id = args.get("subscription_id")
        if not subscription_id:
            raise ValueError("subscription_id is required")
        at_period_end = args.get("at_period_end", True)

        if at_period_end:
            # Schedule cancellation at period end using modify
            modify_kwargs: dict[str, Any] = {"cancel_at_period_end": True}
            if stripe_config and stripe_config.get("stripe_account"):
                modify_kwargs["stripe_account"] = stripe_config["stripe_account"]
            sub = stripe.Subscription.modify(subscription_id, **modify_kwargs)
        else:
            # Cancel immediately using delete
            delete_kwargs: dict[str, Any] = {}
            if stripe_config and stripe_config.get("stripe_account"):
                delete_kwargs["stripe_account"] = stripe_config["stripe_account"]
            sub = stripe.Subscription.delete(subscription_id, **delete_kwargs)
        return {"subscription_id": sub.id, "status": sub.status}

    @requires_stripe_config
    def list_subscriptions(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List subscriptions"""
        limit = args.get("limit", 10)
        customer = args.get("customer_id")
        status = args.get("status")

        params: dict[str, Any] = {"limit": limit}
        if customer:
            params["customer"] = customer
        if status:
            params["status"] = status
        if stripe_config and stripe_config.get("stripe_account"):
            params["stripe_account"] = stripe_config["stripe_account"]

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
