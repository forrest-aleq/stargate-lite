"""Shopify Product Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
)

SHOPIFY_PRODUCTS_LIST = CapabilitySchema(
    capability_key="shopify.products.list",
    service="shopify",
    category="products",
    description="List products from Shopify",
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            enum=["active", "archived", "draft"],
            description="Product status filter",
        ),
        "product_type": ParameterSchema(
            type="string", required=False, description="Filter by product type"
        ),
        "vendor": ParameterSchema(
            type="string", required=False, description="Filter by vendor name"
        ),
        "limit": ParameterSchema(
            type="integer", required=False, description="Maximum products to return"
        ),
    },
    returns={
        "products": ReturnFieldSchema(
            type="array",
            description="Products with id, title, vendor, product_type, variants",
        ),
        "count": ReturnFieldSchema(type="integer", description="Product count"),
    },
    idempotent=True,
    has_side_effects=False,
)

PRODUCT_SCHEMAS = {
    "shopify.products.list": SHOPIFY_PRODUCTS_LIST,
}
