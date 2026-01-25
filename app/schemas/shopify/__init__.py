"""
Shopify Capability Schemas.

Rich metadata for Shopify e-commerce operations via Admin API.
Finance teams use Shopify for order management, revenue tracking, and reconciliation.

API Docs: https://shopify.dev/docs/api/admin-rest
"""

from app.schemas.shopify.customers import CUSTOMER_SCHEMAS
from app.schemas.shopify.fulfillment import FULFILLMENT_SCHEMAS
from app.schemas.shopify.orders import ORDER_SCHEMAS
from app.schemas.shopify.payments import PAYMENT_SCHEMAS
from app.schemas.shopify.products import PRODUCT_SCHEMAS
from app.schemas.shopify.shop import SHOP_SCHEMAS

from app.schemas.base import CapabilitySchema

# Export all schemas
SHOPIFY_SCHEMAS: dict[str, CapabilitySchema] = {
    **SHOP_SCHEMAS,
    **ORDER_SCHEMAS,
    **PAYMENT_SCHEMAS,
    **CUSTOMER_SCHEMAS,
    **PRODUCT_SCHEMAS,
    **FULFILLMENT_SCHEMAS,
}

__all__ = ["SHOPIFY_SCHEMAS"]
