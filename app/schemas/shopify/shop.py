"""Shopify Shop Capability Schemas."""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ReturnFieldSchema,
)

SHOPIFY_SHOP_GET = CapabilitySchema(
    capability_key="shopify.shop.get",
    service="shopify",
    category="shop",
    description="Get Shopify shop information",
    parameters={},
    returns={
        "id": ReturnFieldSchema(type="string", description="Shop ID"),
        "name": ReturnFieldSchema(type="string", description="Shop name"),
        "email": ReturnFieldSchema(type="string", description="Shop email"),
        "domain": ReturnFieldSchema(type="string", description="Primary domain"),
        "currency": ReturnFieldSchema(type="string", description="Currency code"),
        "timezone": ReturnFieldSchema(type="string", description="Timezone"),
        "plan_name": ReturnFieldSchema(type="string", description="Shopify plan"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Shopify credentials not configured",
            recovery_hint="User must connect Shopify store",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

SHOP_SCHEMAS = {
    "shopify.shop.get": SHOPIFY_SHOP_GET,
}
