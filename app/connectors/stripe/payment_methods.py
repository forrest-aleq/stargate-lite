"""
Stripe connector - Payment Methods module

Handles payment method operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_init


class StripePaymentMethodsMixin:
    """Stripe payment method operations mixin"""

    @requires_stripe_init
    def list_payment_methods(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List payment methods for a customer"""
        customer_id = args.get("customer_id")
        if not customer_id:
            raise ValueError("customer_id is required")
        type_ = args.get("type", "card")
        limit = args.get("limit", 10)

        methods = stripe.PaymentMethod.list(customer=customer_id, type=type_, limit=limit)
        return {
            "payment_methods": [
                {
                    "id": m.id,
                    "type": m.type,
                    "card": m.card.to_dict() if m.card else None,
                    "created": m.created,
                }
                for m in methods.data
            ],
            "has_more": methods.has_more,
        }

    @requires_stripe_init
    def attach_payment_method(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Attach a payment method to a customer"""
        payment_method_id = args.get("payment_method_id")
        if not payment_method_id:
            raise ValueError("payment_method_id is required")
        customer_id = args.get("customer_id")
        if not customer_id:
            raise ValueError("customer_id is required")

        method = stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        return {"payment_method_id": method.id, "customer": method.customer, "type": method.type}

    @requires_stripe_init
    def create_payment_method(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a payment method"""
        type_ = args.get("type", "card")
        card = args.get("card")  # token or card details
        billing_details = args.get("billing_details", {})

        method = stripe.PaymentMethod.create(type=type_, card=card, billing_details=billing_details)
        return {
            "payment_method_id": method.id,
            "type": method.type,
            "created": method.created,
        }

    @requires_stripe_init
    def retrieve_payment_method(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Retrieve a payment method"""
        payment_method_id = args.get("payment_method_id")
        if not payment_method_id:
            raise ValueError("payment_method_id is required")
        method = stripe.PaymentMethod.retrieve(payment_method_id)
        return {
            "payment_method_id": method.id,
            "type": method.type,
            "card": method.card.to_dict() if method.card else None,
            "customer": method.customer,
            "billing_details": method.billing_details.to_dict() if method.billing_details else None,
        }

    @requires_stripe_init
    def update_payment_method(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a payment method"""
        payment_method_id = args.get("payment_method_id")
        if not payment_method_id:
            raise ValueError("payment_method_id is required")
        billing_details = args.get("billing_details", {})
        metadata = args.get("metadata", {})

        update_params: dict[str, Any] = {}
        if billing_details:
            update_params["billing_details"] = billing_details
        if metadata:
            update_params["metadata"] = metadata

        method = stripe.PaymentMethod.modify(payment_method_id, **update_params)
        return {"payment_method_id": method.id, "type": method.type}

    @requires_stripe_init
    def detach_payment_method(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Detach a payment method from its customer"""
        payment_method_id = args.get("payment_method_id")
        if not payment_method_id:
            raise ValueError("payment_method_id is required")
        method = stripe.PaymentMethod.detach(payment_method_id)
        return {"payment_method_id": method.id, "detached": True}
