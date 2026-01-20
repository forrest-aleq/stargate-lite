"""
Stripe Payment Links Capability Schemas.

Rich metadata for no-code payment collection links.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ PAYMENT LINKS ============

PAYMENT_LINK_CREATE = CapabilitySchema(
    capability_key="stripe.payment_link.create",
    service="stripe",
    category="payment_links",
    description="Create a Payment Link",
    description_detailed=(
        "Creates a shareable payment link for no-code payment collection. "
        "Customers can pay by visiting the URL without needing a website."
    ),
    parameters={
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Items to sell",
            items_type="object",
            example=[{"price": "price_ABC123", "quantity": 1}],
        ),
        "after_completion": ParameterSchema(
            type="object",
            required=False,
            description="Post-payment behavior",
            example={
                "type": "redirect",
                "redirect": {"url": "https://example.com/thanks"},
            },
        ),
        "allow_promotion_codes": ParameterSchema(
            type="boolean",
            required=False,
            description="Allow promo codes",
            default=False,
        ),
        "billing_address_collection": ParameterSchema(
            type="string",
            required=False,
            description="Collect billing address",
            enum=["auto", "required"],
        ),
        "shipping_address_collection": ParameterSchema(
            type="object",
            required=False,
            description="Collect shipping address",
        ),
        "customer_creation": ParameterSchema(
            type="string",
            required=False,
            description="When to create customer",
            enum=["always", "if_required"],
        ),
        "payment_method_types": ParameterSchema(
            type="array",
            required=False,
            description="Allowed payment methods",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Payment link ID",
            example="plink_ABC123",
        ),
        "url": ReturnFieldSchema(type="string", description="Shareable URL"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "line_items": ReturnFieldSchema(type="object", description="Items"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid price IDs or configuration",
            recovery_hint="Verify price IDs exist and are active",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

PAYMENT_LINK_RETRIEVE = CapabilitySchema(
    capability_key="stripe.payment_link.retrieve",
    service="stripe",
    category="payment_links",
    description="Retrieve a Payment Link",
    parameters={
        "payment_link_id": ParameterSchema(
            type="string",
            required=True,
            description="Payment link ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Payment link ID"),
        "url": ReturnFieldSchema(type="string", description="URL"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "line_items": ReturnFieldSchema(type="object", description="Items"),
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

PAYMENT_LINK_UPDATE = CapabilitySchema(
    capability_key="stripe.payment_link.update",
    service="stripe",
    category="payment_links",
    description="Update a Payment Link",
    parameters={
        "payment_link_id": ParameterSchema(
            type="string",
            required=True,
            description="Payment link ID to update",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Activate or deactivate",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=False,
            description="Update line items",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Payment link ID"),
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
    has_side_effects=True,
)

PAYMENT_LINK_LIST = CapabilitySchema(
    capability_key="stripe.payment_link.list",
    service="stripe",
    category="payment_links",
    description="List Payment Links",
    parameters={
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Filter by active status",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of payment links"),
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

PAYMENT_LINK_LINE_ITEMS_LIST = CapabilitySchema(
    capability_key="stripe.payment_link.line_items.list",
    service="stripe",
    category="payment_links",
    description="List line items for a Payment Link",
    parameters={
        "payment_link_id": ParameterSchema(
            type="string",
            required=True,
            description="Payment link ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="Line items"),
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

PAYMENT_LINK_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.payment_link.create": PAYMENT_LINK_CREATE,
    "stripe.payment_link.retrieve": PAYMENT_LINK_RETRIEVE,
    "stripe.payment_link.update": PAYMENT_LINK_UPDATE,
    "stripe.payment_link.list": PAYMENT_LINK_LIST,
    "stripe.payment_link.line_items.list": PAYMENT_LINK_LINE_ITEMS_LIST,
}
