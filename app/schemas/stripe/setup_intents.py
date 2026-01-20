"""
Stripe Setup Intent & Payment Link Capability Schemas.

Rich metadata for card setup and no-code payment collection.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ SETUP INTENTS ============

SETUP_INTENT_CREATE = CapabilitySchema(
    capability_key="stripe.setup_intent.create",
    service="stripe",
    category="setup_intents",
    description="Create a Setup Intent",
    description_detailed=(
        "Creates a SetupIntent for collecting payment method details without charging. "
        "Use to save cards for future payments like subscriptions or metered billing."
    ),
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Customer to attach payment method to",
        ),
        "payment_method_types": ParameterSchema(
            type="array",
            required=False,
            description="Allowed payment method types",
            items_type="string",
            example=["card"],
        ),
        "usage": ParameterSchema(
            type="string",
            required=False,
            description="How payment method will be used",
            enum=["off_session", "on_session"],
            default="off_session",
        ),
        "confirm": ParameterSchema(
            type="boolean",
            required=False,
            description="Immediately confirm the intent",
            default=False,
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method to attach and confirm",
        ),
        "return_url": ParameterSchema(
            type="string",
            required=False,
            description="URL for redirect after setup",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your use",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="SetupIntent ID",
            example="seti_ABC123",
        ),
        "client_secret": ReturnFieldSchema(type="string", description="Client secret"),
        "status": ReturnFieldSchema(type="string", description="Setup status"),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
        "payment_method": ReturnFieldSchema(type="string", description="Payment method"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.subscription.create", "stripe.setup_intent.confirm"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SETUP_INTENT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.setup_intent.retrieve",
    service="stripe",
    category="setup_intents",
    description="Retrieve a Setup Intent",
    parameters={
        "setup_intent_id": ParameterSchema(
            type="string",
            required=True,
            description="SetupIntent ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="SetupIntent ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "customer": ReturnFieldSchema(type="string", description="Customer"),
        "payment_method": ReturnFieldSchema(type="string", description="Payment method"),
        "client_secret": ReturnFieldSchema(type="string", description="Client secret"),
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

SETUP_INTENT_UPDATE = CapabilitySchema(
    capability_key="stripe.setup_intent.update",
    service="stripe",
    category="setup_intents",
    description="Update a Setup Intent",
    parameters={
        "setup_intent_id": ParameterSchema(
            type="string",
            required=True,
            description="SetupIntent ID to update",
        ),
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="New customer ID",
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="New payment method",
        ),
        "payment_method_types": ParameterSchema(
            type="array",
            required=False,
            description="Update allowed types",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="SetupIntent ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Cannot update confirmed SetupIntent",
            recovery_hint="Create a new SetupIntent",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

SETUP_INTENT_CONFIRM = CapabilitySchema(
    capability_key="stripe.setup_intent.confirm",
    service="stripe",
    category="setup_intents",
    description="Confirm a Setup Intent",
    description_detailed=(
        "Confirms a SetupIntent to complete the payment method setup process. "
        "May require customer authentication for 3D Secure."
    ),
    parameters={
        "setup_intent_id": ParameterSchema(
            type="string",
            required=True,
            description="SetupIntent ID to confirm",
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Payment method to attach",
        ),
        "return_url": ParameterSchema(
            type="string",
            required=False,
            description="URL for redirect after auth",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="SetupIntent ID"),
        "status": ReturnFieldSchema(type="string", description="Should be succeeded"),
        "payment_method": ReturnFieldSchema(type="string", description="Saved method"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Setup failed or requires action",
            recovery_hint="Check next_action for required steps",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

SETUP_INTENT_CANCEL = CapabilitySchema(
    capability_key="stripe.setup_intent.cancel",
    service="stripe",
    category="setup_intents",
    description="Cancel a Setup Intent",
    parameters={
        "setup_intent_id": ParameterSchema(
            type="string",
            required=True,
            description="SetupIntent ID to cancel",
        ),
        "cancellation_reason": ParameterSchema(
            type="string",
            required=False,
            description="Reason for cancellation",
            enum=["abandoned", "requested_by_customer", "duplicate"],
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="SetupIntent ID"),
        "status": ReturnFieldSchema(type="string", description="Should be canceled"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Cannot cancel succeeded SetupIntent",
            recovery_hint="Only pending intents can be canceled",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

SETUP_INTENT_LIST = CapabilitySchema(
    capability_key="stripe.setup_intent.list",
    service="stripe",
    category="setup_intents",
    description="List Setup Intents",
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer ID",
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Filter by payment method",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of SetupIntents"),
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

SETUP_INTENT_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.setup_intent.create": SETUP_INTENT_CREATE,
    "stripe.setup_intent.retrieve": SETUP_INTENT_RETRIEVE,
    "stripe.setup_intent.update": SETUP_INTENT_UPDATE,
    "stripe.setup_intent.confirm": SETUP_INTENT_CONFIRM,
    "stripe.setup_intent.cancel": SETUP_INTENT_CANCEL,
    "stripe.setup_intent.list": SETUP_INTENT_LIST,
}
