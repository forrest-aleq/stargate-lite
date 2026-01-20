"""
Stripe Product Capability Schemas.

Rich metadata for product operations.
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

PRODUCT_CREATE = CapabilitySchema(
    capability_key="stripe.product.create",
    service="stripe",
    category="products",
    description="Create a product in Stripe",
    description_detailed=(
        "Creates a new product object in Stripe. Products represent goods or services "
        "you sell. After creating a product, create prices to define how much to charge."
    ),
    parameters={
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Product name displayed to customers",
            example="Premium Plan",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Product description",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Whether product is available for purchase",
            default=True,
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your own use",
        ),
        "images": ParameterSchema(
            type="array",
            required=False,
            description="URLs of product images",
            items_type="string",
        ),
        "default_price_data": ParameterSchema(
            type="object",
            required=False,
            description="Create default price alongside product",
            example={"unit_amount": 1999, "currency": "usd"},
        ),
        "tax_code": ParameterSchema(
            type="string",
            required=False,
            description="Tax code for automatic tax calculation",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Product ID",
            example="prod_ABC123",
        ),
        "name": ReturnFieldSchema(type="string", description="Product name"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "default_price": ReturnFieldSchema(type="string", description="Default price ID"),
        "created": ReturnFieldSchema(type="integer", description="Unix timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.price.create", "stripe.checkout.session.create"],
        related_capabilities=["stripe.product.list", "stripe.product.update"],
    ),
    examples=[
        UsageExample(
            description="Create a SaaS product with default price",
            args={
                "name": "Pro Plan",
                "description": "Full access to all features",
                "default_price_data": {
                    "unit_amount": 2999,
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                },
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

PRODUCT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.product.retrieve",
    service="stripe",
    category="products",
    description="Retrieve a product in Stripe",
    parameters={
        "product_id": ParameterSchema(
            type="string",
            required=True,
            description="Product ID",
            example="prod_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Product ID"),
        "name": ReturnFieldSchema(type="string", description="Product name"),
        "description": ReturnFieldSchema(type="string", description="Description"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "default_price": ReturnFieldSchema(type="string", description="Default price ID"),
        "metadata": ReturnFieldSchema(type="object", description="Metadata"),
        "images": ReturnFieldSchema(type="array", description="Image URLs"),
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

PRODUCT_UPDATE = CapabilitySchema(
    capability_key="stripe.product.update",
    service="stripe",
    category="products",
    description="Update a product in Stripe",
    parameters={
        "product_id": ParameterSchema(
            type="string",
            required=True,
            description="Product ID to update",
        ),
        "name": ParameterSchema(
            type="string",
            required=False,
            description="New product name",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="New description",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Set active status",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
        "default_price": ParameterSchema(
            type="string",
            required=False,
            description="New default price ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Product ID"),
        "name": ReturnFieldSchema(type="string", description="Updated name"),
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

PRODUCT_LIST = CapabilitySchema(
    capability_key="stripe.product.list",
    service="stripe",
    category="products",
    description="List products in Stripe",
    parameters={
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Filter by active status",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return (1-100)",
            default=10,
        ),
        "starting_after": ParameterSchema(
            type="string",
            required=False,
            description="Cursor for pagination",
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of product objects"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results available"),
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

PRODUCT_DELETE = CapabilitySchema(
    capability_key="stripe.product.delete",
    service="stripe",
    category="products",
    description="Delete a product in Stripe",
    description_detailed=(
        "Deletes a product. Products can only be deleted if they have no prices "
        "associated with them."
    ),
    parameters={
        "product_id": ParameterSchema(
            type="string",
            required=True,
            description="Product ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted product ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Product has associated prices",
            recovery_hint="Archive prices first or set product to inactive instead",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

PRODUCT_SEARCH = CapabilitySchema(
    capability_key="stripe.product.search",
    service="stripe",
    category="products",
    description="Search products in Stripe",
    parameters={
        "query": ParameterSchema(
            type="string",
            required=True,
            description="Search query string",
            example="name~'Premium' AND active:'true'",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="Matching products"),
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

PRODUCT_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.product.create": PRODUCT_CREATE,
    "stripe.product.retrieve": PRODUCT_RETRIEVE,
    "stripe.product.update": PRODUCT_UPDATE,
    "stripe.product.list": PRODUCT_LIST,
    "stripe.product.delete": PRODUCT_DELETE,
    "stripe.product.search": PRODUCT_SEARCH,
}
