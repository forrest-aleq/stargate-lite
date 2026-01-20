"""
Stripe Coupons & Promotions Capability Schemas.

Rich metadata for discount management.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ COUPONS ============

COUPON_CREATE = CapabilitySchema(
    capability_key="stripe.coupon.create",
    service="stripe",
    category="coupons",
    description="Create a coupon in Stripe",
    description_detailed=(
        "Creates a coupon that can be applied to customers, subscriptions, "
        "or invoices to provide a discount."
    ),
    parameters={
        "percent_off": ParameterSchema(
            type="number",
            required=False,
            description="Percentage discount (1-100)",
            example=25.0,
        ),
        "amount_off": ParameterSchema(
            type="integer",
            required=False,
            description="Fixed amount discount in cents",
        ),
        "currency": ParameterSchema(
            type="string",
            required=False,
            description="Currency (required if amount_off)",
        ),
        "duration": ParameterSchema(
            type="string",
            required=True,
            description="How long the discount applies",
            enum=["forever", "once", "repeating"],
            example="once",
        ),
        "duration_in_months": ParameterSchema(
            type="integer",
            required=False,
            description="Months for repeating duration",
        ),
        "id": ParameterSchema(
            type="string",
            required=False,
            description="Unique coupon code",
            example="SUMMER25",
        ),
        "name": ParameterSchema(
            type="string",
            required=False,
            description="Display name",
        ),
        "max_redemptions": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum redemption count",
        ),
        "redeem_by": ParameterSchema(
            type="integer",
            required=False,
            description="Unix timestamp redemption deadline",
        ),
        "applies_to": ParameterSchema(
            type="object",
            required=False,
            description="Product restrictions",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Coupon ID/code"),
        "percent_off": ReturnFieldSchema(type="number", description="Percent off"),
        "amount_off": ReturnFieldSchema(type="integer", description="Amount off"),
        "duration": ReturnFieldSchema(type="string", description="Duration"),
        "valid": ReturnFieldSchema(type="boolean", description="Is valid"),
        "times_redeemed": ReturnFieldSchema(type="integer", description="Redemptions"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Must specify percent_off or amount_off",
            recovery_hint="Provide exactly one discount type",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.promotion_code.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

COUPON_RETRIEVE = CapabilitySchema(
    capability_key="stripe.coupon.retrieve",
    service="stripe",
    category="coupons",
    description="Retrieve a coupon",
    parameters={
        "coupon_id": ParameterSchema(
            type="string",
            required=True,
            description="Coupon ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Coupon ID"),
        "percent_off": ReturnFieldSchema(type="number", description="Percent off"),
        "amount_off": ReturnFieldSchema(type="integer", description="Amount off"),
        "duration": ReturnFieldSchema(type="string", description="Duration"),
        "valid": ReturnFieldSchema(type="boolean", description="Is valid"),
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

COUPON_UPDATE = CapabilitySchema(
    capability_key="stripe.coupon.update",
    service="stripe",
    category="coupons",
    description="Update a coupon",
    parameters={
        "coupon_id": ParameterSchema(
            type="string",
            required=True,
            description="Coupon ID to update",
        ),
        "name": ParameterSchema(
            type="string",
            required=False,
            description="New display name",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Coupon ID"),
        "name": ReturnFieldSchema(type="string", description="Updated name"),
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

COUPON_DELETE = CapabilitySchema(
    capability_key="stripe.coupon.delete",
    service="stripe",
    category="coupons",
    description="Delete a coupon",
    description_detailed=("Deletes a coupon. Existing discounts using the coupon remain valid."),
    parameters={
        "coupon_id": ParameterSchema(
            type="string",
            required=True,
            description="Coupon ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted coupon ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

COUPON_LIST = CapabilitySchema(
    capability_key="stripe.coupon.list",
    service="stripe",
    category="coupons",
    description="List coupons",
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of coupons"),
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

# ============ PROMOTION CODES ============

PROMOTION_CODE_CREATE = CapabilitySchema(
    capability_key="stripe.promotion_code.create",
    service="stripe",
    category="coupons",
    description="Create a promotion code",
    description_detailed=(
        "Creates a promotion code that customers can enter to apply a coupon. "
        "Promotion codes can have restrictions like customer, date, or usage limits."
    ),
    parameters={
        "coupon": ParameterSchema(
            type="string",
            required=True,
            description="Coupon ID this code applies",
        ),
        "code": ParameterSchema(
            type="string",
            required=False,
            description="The customer-facing code",
            example="NEWCUSTOMER",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Whether code is active",
            default=True,
        ),
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Restrict to specific customer",
        ),
        "expires_at": ParameterSchema(
            type="integer",
            required=False,
            description="Expiration timestamp",
        ),
        "max_redemptions": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of redemptions",
        ),
        "restrictions": ParameterSchema(
            type="object",
            required=False,
            description="Usage restrictions",
            example={
                "first_time_transaction": True,
                "minimum_amount": 5000,
            },
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Promotion code ID"),
        "code": ReturnFieldSchema(type="string", description="The code"),
        "coupon": ReturnFieldSchema(type="string", description="Coupon ID"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "times_redeemed": ReturnFieldSchema(type="integer", description="Redemptions"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Code already exists or invalid coupon",
            recovery_hint="Use unique code and verify coupon exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.coupon.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

PROMOTION_CODE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.promotion_code.retrieve",
    service="stripe",
    category="coupons",
    description="Retrieve a promotion code",
    parameters={
        "promotion_code_id": ParameterSchema(
            type="string",
            required=True,
            description="Promotion code ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Promotion code ID"),
        "code": ReturnFieldSchema(type="string", description="The code"),
        "coupon": ReturnFieldSchema(type="object", description="Coupon details"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "restrictions": ReturnFieldSchema(type="object", description="Restrictions"),
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

PROMOTION_CODE_UPDATE = CapabilitySchema(
    capability_key="stripe.promotion_code.update",
    service="stripe",
    category="coupons",
    description="Update a promotion code",
    parameters={
        "promotion_code_id": ParameterSchema(
            type="string",
            required=True,
            description="Promotion code ID to update",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Activate or deactivate",
        ),
        "restrictions": ParameterSchema(
            type="object",
            required=False,
            description="Update restrictions",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Promotion code ID"),
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

PROMOTION_CODE_LIST = CapabilitySchema(
    capability_key="stripe.promotion_code.list",
    service="stripe",
    category="coupons",
    description="List promotion codes",
    parameters={
        "coupon": ParameterSchema(
            type="string",
            required=False,
            description="Filter by coupon ID",
        ),
        "code": ParameterSchema(
            type="string",
            required=False,
            description="Filter by code",
        ),
        "active": ParameterSchema(
            type="boolean",
            required=False,
            description="Filter by active status",
        ),
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of promotion codes"),
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

COUPON_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.coupon.create": COUPON_CREATE,
    "stripe.coupon.retrieve": COUPON_RETRIEVE,
    "stripe.coupon.update": COUPON_UPDATE,
    "stripe.coupon.delete": COUPON_DELETE,
    "stripe.coupon.list": COUPON_LIST,
    "stripe.promotion_code.create": PROMOTION_CODE_CREATE,
    "stripe.promotion_code.retrieve": PROMOTION_CODE_RETRIEVE,
    "stripe.promotion_code.update": PROMOTION_CODE_UPDATE,
    "stripe.promotion_code.list": PROMOTION_CODE_LIST,
}
