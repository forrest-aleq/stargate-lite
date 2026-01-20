"""
Stripe Billing Capability Schemas.

Rich metadata for payment methods and disputes.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ PAYMENT METHODS ============

PAYMENT_METHOD_CREATE = CapabilitySchema(
    capability_key="stripe.paymentmethod.create",
    service="stripe",
    category="billing",
    description="Create a payment method in Stripe",
    description_detailed=(
        "Creates a PaymentMethod object. PaymentMethods represent your customer's "
        "payment instruments. They can be attached to customers for future payments."
    ),
    parameters={
        "type": ParameterSchema(
            type="string",
            required=True,
            description="Type of payment method",
            enum=["card", "us_bank_account", "sepa_debit", "ideal", "bancontact"],
            example="card",
        ),
        "card": ParameterSchema(
            type="object",
            required=False,
            description="Card details (number, exp_month, exp_year, cvc)",
        ),
        "billing_details": ParameterSchema(
            type="object",
            required=False,
            description="Billing details (name, email, phone, address)",
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
            description="PaymentMethod ID",
            example="pm_ABC123",
        ),
        "type": ReturnFieldSchema(type="string", description="Payment method type"),
        "card": ReturnFieldSchema(type="object", description="Card details (last4, brand, etc.)"),
        "billing_details": ReturnFieldSchema(type="object", description="Billing info"),
        "created": ReturnFieldSchema(type="integer", description="Unix timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid card details",
            recovery_hint="Verify card number, expiration, and CVC",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.paymentmethod.attach", "stripe.payment.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

PAYMENT_METHOD_RETRIEVE = CapabilitySchema(
    capability_key="stripe.paymentmethod.retrieve",
    service="stripe",
    category="billing",
    description="Retrieve a payment method in Stripe",
    parameters={
        "payment_method_id": ParameterSchema(
            type="string",
            required=True,
            description="PaymentMethod ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="PaymentMethod ID"),
        "type": ReturnFieldSchema(type="string", description="Type"),
        "card": ReturnFieldSchema(type="object", description="Card details"),
        "customer": ReturnFieldSchema(type="string", description="Attached customer"),
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

PAYMENT_METHOD_UPDATE = CapabilitySchema(
    capability_key="stripe.paymentmethod.update",
    service="stripe",
    category="billing",
    description="Update a payment method in Stripe",
    parameters={
        "payment_method_id": ParameterSchema(
            type="string",
            required=True,
            description="PaymentMethod ID to update",
        ),
        "billing_details": ParameterSchema(
            type="object",
            required=False,
            description="Updated billing details",
        ),
        "card": ParameterSchema(
            type="object",
            required=False,
            description="Update card details (exp_month, exp_year only)",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="PaymentMethod ID"),
        "billing_details": ReturnFieldSchema(type="object", description="Updated billing"),
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

PAYMENT_METHOD_LIST = CapabilitySchema(
    capability_key="stripe.paymentmethod.list",
    service="stripe",
    category="billing",
    description="List payment methods for a customer",
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "type": ParameterSchema(
            type="string",
            required=True,
            description="Filter by payment method type",
            enum=["card", "us_bank_account", "sepa_debit"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of payment methods"),
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

PAYMENT_METHOD_ATTACH = CapabilitySchema(
    capability_key="stripe.paymentmethod.attach",
    service="stripe",
    category="billing",
    description="Attach a payment method to a customer",
    description_detailed=(
        "Attaches a PaymentMethod to a Customer. This allows the payment method "
        "to be reused for future payments."
    ),
    parameters={
        "payment_method_id": ParameterSchema(
            type="string",
            required=True,
            description="PaymentMethod ID to attach",
        ),
        "customer": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID to attach to",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="PaymentMethod ID"),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Payment method already attached or invalid customer",
            recovery_hint="Detach from current customer first or verify customer ID",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.paymentmethod.create", "stripe.customer.create"],
        typically_followed_by=["stripe.subscription.create", "stripe.payment.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

PAYMENT_METHOD_DETACH = CapabilitySchema(
    capability_key="stripe.paymentmethod.detach",
    service="stripe",
    category="billing",
    description="Detach a payment method from a customer",
    parameters={
        "payment_method_id": ParameterSchema(
            type="string",
            required=True,
            description="PaymentMethod ID to detach",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="PaymentMethod ID"),
        "customer": ReturnFieldSchema(type="string", description="Should be null"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Payment method not attached to any customer",
            recovery_hint="Verify payment method is attached",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

# ============ DISPUTES ============

DISPUTE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.dispute.retrieve",
    service="stripe",
    category="billing",
    description="Retrieve a dispute in Stripe",
    description_detailed=(
        "Retrieves a dispute (chargeback) initiated by a customer's bank. "
        "Disputes require evidence submission to challenge."
    ),
    parameters={
        "dispute_id": ParameterSchema(
            type="string",
            required=True,
            description="Dispute ID",
            example="dp_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Dispute ID"),
        "status": ReturnFieldSchema(
            type="string",
            description="Dispute status (warning_needs_response, needs_response, etc.)",
        ),
        "amount": ReturnFieldSchema(type="integer", description="Disputed amount"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "charge": ReturnFieldSchema(type="string", description="Related charge ID"),
        "reason": ReturnFieldSchema(type="string", description="Dispute reason"),
        "evidence_due_by": ReturnFieldSchema(type="integer", description="Evidence deadline"),
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

DISPUTE_UPDATE = CapabilitySchema(
    capability_key="stripe.dispute.update",
    service="stripe",
    category="billing",
    description="Update a dispute with evidence in Stripe",
    description_detailed=(
        "Updates a dispute with evidence to challenge it. You can submit "
        "various types of evidence to support your case."
    ),
    parameters={
        "dispute_id": ParameterSchema(
            type="string",
            required=True,
            description="Dispute ID to update",
        ),
        "evidence": ParameterSchema(
            type="object",
            required=False,
            description="Evidence to submit",
            example={
                "customer_email_address": "customer@example.com",
                "customer_signature": "file_ABC123",
                "product_description": "Digital software license",
            },
        ),
        "submit": ParameterSchema(
            type="boolean",
            required=False,
            description="Submit evidence for review (cannot be undone)",
            default=False,
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Dispute ID"),
        "status": ReturnFieldSchema(type="string", description="Updated status"),
        "evidence": ReturnFieldSchema(type="object", description="Submitted evidence"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Dispute already closed or evidence deadline passed",
            recovery_hint="Check dispute status and deadline",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

DISPUTE_CLOSE = CapabilitySchema(
    capability_key="stripe.dispute.close",
    service="stripe",
    category="billing",
    description="Close a dispute in Stripe",
    description_detailed=(
        "Closes a dispute, accepting the customer's claim. This action cannot "
        "be undone and the disputed amount will be returned to the customer."
    ),
    parameters={
        "dispute_id": ParameterSchema(
            type="string",
            required=True,
            description="Dispute ID to close",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Dispute ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'lost'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Dispute already closed",
            recovery_hint="Check dispute status first",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

DISPUTE_LIST = CapabilitySchema(
    capability_key="stripe.dispute.list",
    service="stripe",
    category="billing",
    description="List disputes in Stripe",
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
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of disputes"),
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

BILLING_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.paymentmethod.create": PAYMENT_METHOD_CREATE,
    "stripe.paymentmethod.retrieve": PAYMENT_METHOD_RETRIEVE,
    "stripe.paymentmethod.update": PAYMENT_METHOD_UPDATE,
    "stripe.paymentmethod.list": PAYMENT_METHOD_LIST,
    "stripe.paymentmethod.attach": PAYMENT_METHOD_ATTACH,
    "stripe.paymentmethod.detach": PAYMENT_METHOD_DETACH,
    "stripe.dispute.retrieve": DISPUTE_RETRIEVE,
    "stripe.dispute.update": DISPUTE_UPDATE,
    "stripe.dispute.close": DISPUTE_CLOSE,
    "stripe.dispute.list": DISPUTE_LIST,
}
