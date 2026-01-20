"""
Stripe Price Capability Schemas.

Rich metadata for price operations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    UsageExample,
    WorkflowHints,
)

PRICE_CREATE = CapabilitySchema(
    capability_key="stripe.price.create",
    service="stripe",
    category="prices",
    description="Create a price in Stripe",
    description_detailed=(
        "Creates a new price for a product. Prices define how much and how often "
        "to charge. A product can have multiple prices (e.g., monthly vs annual)."
    ),
    parameters={
        "product": ParameterSchema(
            type="string",
            required=True,
            description="Product ID this price is for",
            example="prod_ABC123",
        ),
        "unit_amount": ParameterSchema(
            type="integer",
            required=False,
            description="Price in smallest currency unit (cents)",
            example=1999,
        ),
        "currency": ParameterSchema(
            type="string",
            required=True,
            description="Three-letter ISO currency code",
            example="usd",
        ),
        "recurring": ParameterSchema(
            type="object",
            required=False,
            description="Recurring billing configuration",
            example={"interval": "month", "interval_count": 1},
        ),
        "nickname": ParameterSchema(
            type="string",
            required=False,
            description="Brief description (for your reference)",
        ),
        "billing_scheme": ParameterSchema(
            type="string",
            required=False,
            description="How to compute the price",
            enum=["per_unit", "tiered"],
            default="per_unit",
        ),
        "tiers": ParameterSchema(
            type="array",
            required=False,
            description="Pricing tiers (if billing_scheme is tiered)",
        ),
        "tiers_mode": ParameterSchema(
            type="string",
            required=False,
            description="How tiers are applied",
            enum=["graduated", "volume"],
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your own use",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Price ID",
            example="price_ABC123",
        ),
        "product": ReturnFieldSchema(type="string", description="Product ID"),
        "unit_amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "currency": ReturnFieldSchema(type="string", description="Currency code"),
        "recurring": ReturnFieldSchema(type="object", description="Recurring config"),
        "type": ReturnFieldSchema(type="string", description="one_time or recurring"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid product ID or price configuration",
            recovery_hint="Verify product exists and price params are valid",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.product.create"],
        typically_followed_by=["stripe.subscription.create", "stripe.checkout.session.create"],
    ),
    examples=[
        UsageExample(
            description="Create a monthly recurring price",
            args={
                "product": "prod_ABC123",
                "unit_amount": 2999,
                "currency": "usd",
                "recurring": {"interval": "month"},
                "nickname": "Monthly Plan",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

PRICE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.price.retrieve",
    service="stripe",
    category="prices",
    description="Retrieve a price in Stripe",
    parameters={
        "price_id": ParameterSchema(
            type="string",
            required=True,
            description="Price ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Price ID"),
        "product": ReturnFieldSchema(type="string", description="Product ID"),
        "unit_amount": ReturnFieldSchema(type="integer", description="Amount"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "recurring": ReturnFieldSchema(type="object", description="Recurring config"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

PRICE_UPDATE = CapabilitySchema(
    capability_key="stripe.price.update",
    service="stripe",
    category="prices",
    description="Update a price in Stripe",
    description_detailed=(
        "Updates a price. Most fields are immutable after creation - you can only "
        "update metadata, nickname, and active status."
    ),
    parameters={
        "price_id": ParameterSchema(
            type="string",
            required=True,
            description="Price ID to update",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Set active status",
        ),
        "nickname": ParameterSchema(
            type="string",
            required=False,
            description="Update nickname",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Price ID"),
        "active": ReturnFieldSchema(type="boolean", description="Active status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

PRICE_LIST = CapabilitySchema(
    capability_key="stripe.price.list",
    service="stripe",
    category="prices",
    description="List prices in Stripe",
    parameters={
        "product": ParameterSchema(
            type="string",
            required=False,
            description="Filter by product ID",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Filter by active status",
        ),
        "type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by type",
            enum=["one_time", "recurring"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of price objects"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

PRICE_SEARCH = CapabilitySchema(
    capability_key="stripe.price.search",
    service="stripe",
    category="prices",
    description="Search prices in Stripe",
    parameters={
        "query": ParameterSchema(
            type="string",
            required=True,
            description="Search query string",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="Matching prices"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

PRICE_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.price.create": PRICE_CREATE,
    "stripe.price.retrieve": PRICE_RETRIEVE,
    "stripe.price.update": PRICE_UPDATE,
    "stripe.price.list": PRICE_LIST,
    "stripe.price.search": PRICE_SEARCH,
}
