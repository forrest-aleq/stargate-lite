"""
Stripe connector - Checkout module

Handles checkout session operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_init
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeCheckoutMixin:
    """Stripe checkout session operations mixin"""

    @requires_stripe_init
    def create_checkout_session(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a checkout session"""
        mode = args.get("mode", "payment")  # payment, subscription, or setup
        success_url = args.get("success_url")
        cancel_url = args.get("cancel_url")
        line_items = args.get("line_items", [])
        customer = args.get("customer_id")
        metadata = args.get("metadata", {})

        metadata.update({"org_id": org_id, "user_id": user_id})

        session_params: dict[str, Any] = {
            "mode": mode,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": line_items,
            "metadata": metadata,
        }
        if customer:
            session_params["customer"] = customer

        session = stripe.checkout.Session.create(**session_params)
        return {
            "session_id": session.id,
            "url": session.url,
            "status": session.status,
            "mode": session.mode,
        }

    @requires_stripe_init
    def retrieve_checkout_session(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Retrieve a checkout session"""
        session_id = args.get("session_id")
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "session_id": session.id,
            "status": session.status,
            "customer": session.customer,
            "payment_status": session.payment_status,
            "amount_total": session.amount_total,
        }

    @requires_stripe_init
    def expire_checkout_session(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Expire a checkout session"""
        session_id = args.get("session_id")
        session = stripe.checkout.Session.expire(session_id)
        return {"session_id": session.id, "status": session.status}

    @requires_stripe_init
    def list_checkout_sessions(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List checkout sessions"""
        limit = args.get("limit", 10)
        customer = args.get("customer_id")

        params: dict[str, Any] = {"limit": limit}
        if customer:
            params["customer"] = customer

        sessions = stripe.checkout.Session.list(**params)
        return {
            "sessions": [
                {
                    "session_id": s.id,
                    "status": s.status,
                    "payment_status": s.payment_status,
                    "customer": s.customer,
                }
                for s in sessions.data
            ],
            "has_more": sessions.has_more,
        }

    @requires_stripe_init
    def list_checkout_line_items(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List line items for a checkout session"""
        session_id = args.get("session_id")
        limit = args.get("limit", 10)

        line_items = stripe.checkout.Session.list_line_items(session_id, limit=limit)
        return {
            "line_items": [
                {
                    "id": item.id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "amount_total": item.amount_total,
                    "currency": item.currency,
                }
                for item in line_items.data
            ],
            "has_more": line_items.has_more,
        }
