"""
Stripe Issuing Disputes Capability Schemas.

Rich metadata for Issuing card dispute management.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ DISPUTES ============

ISSUING_DISPUTE_CREATE = CapabilitySchema(
    capability_key="stripe.issuing.dispute.create",
    service="stripe",
    category="issuing",
    description="Create an Issuing dispute",
    description_detailed=(
        "Creates a dispute for an Issuing transaction. Use when a cardholder "
        "disputes a charge on their Issuing card."
    ),
    parameters={
        "transaction": ParameterSchema(
            type="string",
            required=True,
            description="Transaction ID to dispute",
        ),
        "evidence": ParameterSchema(
            type="object",
            required=False,
            description="Evidence supporting the dispute",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Dispute ID"),
        "transaction": ReturnFieldSchema(type="string", description="Transaction ID"),
        "status": ReturnFieldSchema(type="string", description="Dispute status"),
        "amount": ReturnFieldSchema(type="integer", description="Disputed amount"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Transaction not eligible for dispute",
            recovery_hint="Verify transaction exists and can be disputed",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

ISSUING_DISPUTE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.issuing.dispute.retrieve",
    service="stripe",
    category="issuing",
    description="Retrieve an Issuing dispute",
    parameters={
        "dispute_id": ParameterSchema(
            type="string",
            required=True,
            description="Dispute ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Dispute ID"),
        "transaction": ReturnFieldSchema(type="string", description="Transaction ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "evidence": ReturnFieldSchema(type="object", description="Evidence"),
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

ISSUING_DISPUTE_UPDATE = CapabilitySchema(
    capability_key="stripe.issuing.dispute.update",
    service="stripe",
    category="issuing",
    description="Update an Issuing dispute",
    parameters={
        "dispute_id": ParameterSchema(
            type="string",
            required=True,
            description="Dispute ID to update",
        ),
        "evidence": ParameterSchema(
            type="object",
            required=False,
            description="Updated evidence",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Dispute ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
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

ISSUING_DISPUTE_SUBMIT = CapabilitySchema(
    capability_key="stripe.issuing.dispute.submit",
    service="stripe",
    category="issuing",
    description="Submit an Issuing dispute for review",
    parameters={
        "dispute_id": ParameterSchema(
            type="string",
            required=True,
            description="Dispute ID to submit",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Metadata to attach",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Dispute ID"),
        "status": ReturnFieldSchema(type="string", description="Should be submitted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Missing required evidence",
            recovery_hint="Add evidence before submitting",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

ISSUING_DISPUTE_LIST = CapabilitySchema(
    capability_key="stripe.issuing.dispute.list",
    service="stripe",
    category="issuing",
    description="List Issuing disputes",
    parameters={
        "transaction": ParameterSchema(
            type="string",
            required=False,
            description="Filter by transaction ID",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["unsubmitted", "under_review", "won", "lost"],
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

ISSUING_DISPUTE_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.issuing.dispute.create": ISSUING_DISPUTE_CREATE,
    "stripe.issuing.dispute.retrieve": ISSUING_DISPUTE_RETRIEVE,
    "stripe.issuing.dispute.update": ISSUING_DISPUTE_UPDATE,
    "stripe.issuing.dispute.submit": ISSUING_DISPUTE_SUBMIT,
    "stripe.issuing.dispute.list": ISSUING_DISPUTE_LIST,
}
