"""
Stripe Checkout Capability Schemas.

Rich metadata for Checkout Sessions.
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

CHECKOUT_SESSION_CREATE = CapabilitySchema(
    capability_key="stripe.checkout.session.create",
    service="stripe",
    category="checkout",
    description="Create a Checkout Session in Stripe",
    description_detailed=(
        "Creates a Checkout Session for collecting payment. Stripe Checkout is a "
        "pre-built, hosted payment page that handles card input, validation, and "
        "3D Secure authentication. Supports one-time and subscription payments."
    ),
    parameters={
        "mode": ParameterSchema(
            type="string",
            required=True,
            description="Checkout mode",
            enum=["payment", "subscription", "setup"],
            example="payment",
        ),
        "success_url": ParameterSchema(
            type="string",
            required=True,
            description="URL to redirect after successful payment",
            example="https://example.com/success?session_id={CHECKOUT_SESSION_ID}",
        ),
        "cancel_url": ParameterSchema(
            type="string",
            required=False,
            description="URL to redirect if customer cancels",
            example="https://example.com/cancel",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=False,
            description="Line items for the checkout (price or price_data)",
            items_type="object",
            example=[{"price": "price_ABC123", "quantity": 1}],
        ),
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Existing customer ID",
        ),
        "customer_email": ParameterSchema(
            type="string",
            required=False,
            description="Pre-fill customer email",
        ),
        "client_reference_id": ParameterSchema(
            type="string",
            required=False,
            description="Your reference ID for this session",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your own use",
        ),
        "payment_method_types": ParameterSchema(
            type="array",
            required=False,
            description="Allowed payment methods",
            items_type="string",
            example=["card"],
        ),
        "allow_promotion_codes": ParameterSchema(
            type="boolean",
            required=False,
            description="Allow promotion codes",
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
            description="Collect shipping address (allowed_countries)",
        ),
        "expires_at": ParameterSchema(
            type="integer",
            required=False,
            description="Unix timestamp when session expires",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Checkout Session ID",
            example="cs_ABC123",
        ),
        "url": ReturnFieldSchema(
            type="string",
            description="Checkout page URL to redirect customer",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Session status (open, complete, expired)",
        ),
        "payment_status": ReturnFieldSchema(
            type="string",
            description="Payment status (unpaid, paid, no_payment_required)",
        ),
        "customer": ReturnFieldSchema(type="string", description="Customer ID if created"),
        "payment_intent": ReturnFieldSchema(type="string", description="PaymentIntent ID"),
        "subscription": ReturnFieldSchema(
            type="string", description="Subscription ID if mode=subscription"
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid line items or URLs",
            recovery_hint="Verify price IDs exist and URLs are valid",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.product.create", "stripe.price.create"],
        typically_followed_by=["stripe.checkout.session.retrieve", "stripe.payment.retrieve"],
        related_capabilities=["stripe.subscription.create", "stripe.payment.create"],
    ),
    examples=[
        UsageExample(
            description="Create a one-time payment checkout",
            args={
                "mode": "payment",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
                "line_items": [{"price": "price_ABC123", "quantity": 1}],
            },
        ),
        UsageExample(
            description="Create a subscription checkout",
            args={
                "mode": "subscription",
                "success_url": "https://example.com/success",
                "line_items": [{"price": "price_monthly", "quantity": 1}],
                "customer_email": "customer@example.com",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CHECKOUT_SESSION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.checkout.session.retrieve",
    service="stripe",
    category="checkout",
    description="Retrieve a Checkout Session in Stripe",
    description_detailed=(
        "Retrieves a Checkout Session. Use to verify payment completion after "
        "customer returns from the hosted checkout page."
    ),
    parameters={
        "session_id": ParameterSchema(
            type="string",
            required=True,
            description="Checkout Session ID",
            example="cs_ABC123",
        ),
        "expand": ParameterSchema(
            type="array",
            required=False,
            description="Objects to expand (e.g., line_items, customer)",
            items_type="string",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Session ID"),
        "status": ReturnFieldSchema(type="string", description="Session status"),
        "payment_status": ReturnFieldSchema(type="string", description="Payment status"),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
        "customer_email": ReturnFieldSchema(type="string", description="Customer email"),
        "amount_total": ReturnFieldSchema(type="integer", description="Total in cents"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "payment_intent": ReturnFieldSchema(type="string", description="PaymentIntent ID"),
        "subscription": ReturnFieldSchema(type="string", description="Subscription ID"),
        "metadata": ReturnFieldSchema(type="object", description="Metadata"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Session not found",
            recovery_hint="Verify session_id is correct",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

CHECKOUT_SESSION_EXPIRE = CapabilitySchema(
    capability_key="stripe.checkout.session.expire",
    service="stripe",
    category="checkout",
    description="Expire a Checkout Session in Stripe",
    description_detailed=(
        "Expires an open Checkout Session, preventing it from being completed. "
        "Useful for invalidating sessions that are no longer valid."
    ),
    parameters={
        "session_id": ParameterSchema(
            type="string",
            required=True,
            description="Checkout Session ID to expire",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Session ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'expired'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Session already completed or expired",
            recovery_hint="Only open sessions can be expired",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CHECKOUT_SESSION_LIST = CapabilitySchema(
    capability_key="stripe.checkout.session.list",
    service="stripe",
    category="checkout",
    description="List Checkout Sessions in Stripe",
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer ID",
        ),
        "payment_intent": ParameterSchema(
            type="string",
            required=False,
            description="Filter by payment intent ID",
        ),
        "subscription": ParameterSchema(
            type="string",
            required=False,
            description="Filter by subscription ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return (1-100)",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of sessions"),
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

CHECKOUT_LINE_ITEMS_LIST = CapabilitySchema(
    capability_key="stripe.checkout.lineitems.list",
    service="stripe",
    category="checkout",
    description="List line items for a Checkout Session",
    description_detailed=(
        "Retrieves the line items for a Checkout Session. Line items show what "
        "the customer purchased or will purchase."
    ),
    parameters={
        "session_id": ParameterSchema(
            type="string",
            required=True,
            description="Checkout Session ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(
            type="array",
            description="List of line items with price, quantity, amount",
        ),
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

CHECKOUT_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.checkout.session.create": CHECKOUT_SESSION_CREATE,
    "stripe.checkout.session.retrieve": CHECKOUT_SESSION_RETRIEVE,
    "stripe.checkout.session.expire": CHECKOUT_SESSION_EXPIRE,
    "stripe.checkout.session.list": CHECKOUT_SESSION_LIST,
    "stripe.checkout.lineitems.list": CHECKOUT_LINE_ITEMS_LIST,
}
