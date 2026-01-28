"""
Stripe connector - Payments module

Handles payment intents, charges, and refunds.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_config
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripePaymentsMixin:
    """Stripe payment operations mixin"""

    @requires_stripe_config
    def create_payment_intent(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a payment intent"""
        amount = args.get("amount")  # Amount in cents
        currency = args.get("currency", "usd")
        customer_id = args.get("customer_id")
        description = args.get("description", "")
        metadata = args.get("metadata", {})

        logger.info(
            "Creating payment intent",
            service="stripe",
            amount=amount,
            currency=currency,
            customer_id=customer_id,
            log_event="stripe_payment_intent_create",
        )

        # Add org/user context to metadata
        metadata.update({"org_id": org_id, "user_id": user_id})

        create_kwargs: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "customer": customer_id,
            "description": description,
            "metadata": metadata,
            "automatic_payment_methods": {"enabled": True},
        }
        if stripe_config and stripe_config.get("stripe_account"):
            create_kwargs["stripe_account"] = stripe_config["stripe_account"]

        payment_intent = stripe.PaymentIntent.create(**create_kwargs)

        logger.info(
            "Payment intent created",
            service="stripe",
            payment_intent_id=payment_intent.id,
            status=payment_intent.status,
            log_event="stripe_payment_intent_created",
        )

        return {
            "payment_intent_id": payment_intent.id,
            "client_secret": payment_intent.client_secret,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "status": payment_intent.status,
        }

    @requires_stripe_config
    def retrieve_payment_intent(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a payment intent"""
        payment_intent_id = args.get("payment_intent_id")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        pi = stripe.PaymentIntent.retrieve(payment_intent_id, **retrieve_kwargs)
        return {
            "payment_intent_id": pi.id,
            "amount": pi.amount,
            "currency": pi.currency,
            "status": pi.status,
            "customer": pi.customer,
            "description": pi.description,
        }

    @requires_stripe_config
    def refund_payment(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Refund a payment"""
        payment_intent_id = args.get("payment_intent_id")
        amount = args.get("amount")  # Optional: partial refund
        reason = args.get("reason", "requested_by_customer")

        logger.info(
            "Processing refund",
            service="stripe",
            payment_intent_id=payment_intent_id,
            amount=amount,
            reason=reason,
            log_event="stripe_refund_create",
        )

        refund_params: dict[str, Any] = {"payment_intent": payment_intent_id, "reason": reason}
        if amount:
            refund_params["amount"] = amount
        if stripe_config and stripe_config.get("stripe_account"):
            refund_params["stripe_account"] = stripe_config["stripe_account"]

        refund = stripe.Refund.create(**refund_params)

        logger.info(
            "Refund processed",
            service="stripe",
            refund_id=refund.id,
            amount=refund.amount,
            status=refund.status,
            log_event="stripe_refund_created",
        )

        return {
            "refund_id": refund.id,
            "amount": refund.amount,
            "status": refund.status,
            "payment_intent_id": refund.payment_intent,
        }

    @requires_stripe_config
    def retrieve_refund(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a refund"""
        refund_id = args.get("refund_id")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        refund = stripe.Refund.retrieve(refund_id, **retrieve_kwargs)
        return {
            "refund_id": refund.id,
            "amount": refund.amount,
            "status": refund.status,
            "payment_intent": refund.payment_intent,
            "reason": refund.reason,
        }

    @requires_stripe_config
    def update_refund(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a refund"""
        refund_id = args.get("refund_id")
        metadata = args.get("metadata", {})

        update_kwargs: dict[str, Any] = {"metadata": metadata}
        if stripe_config and stripe_config.get("stripe_account"):
            update_kwargs["stripe_account"] = stripe_config["stripe_account"]

        refund = stripe.Refund.modify(refund_id, **update_kwargs)
        return {
            "refund_id": refund.id,
            "status": refund.status,
            "metadata": refund.metadata,
        }

    @requires_stripe_config
    def cancel_refund(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Cancel a refund (only possible if not yet processed)"""
        refund_id = args.get("refund_id")

        cancel_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            cancel_kwargs["stripe_account"] = stripe_config["stripe_account"]

        refund = stripe.Refund.cancel(refund_id, **cancel_kwargs)
        return {"refund_id": refund.id, "status": refund.status}

    @requires_stripe_config
    def list_refunds(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List refunds"""
        limit = args.get("limit", 10)
        payment_intent = args.get("payment_intent_id")
        charge = args.get("charge_id")

        params: dict[str, Any] = {"limit": limit}
        if payment_intent:
            params["payment_intent"] = payment_intent
        if charge:
            params["charge"] = charge
        if stripe_config and stripe_config.get("stripe_account"):
            params["stripe_account"] = stripe_config["stripe_account"]

        refunds = stripe.Refund.list(**params)
        return {
            "refunds": [
                {
                    "refund_id": r.id,
                    "amount": r.amount,
                    "status": r.status,
                    "payment_intent": r.payment_intent,
                }
                for r in refunds.data
            ],
            "has_more": refunds.has_more,
        }

    @requires_stripe_config
    def retrieve_charge(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a charge"""
        charge_id = args.get("charge_id")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        charge = stripe.Charge.retrieve(charge_id, **retrieve_kwargs)
        return {
            "charge_id": charge.id,
            "amount": charge.amount,
            "currency": charge.currency,
            "status": charge.status,
            "customer": charge.customer,
            "payment_intent": charge.payment_intent,
            "refunded": charge.refunded,
        }

    @requires_stripe_config
    def list_charges(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List charges"""
        limit = args.get("limit", 10)
        customer = args.get("customer_id")
        payment_intent = args.get("payment_intent_id")

        params: dict[str, Any] = {"limit": limit}
        if customer:
            params["customer"] = customer
        if payment_intent:
            params["payment_intent"] = payment_intent
        if stripe_config and stripe_config.get("stripe_account"):
            params["stripe_account"] = stripe_config["stripe_account"]

        charges = stripe.Charge.list(**params)
        return {
            "charges": [
                {
                    "charge_id": c.id,
                    "amount": c.amount,
                    "currency": c.currency,
                    "status": c.status,
                    "customer": c.customer,
                }
                for c in charges.data
            ],
            "has_more": charges.has_more,
        }
