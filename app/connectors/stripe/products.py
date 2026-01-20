"""
Stripe connector - Products and Prices module

Handles product and price CRUD operations.
"""

from typing import Any

import stripe

from app.logging_config import get_logger

logger = get_logger(__name__)


class StripeProductsMixin:
    """Stripe product and price operations mixin"""

    def create_product(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a product"""
        name = args.get("name")
        description = args.get("description")
        metadata = args.get("metadata", {})
        active = args.get("active", True)

        metadata.update({"org_id": org_id, "user_id": user_id})

        product = stripe.Product.create(
            name=name, description=description, metadata=metadata, active=active
        )
        return {
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "active": product.active,
        }

    def retrieve_product(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Retrieve a product"""
        product_id = args.get("product_id")
        product = stripe.Product.retrieve(product_id)
        return {
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "active": product.active,
            "default_price": product.default_price,
        }

    def update_product(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a product"""
        product_id = args.get("product_id")
        name = args.get("name")
        description = args.get("description")
        active = args.get("active")

        update_params: dict[str, Any] = {}
        if name:
            update_params["name"] = name
        if description:
            update_params["description"] = description
        if active is not None:
            update_params["active"] = active

        product = stripe.Product.modify(product_id, **update_params)
        return {
            "product_id": product.id,
            "name": product.name,
            "description": product.description,
            "active": product.active,
        }

    def list_products(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List products"""
        limit = args.get("limit", 10)
        active = args.get("active")

        params: dict[str, Any] = {"limit": limit}
        if active is not None:
            params["active"] = active

        products = stripe.Product.list(**params)
        return {
            "products": [
                {
                    "product_id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "active": p.active,
                }
                for p in products.data
            ],
            "has_more": products.has_more,
        }

    def delete_product(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete a product"""
        product_id = args.get("product_id")
        deleted = stripe.Product.delete(product_id)
        return {"product_id": deleted.id, "deleted": deleted.deleted}

    def search_products(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search for products"""
        query = args.get("query")  # e.g., "name:'Premium'" or "active:'true'"
        limit = args.get("limit", 10)

        products = stripe.Product.search(query=query, limit=limit)
        return {
            "products": [
                {
                    "product_id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "active": p.active,
                }
                for p in products.data
            ],
            "has_more": products.has_more,
        }

    def create_price(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a price for a product"""
        product_id = args.get("product_id")
        unit_amount = args.get("unit_amount")  # Amount in cents
        currency = args.get("currency", "usd")
        recurring = args.get("recurring")  # e.g., {"interval": "month"}
        metadata = args.get("metadata", {})

        metadata.update({"org_id": org_id, "user_id": user_id})

        price_params: dict[str, Any] = {
            "product": product_id,
            "unit_amount": unit_amount,
            "currency": currency,
            "metadata": metadata,
        }
        if recurring:
            price_params["recurring"] = recurring

        price = stripe.Price.create(**price_params)
        return {
            "price_id": price.id,
            "product": price.product,
            "unit_amount": price.unit_amount,
            "currency": price.currency,
            "type": price.type,
        }

    def retrieve_price(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Retrieve a price"""
        price_id = args.get("price_id")
        price = stripe.Price.retrieve(price_id)
        return {
            "price_id": price.id,
            "product": price.product,
            "unit_amount": price.unit_amount,
            "currency": price.currency,
            "active": price.active,
            "type": price.type,
        }

    def update_price(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update a price"""
        price_id = args.get("price_id")
        active = args.get("active")
        metadata = args.get("metadata", {})

        update_params: dict[str, Any] = {}
        if active is not None:
            update_params["active"] = active
        if metadata:
            update_params["metadata"] = metadata

        price = stripe.Price.modify(price_id, **update_params)
        return {
            "price_id": price.id,
            "active": price.active,
            "metadata": price.metadata,
        }

    def list_prices(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List prices"""
        limit = args.get("limit", 10)
        product = args.get("product_id")
        active = args.get("active")

        params: dict[str, Any] = {"limit": limit}
        if product:
            params["product"] = product
        if active is not None:
            params["active"] = active

        prices = stripe.Price.list(**params)
        return {
            "prices": [
                {
                    "price_id": p.id,
                    "product": p.product,
                    "unit_amount": p.unit_amount,
                    "currency": p.currency,
                    "active": p.active,
                }
                for p in prices.data
            ],
            "has_more": prices.has_more,
        }

    def search_prices(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Search for prices"""
        query = args.get("query")  # e.g., "product:'prod_xxx'" or "active:'true'"
        limit = args.get("limit", 10)

        prices = stripe.Price.search(query=query, limit=limit)
        return {
            "prices": [
                {
                    "price_id": p.id,
                    "product": p.product,
                    "unit_amount": p.unit_amount,
                    "currency": p.currency,
                    "active": p.active,
                }
                for p in prices.data
            ],
            "has_more": prices.has_more,
        }
