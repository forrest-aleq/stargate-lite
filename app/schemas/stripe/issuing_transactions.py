"""
Stripe Issuing Transactions & Authorizations Capability Schemas.

Rich metadata for transaction monitoring and authorization handling.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ AUTHORIZATIONS ============

AUTHORIZATION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.issuing.authorization.retrieve",
    service="stripe",
    category="issuing",
    description="Retrieve an Issuing authorization",
    description_detailed=(
        "Retrieves an authorization representing a request to authorize "
        "a purchase on an Issuing card."
    ),
    parameters={
        "authorization_id": ParameterSchema(
            type="string",
            required=True,
            description="Authorization ID",
            example="iauth_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Authorization ID"),
        "card": ReturnFieldSchema(type="string", description="Card ID"),
        "cardholder": ReturnFieldSchema(type="string", description="Cardholder ID"),
        "amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "status": ReturnFieldSchema(type="string", description="Authorization status"),
        "approved": ReturnFieldSchema(type="boolean", description="Was approved"),
        "merchant_data": ReturnFieldSchema(type="object", description="Merchant info"),
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

AUTHORIZATION_UPDATE = CapabilitySchema(
    capability_key="stripe.issuing.authorization.update",
    service="stripe",
    category="issuing",
    description="Update an Issuing authorization",
    parameters={
        "authorization_id": ParameterSchema(
            type="string",
            required=True,
            description="Authorization ID to update",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Authorization ID"),
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

AUTHORIZATION_APPROVE = CapabilitySchema(
    capability_key="stripe.issuing.authorization.approve",
    service="stripe",
    category="issuing",
    description="Approve an Issuing authorization",
    description_detailed=(
        "Approves a pending authorization. Only works for real-time authorizations "
        "when you have real-time authorization controls enabled."
    ),
    parameters={
        "authorization_id": ParameterSchema(
            type="string",
            required=True,
            description="Authorization ID to approve",
        ),
        "amount": ParameterSchema(
            type="integer",
            required=False,
            description="Approved amount (partial approval)",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Metadata to attach",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Authorization ID"),
        "approved": ReturnFieldSchema(type="boolean", description="Should be true"),
        "status": ReturnFieldSchema(type="string", description="Updated status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Authorization already processed or expired",
            recovery_hint="Only pending authorizations can be approved",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

AUTHORIZATION_DECLINE = CapabilitySchema(
    capability_key="stripe.issuing.authorization.decline",
    service="stripe",
    category="issuing",
    description="Decline an Issuing authorization",
    parameters={
        "authorization_id": ParameterSchema(
            type="string",
            required=True,
            description="Authorization ID to decline",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Metadata to attach",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Authorization ID"),
        "approved": ReturnFieldSchema(type="boolean", description="Should be false"),
        "status": ReturnFieldSchema(type="string", description="Updated status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Authorization already processed or expired",
            recovery_hint="Only pending authorizations can be declined",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

AUTHORIZATION_LIST = CapabilitySchema(
    capability_key="stripe.issuing.authorization.list",
    service="stripe",
    category="issuing",
    description="List Issuing authorizations",
    parameters={
        "card": ParameterSchema(
            type="string",
            required=False,
            description="Filter by card ID",
        ),
        "cardholder": ParameterSchema(
            type="string",
            required=False,
            description="Filter by cardholder ID",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["pending", "closed", "reversed"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of authorizations"),
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

# ============ TRANSACTIONS ============

TRANSACTION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.issuing.transaction.retrieve",
    service="stripe",
    category="issuing",
    description="Retrieve an Issuing transaction",
    description_detailed=(
        "Retrieves a transaction representing a completed purchase on an Issuing card."
    ),
    parameters={
        "transaction_id": ParameterSchema(
            type="string",
            required=True,
            description="Transaction ID",
            example="ipi_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transaction ID"),
        "card": ReturnFieldSchema(type="string", description="Card ID"),
        "cardholder": ReturnFieldSchema(type="string", description="Cardholder ID"),
        "amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "type": ReturnFieldSchema(type="string", description="Transaction type"),
        "merchant_data": ReturnFieldSchema(type="object", description="Merchant info"),
        "authorization": ReturnFieldSchema(type="string", description="Auth ID"),
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

TRANSACTION_UPDATE = CapabilitySchema(
    capability_key="stripe.issuing.transaction.update",
    service="stripe",
    category="issuing",
    description="Update an Issuing transaction",
    parameters={
        "transaction_id": ParameterSchema(
            type="string",
            required=True,
            description="Transaction ID to update",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transaction ID"),
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

TRANSACTION_LIST = CapabilitySchema(
    capability_key="stripe.issuing.transaction.list",
    service="stripe",
    category="issuing",
    description="List Issuing transactions",
    parameters={
        "card": ParameterSchema(
            type="string",
            required=False,
            description="Filter by card ID",
        ),
        "cardholder": ParameterSchema(
            type="string",
            required=False,
            description="Filter by cardholder ID",
        ),
        "type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by type",
            enum=["capture", "refund"],
        ),
        "created": ParameterSchema(
            type="object",
            required=False,
            description="Filter by created date",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of transactions"),
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

ISSUING_TRANSACTION_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.issuing.authorization.retrieve": AUTHORIZATION_RETRIEVE,
    "stripe.issuing.authorization.update": AUTHORIZATION_UPDATE,
    "stripe.issuing.authorization.approve": AUTHORIZATION_APPROVE,
    "stripe.issuing.authorization.decline": AUTHORIZATION_DECLINE,
    "stripe.issuing.authorization.list": AUTHORIZATION_LIST,
    "stripe.issuing.transaction.retrieve": TRANSACTION_RETRIEVE,
    "stripe.issuing.transaction.update": TRANSACTION_UPDATE,
    "stripe.issuing.transaction.list": TRANSACTION_LIST,
}
