"""
Stripe connector - Customers module

Handles customer CRUD operations.
"""

from typing import Any

import stripe

from app.connectors.stripe.base import requires_stripe_init
from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeCustomersMixin:
    """Stripe customer operations mixin"""

    @requires_stripe_init
    def create_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a Stripe customer"""
        email = args.get("email")
        name = args.get("name")
        phone = args.get("phone")
        metadata = dict(args.get("metadata", {}))  # Copy to avoid mutating caller's dict

        logger.info(
            "Creating customer", service="stripe", email=email, log_event="stripe_customer_create"
        )

        metadata.update({"org_id": org_id, "user_id": user_id})

        customer = stripe.Customer.create(email=email, name=name, phone=phone, metadata=metadata)

        logger.info(
            "Customer created",
            service="stripe",
            customer_id=customer.id,
            log_event="stripe_customer_created",
        )

        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "created_at": customer.created,
        }

    @requires_stripe_init
    def search_customers(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search for customers"""
        query = args.get("query")  # e.g., "email:'john@example.com'" or "name:'John Doe'"
        if not query:
            raise ValueError("query is required")
        limit = args.get("limit", 10)

        customers = stripe.Customer.search(query=query, limit=limit)
        return {
            "customers": [
                {"customer_id": c.id, "email": c.email, "name": c.name} for c in customers.data
            ],
            "has_more": customers.has_more,
        }

    @requires_stripe_init
    def retrieve_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Retrieve a customer"""
        customer_id = args.get("customer_id")
        if not customer_id:
            raise ValueError("customer_id is required")
        customer = stripe.Customer.retrieve(customer_id)
        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "phone": customer.phone,
            "created": customer.created,
            "default_source": customer.default_source,
        }

    @requires_stripe_init
    def update_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a customer"""
        customer_id = args.get("customer_id")
        if not customer_id:
            raise ValueError("customer_id is required")
        email = args.get("email")
        name = args.get("name")
        phone = args.get("phone")
        metadata = args.get("metadata", {})

        update_params: dict[str, Any] = {}
        if email:
            update_params["email"] = email
        if name:
            update_params["name"] = name
        if phone:
            update_params["phone"] = phone
        if metadata:
            update_params["metadata"] = metadata

        customer = stripe.Customer.modify(customer_id, **update_params)
        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "phone": customer.phone,
        }

    @requires_stripe_init
    def list_customers(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List customers"""
        limit = args.get("limit", 10)
        email = args.get("email")

        params: dict[str, Any] = {"limit": limit}
        if email:
            params["email"] = email

        customers = stripe.Customer.list(**params)
        return {
            "customers": [
                {"customer_id": c.id, "email": c.email, "name": c.name} for c in customers.data
            ],
            "has_more": customers.has_more,
        }

    @requires_stripe_init
    def delete_customer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a customer"""
        customer_id = args.get("customer_id")
        if not customer_id:
            raise ValueError("customer_id is required")
        deleted = stripe.Customer.delete(customer_id)
        return {"customer_id": deleted.id, "deleted": deleted.deleted}
