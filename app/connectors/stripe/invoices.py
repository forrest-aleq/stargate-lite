"""
Stripe connector - Invoices module

Handles invoice CRUD and operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_config
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeInvoicesMixin:
    """Stripe invoice operations mixin"""

    @requires_stripe_config
    def create_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create an invoice for a customer"""
        customer_id = args.get("customer_id")
        description = args.get("description")
        metadata = args.get("metadata", {})

        logger.info(
            "Creating invoice",
            service="stripe",
            customer_id=customer_id,
            log_event="stripe_invoice_create",
        )

        metadata.update({"org_id": org_id, "user_id": user_id})

        create_kwargs: dict[str, Any] = {
            "customer": customer_id, "description": description, "metadata": metadata, "auto_advance": True
        }
        if stripe_config and stripe_config.get("stripe_account"):
            create_kwargs["stripe_account"] = stripe_config["stripe_account"]

        invoice = stripe.Invoice.create(**create_kwargs)

        logger.info(
            "Invoice created",
            service="stripe",
            invoice_id=invoice.id,
            amount_due=invoice.amount_due,
            log_event="stripe_invoice_created",
        )

        return {
            "invoice_id": invoice.id,
            "customer_id": invoice.customer,
            "status": invoice.status,
            "amount_due": invoice.amount_due,
            "hosted_invoice_url": invoice.hosted_invoice_url,
        }

    @requires_stripe_config
    def retrieve_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Retrieve an invoice"""
        invoice_id = args.get("invoice_id")

        retrieve_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            retrieve_kwargs["stripe_account"] = stripe_config["stripe_account"]

        invoice = stripe.Invoice.retrieve(invoice_id, **retrieve_kwargs)
        return {
            "invoice_id": invoice.id,
            "customer": invoice.customer,
            "status": invoice.status,
            "amount_due": invoice.amount_due,
            "amount_paid": invoice.amount_paid,
            "hosted_invoice_url": invoice.hosted_invoice_url,
        }

    @requires_stripe_config
    def update_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Update an invoice"""
        invoice_id = args.get("invoice_id")
        description = args.get("description")
        metadata = args.get("metadata", {})

        update_params: dict[str, Any] = {}
        if description:
            update_params["description"] = description
        if metadata:
            update_params["metadata"] = metadata
        if stripe_config and stripe_config.get("stripe_account"):
            update_params["stripe_account"] = stripe_config["stripe_account"]

        invoice = stripe.Invoice.modify(invoice_id, **update_params)
        return {"invoice_id": invoice.id, "status": invoice.status}

    @requires_stripe_config
    def finalize_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Finalize a draft invoice"""
        invoice_id = args.get("invoice_id")

        finalize_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            finalize_kwargs["stripe_account"] = stripe_config["stripe_account"]

        invoice = stripe.Invoice.finalize_invoice(invoice_id, **finalize_kwargs)
        return {"invoice_id": invoice.id, "status": invoice.status}

    @requires_stripe_config
    def pay_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Pay an invoice"""
        invoice_id = args.get("invoice_id")

        pay_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            pay_kwargs["stripe_account"] = stripe_config["stripe_account"]

        invoice = stripe.Invoice.pay(invoice_id, **pay_kwargs)
        return {"invoice_id": invoice.id, "status": invoice.status, "paid": invoice.paid}

    @requires_stripe_config
    def send_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send an invoice for manual payment"""
        invoice_id = args.get("invoice_id")

        send_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            send_kwargs["stripe_account"] = stripe_config["stripe_account"]

        invoice = stripe.Invoice.send_invoice(invoice_id, **send_kwargs)
        return {"invoice_id": invoice.id, "status": invoice.status}

    @requires_stripe_config
    def void_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Void an invoice"""
        invoice_id = args.get("invoice_id")

        void_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            void_kwargs["stripe_account"] = stripe_config["stripe_account"]

        invoice = stripe.Invoice.void_invoice(invoice_id, **void_kwargs)
        return {"invoice_id": invoice.id, "status": invoice.status}

    @requires_stripe_config
    def list_invoices(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """List invoices"""
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

        invoices = stripe.Invoice.list(**params)
        return {
            "invoices": [
                {
                    "invoice_id": i.id,
                    "customer": i.customer,
                    "status": i.status,
                    "amount_due": i.amount_due,
                    "amount_paid": i.amount_paid,
                }
                for i in invoices.data
            ],
            "has_more": invoices.has_more,
        }

    @requires_stripe_config
    def delete_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any],
        stripe_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Delete a draft invoice"""
        invoice_id = args.get("invoice_id")

        delete_kwargs: dict[str, Any] = {}
        if stripe_config and stripe_config.get("stripe_account"):
            delete_kwargs["stripe_account"] = stripe_config["stripe_account"]

        deleted = stripe.Invoice.delete(invoice_id, **delete_kwargs)
        return {"invoice_id": deleted.id, "deleted": deleted.deleted}
