"""
Stripe Payment Capability Schemas.

Rich metadata for payment intents, refunds, and charges.
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

# ============ PAYMENT INTENTS ============

PAYMENT_CREATE = CapabilitySchema(
    capability_key="stripe.payment.create",
    service="stripe",
    category="payments",
    description="Create a payment intent in Stripe",
    description_detailed=(
        "Creates a PaymentIntent object to represent your intent to collect payment. "
        "PaymentIntents track the lifecycle of a payment from creation through checkout. "
        "Use for one-time payments; for recurring, use subscriptions instead."
    ),
    parameters={
        "amount": ParameterSchema(
            type="integer",
            required=True,
            description="Amount in smallest currency unit (cents for USD)",
            example=2000,
        ),
        "currency": ParameterSchema(
            type="string",
            required=True,
            description="Three-letter ISO currency code (lowercase)",
            example="usd",
        ),
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Stripe customer ID to associate with payment",
            example="cus_ABC123",
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method ID to use",
            example="pm_card_visa",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Description for the payment (appears in dashboard)",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your own use",
        ),
        "confirm": ParameterSchema(
            type="boolean",
            required=False,
            description="Immediately confirm and attempt payment",
            default=False,
        ),
        "automatic_payment_methods": ParameterSchema(
            type="object",
            required=False,
            description="Enable automatic payment method selection",
            example={"enabled": True},
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="PaymentIntent ID",
            example="pi_3ABC123",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Payment status",
            example="requires_payment_method",
        ),
        "amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "currency": ReturnFieldSchema(type="string", description="Currency code"),
        "client_secret": ReturnFieldSchema(
            type="string",
            description="Client secret for frontend confirmation",
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
            description="Invalid amount, currency, or payment method",
            recovery_hint="Verify amount > 0 and currency is valid ISO code",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.customer.create", "stripe.paymentmethod.create"],
        typically_followed_by=["stripe.payment.retrieve", "stripe.charge.retrieve"],
        related_capabilities=["stripe.payment.refund", "stripe.checkout.session.create"],
    ),
    examples=[
        UsageExample(
            description="Create a $20 payment intent",
            args={
                "amount": 2000,
                "currency": "usd",
                "description": "Order #12345",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

PAYMENT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.payment.retrieve",
    service="stripe",
    category="payments",
    description="Retrieve a payment intent in Stripe",
    description_detailed=(
        "Retrieves the details of a PaymentIntent that was previously created. "
        "Use to check payment status or get details for reconciliation."
    ),
    parameters={
        "payment_intent_id": ParameterSchema(
            type="string",
            required=True,
            description="PaymentIntent ID",
            example="pi_3ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="PaymentIntent ID"),
        "status": ReturnFieldSchema(
            type="string",
            description="Payment status (requires_payment_method, succeeded, etc.)",
        ),
        "amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "amount_received": ReturnFieldSchema(
            type="integer",
            description="Amount actually received",
        ),
        "currency": ReturnFieldSchema(type="string", description="Currency code"),
        "customer": ReturnFieldSchema(type="string", description="Customer ID if set"),
        "charges": ReturnFieldSchema(type="object", description="Associated charges"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="PaymentIntent not found",
            recovery_hint="Verify payment_intent_id is correct",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

PAYMENT_REFUND = CapabilitySchema(
    capability_key="stripe.payment.refund",
    service="stripe",
    category="payments",
    description="Refund a payment in Stripe",
    description_detailed=(
        "Creates a refund for a PaymentIntent or Charge. You can refund the full "
        "amount or a partial amount. Refunds are processed immediately but may take "
        "5-10 business days to appear on customer's statement."
    ),
    parameters={
        "payment_intent": ParameterSchema(
            type="string",
            required=False,
            description="PaymentIntent ID to refund",
            example="pi_3ABC123",
        ),
        "charge": ParameterSchema(
            type="string",
            required=False,
            description="Charge ID to refund (alternative to payment_intent)",
            example="ch_3ABC123",
        ),
        "amount": ParameterSchema(
            type="integer",
            required=False,
            description="Amount to refund in cents (defaults to full amount)",
        ),
        "reason": ParameterSchema(
            type="string",
            required=False,
            description="Reason for refund",
            enum=["duplicate", "fraudulent", "requested_by_customer"],
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your own use",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Refund ID", example="re_3ABC123"),
        "status": ReturnFieldSchema(
            type="string",
            description="Refund status (succeeded, pending, failed)",
        ),
        "amount": ReturnFieldSchema(type="integer", description="Refund amount in cents"),
        "charge": ReturnFieldSchema(type="string", description="Associated charge ID"),
        "payment_intent": ReturnFieldSchema(type="string", description="Associated PI ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Refund amount exceeds charge amount or charge already refunded",
            recovery_hint="Check charge status and remaining refundable amount",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.payment.retrieve", "stripe.charge.retrieve"],
        typically_followed_by=["stripe.refund.retrieve"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ REFUNDS ============

REFUND_RETRIEVE = CapabilitySchema(
    capability_key="stripe.refund.retrieve",
    service="stripe",
    category="payments",
    description="Retrieve a refund in Stripe",
    parameters={
        "refund_id": ParameterSchema(
            type="string",
            required=True,
            description="Refund ID",
            example="re_3ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Refund ID"),
        "status": ReturnFieldSchema(type="string", description="Refund status"),
        "amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "charge": ReturnFieldSchema(type="string", description="Charge ID"),
        "reason": ReturnFieldSchema(type="string", description="Refund reason"),
        "created": ReturnFieldSchema(type="integer", description="Unix timestamp"),
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

REFUND_UPDATE = CapabilitySchema(
    capability_key="stripe.refund.update",
    service="stripe",
    category="payments",
    description="Update a refund in Stripe",
    description_detailed="Updates the metadata on a refund. Other fields cannot be changed.",
    parameters={
        "refund_id": ParameterSchema(
            type="string",
            required=True,
            description="Refund ID to update",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs to update",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Refund ID"),
        "metadata": ReturnFieldSchema(type="object", description="Updated metadata"),
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

REFUND_CANCEL = CapabilitySchema(
    capability_key="stripe.refund.cancel",
    service="stripe",
    category="payments",
    description="Cancel a refund in Stripe",
    description_detailed=(
        "Cancels a refund with a status of requires_action. You cannot cancel "
        "refunds that have already been processed."
    ),
    parameters={
        "refund_id": ParameterSchema(
            type="string",
            required=True,
            description="Refund ID to cancel",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Refund ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'canceled'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Refund cannot be canceled (already processed)",
            recovery_hint="Only refunds with status requires_action can be canceled",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

REFUND_LIST = CapabilitySchema(
    capability_key="stripe.refund.list",
    service="stripe",
    category="payments",
    description="List refunds in Stripe",
    parameters={
        "charge": ParameterSchema(
            type="string",
            required=False,
            description="Filter by charge ID",
        ),
        "payment_intent": ParameterSchema(
            type="string",
            required=False,
            description="Filter by payment intent ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return (1-100)",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of refund objects"),
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

# ============ CHARGES ============

CHARGE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.charge.retrieve",
    service="stripe",
    category="payments",
    description="Retrieve a charge in Stripe",
    description_detailed=(
        "Retrieves the details of a charge. Charges are created when a PaymentIntent "
        "is confirmed and payment is attempted."
    ),
    parameters={
        "charge_id": ParameterSchema(
            type="string",
            required=True,
            description="Charge ID",
            example="ch_3ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Charge ID"),
        "status": ReturnFieldSchema(type="string", description="Charge status"),
        "amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "amount_refunded": ReturnFieldSchema(type="integer", description="Amount refunded"),
        "currency": ReturnFieldSchema(type="string", description="Currency code"),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
        "payment_intent": ReturnFieldSchema(type="string", description="PaymentIntent ID"),
        "refunded": ReturnFieldSchema(type="boolean", description="Fully refunded"),
        "receipt_url": ReturnFieldSchema(type="string", description="Receipt URL"),
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

CHARGE_LIST = CapabilitySchema(
    capability_key="stripe.charge.list",
    service="stripe",
    category="payments",
    description="List charges in Stripe",
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
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return (1-100)",
            default=10,
        ),
        "created": ParameterSchema(
            type="object",
            required=False,
            description="Filter by created date (gte, lte, gt, lt)",
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of charge objects"),
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

PAYMENT_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.payment.create": PAYMENT_CREATE,
    "stripe.payment.retrieve": PAYMENT_RETRIEVE,
    "stripe.payment.refund": PAYMENT_REFUND,
    "stripe.refund.retrieve": REFUND_RETRIEVE,
    "stripe.refund.update": REFUND_UPDATE,
    "stripe.refund.cancel": REFUND_CANCEL,
    "stripe.refund.list": REFUND_LIST,
    "stripe.charge.retrieve": CHARGE_RETRIEVE,
    "stripe.charge.list": CHARGE_LIST,
}
