"""
Stripe connector - Invoices module

Handles invoice CRUD and operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_init
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeInvoicesMixin:
    """Stripe invoice operations mixin"""

    @requires_stripe_init
    def create_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
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

        invoice = stripe.Invoice.create(
            customer=customer_id, description=description, metadata=metadata, auto_advance=True
        )

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

    @requires_stripe_init
    def retrieve_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Retrieve an invoice"""
        invoice_id = args.get("invoice_id")
        invoice = stripe.Invoice.retrieve(invoice_id)
        return {
            "invoice_id": invoice.id,
            "customer": invoice.customer,
            "status": invoice.status,
            "amount_due": invoice.amount_due,
            "amount_paid": invoice.amount_paid,
            "hosted_invoice_url": invoice.hosted_invoice_url,
        }

    @requires_stripe_init
    def update_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an invoice"""
        invoice_id = args.get("invoice_id")
        description = args.get("description")
        metadata = args.get("metadata", {})

        update_params: dict[str, Any] = {}
        if description:
            update_params["description"] = description
        if metadata:
            update_params["metadata"] = metadata

        invoice = stripe.Invoice.modify(invoice_id, **update_params)
        return {"invoice_id": invoice.id, "status": invoice.status}

    @requires_stripe_init
    def finalize_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Finalize a draft invoice"""
        invoice_id = args.get("invoice_id")
        invoice = stripe.Invoice.finalize_invoice(invoice_id)
        return {"invoice_id": invoice.id, "status": invoice.status}

    @requires_stripe_init
    def pay_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Pay an invoice"""
        invoice_id = args.get("invoice_id")
        invoice = stripe.Invoice.pay(invoice_id)
        return {"invoice_id": invoice.id, "status": invoice.status, "paid": invoice.paid}

    @requires_stripe_init
    def send_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send an invoice for manual payment"""
        invoice_id = args.get("invoice_id")
        invoice = stripe.Invoice.send_invoice(invoice_id)
        return {"invoice_id": invoice.id, "status": invoice.status}

    @requires_stripe_init
    def void_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Void an invoice"""
        invoice_id = args.get("invoice_id")
        invoice = stripe.Invoice.void_invoice(invoice_id)
        return {"invoice_id": invoice.id, "status": invoice.status}

    @requires_stripe_init
    def list_invoices(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List invoices"""
        limit = args.get("limit", 10)
        customer = args.get("customer_id")
        status = args.get("status")

        params: dict[str, Any] = {"limit": limit}
        if customer:
            params["customer"] = customer
        if status:
            params["status"] = status

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

    @requires_stripe_init
    def delete_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a draft invoice"""
        invoice_id = args.get("invoice_id")
        deleted = stripe.Invoice.delete(invoice_id)
        return {"invoice_id": deleted.id, "deleted": deleted.deleted}
