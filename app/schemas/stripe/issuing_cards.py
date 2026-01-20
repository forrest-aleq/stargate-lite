"""
Stripe Issuing Cards Capability Schemas.

Rich metadata for card issuance and management.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

CARD_CREATE = CapabilitySchema(
    capability_key="stripe.issuing.card.create",
    service="stripe",
    category="issuing",
    description="Create an Issuing card",
    description_detailed=(
        "Creates a new Issuing card for a cardholder. Cards can be physical "
        "or virtual. Physical cards are shipped to the cardholder's address."
    ),
    parameters={
        "cardholder": ParameterSchema(
            type="string",
            required=True,
            description="Cardholder ID",
            example="ich_ABC123",
        ),
        "currency": ParameterSchema(
            type="string",
            required=True,
            description="Three-letter ISO currency code",
            example="usd",
        ),
        "type": ParameterSchema(
            type="string",
            required=True,
            description="Card type",
            enum=["physical", "virtual"],
            example="virtual",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Initial card status",
            enum=["active", "inactive"],
            default="active",
        ),
        "spending_controls": ParameterSchema(
            type="object",
            required=False,
            description="Spending limits and restrictions",
            example={
                "spending_limits": [{"amount": 50000, "interval": "monthly"}],
            },
        ),
        "shipping": ParameterSchema(
            type="object",
            required=False,
            description="Shipping details for physical cards",
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
            description="Card ID",
            example="ic_ABC123",
        ),
        "cardholder": ReturnFieldSchema(type="string", description="Cardholder ID"),
        "type": ReturnFieldSchema(type="string", description="Card type"),
        "status": ReturnFieldSchema(type="string", description="Card status"),
        "last4": ReturnFieldSchema(type="string", description="Last 4 digits"),
        "exp_month": ReturnFieldSchema(type="integer", description="Expiry month"),
        "exp_year": ReturnFieldSchema(type="integer", description="Expiry year"),
        "brand": ReturnFieldSchema(type="string", description="Card brand"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid cardholder or missing required fields",
            recovery_hint="Verify cardholder exists and has required info",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.issuing.cardholder.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

CARD_RETRIEVE = CapabilitySchema(
    capability_key="stripe.issuing.card.retrieve",
    service="stripe",
    category="issuing",
    description="Retrieve an Issuing card",
    parameters={
        "card_id": ParameterSchema(
            type="string",
            required=True,
            description="Card ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Card ID"),
        "cardholder": ReturnFieldSchema(type="string", description="Cardholder ID"),
        "type": ReturnFieldSchema(type="string", description="Card type"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "last4": ReturnFieldSchema(type="string", description="Last 4 digits"),
        "spending_controls": ReturnFieldSchema(type="object", description="Limits"),
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

CARD_UPDATE = CapabilitySchema(
    capability_key="stripe.issuing.card.update",
    service="stripe",
    category="issuing",
    description="Update an Issuing card",
    parameters={
        "card_id": ParameterSchema(
            type="string",
            required=True,
            description="Card ID to update",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="New status",
            enum=["active", "inactive", "canceled"],
        ),
        "spending_controls": ParameterSchema(
            type="object",
            required=False,
            description="Updated spending limits",
        ),
        "cancellation_reason": ParameterSchema(
            type="string",
            required=False,
            description="Reason if canceling",
            enum=["lost", "stolen", "design_rejected"],
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Card ID"),
        "status": ReturnFieldSchema(type="string", description="Updated status"),
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

CARD_LIST = CapabilitySchema(
    capability_key="stripe.issuing.card.list",
    service="stripe",
    category="issuing",
    description="List Issuing cards",
    parameters={
        "cardholder": ParameterSchema(
            type="string",
            required=False,
            description="Filter by cardholder ID",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["active", "inactive", "canceled"],
        ),
        "type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by type",
            enum=["physical", "virtual"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of cards"),
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

# ============ CARDHOLDERS ============

CARDHOLDER_CREATE = CapabilitySchema(
    capability_key="stripe.issuing.cardholder.create",
    service="stripe",
    category="issuing",
    description="Create an Issuing cardholder",
    description_detailed=(
        "Creates a new Issuing cardholder. Cardholders represent individuals "
        "or businesses that can be issued cards."
    ),
    parameters={
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Full name",
            example="Jenny Rosen",
        ),
        "email": ParameterSchema(
            type="string",
            required=True,
            description="Email address",
        ),
        "phone_number": ParameterSchema(
            type="string",
            required=False,
            description="Phone number",
        ),
        "type": ParameterSchema(
            type="string",
            required=True,
            description="Cardholder type",
            enum=["individual", "company"],
        ),
        "billing": ParameterSchema(
            type="object",
            required=True,
            description="Billing address",
            example={
                "address": {
                    "line1": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "postal_code": "94102",
                    "country": "US",
                },
            },
        ),
        "individual": ParameterSchema(
            type="object",
            required=False,
            description="Individual details (if type is individual)",
        ),
        "company": ParameterSchema(
            type="object",
            required=False,
            description="Company details (if type is company)",
        ),
        "spending_controls": ParameterSchema(
            type="object",
            required=False,
            description="Default spending limits for cards",
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
            description="Cardholder ID",
            example="ich_ABC123",
        ),
        "name": ReturnFieldSchema(type="string", description="Name"),
        "email": ReturnFieldSchema(type="string", description="Email"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "type": ReturnFieldSchema(type="string", description="Type"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid or incomplete cardholder info",
            recovery_hint="Ensure all required fields are provided",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.issuing.card.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

CARDHOLDER_RETRIEVE = CapabilitySchema(
    capability_key="stripe.issuing.cardholder.retrieve",
    service="stripe",
    category="issuing",
    description="Retrieve an Issuing cardholder",
    parameters={
        "cardholder_id": ParameterSchema(
            type="string",
            required=True,
            description="Cardholder ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Cardholder ID"),
        "name": ReturnFieldSchema(type="string", description="Name"),
        "email": ReturnFieldSchema(type="string", description="Email"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "type": ReturnFieldSchema(type="string", description="Type"),
        "billing": ReturnFieldSchema(type="object", description="Billing address"),
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

CARDHOLDER_UPDATE = CapabilitySchema(
    capability_key="stripe.issuing.cardholder.update",
    service="stripe",
    category="issuing",
    description="Update an Issuing cardholder",
    parameters={
        "cardholder_id": ParameterSchema(
            type="string",
            required=True,
            description="Cardholder ID to update",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="New email",
        ),
        "phone_number": ParameterSchema(
            type="string",
            required=False,
            description="New phone",
        ),
        "billing": ParameterSchema(
            type="object",
            required=False,
            description="Updated billing address",
        ),
        "spending_controls": ParameterSchema(
            type="object",
            required=False,
            description="Updated spending limits",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="New status",
            enum=["active", "inactive"],
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Cardholder ID"),
        "status": ReturnFieldSchema(type="string", description="Updated status"),
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

CARDHOLDER_LIST = CapabilitySchema(
    capability_key="stripe.issuing.cardholder.list",
    service="stripe",
    category="issuing",
    description="List Issuing cardholders",
    parameters={
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Filter by email",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["active", "inactive", "blocked"],
        ),
        "type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by type",
            enum=["individual", "company"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of cardholders"),
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

ISSUING_CARD_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.issuing.card.create": CARD_CREATE,
    "stripe.issuing.card.retrieve": CARD_RETRIEVE,
    "stripe.issuing.card.update": CARD_UPDATE,
    "stripe.issuing.card.list": CARD_LIST,
    "stripe.issuing.cardholder.create": CARDHOLDER_CREATE,
    "stripe.issuing.cardholder.retrieve": CARDHOLDER_RETRIEVE,
    "stripe.issuing.cardholder.update": CARDHOLDER_UPDATE,
    "stripe.issuing.cardholder.list": CARDHOLDER_LIST,
}
