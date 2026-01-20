"""
Stripe Credit Notes Capability Schemas.

Rich metadata for invoice credits and adjustments.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ CREDIT NOTES ============

CREDIT_NOTE_CREATE = CapabilitySchema(
    capability_key="stripe.credit_note.create",
    service="stripe",
    category="credit_notes",
    description="Create a credit note",
    description_detailed=(
        "Creates a credit note for an invoice. Credit notes reduce the amount "
        "owed and can refund customers or create account credit."
    ),
    parameters={
        "invoice": ParameterSchema(
            type="string",
            required=True,
            description="Invoice ID to credit",
        ),
        "lines": ParameterSchema(
            type="array",
            required=False,
            description="Line items to credit",
        ),
        "amount": ParameterSchema(
            type="integer",
            required=False,
            description="Total credit amount",
        ),
        "credit_amount": ParameterSchema(
            type="integer",
            required=False,
            description="Amount to add as customer credit",
        ),
        "refund_amount": ParameterSchema(
            type="integer",
            required=False,
            description="Amount to refund",
        ),
        "out_of_band_amount": ParameterSchema(
            type="integer",
            required=False,
            description="Amount refunded outside Stripe",
        ),
        "reason": ParameterSchema(
            type="string",
            required=False,
            description="Reason for credit",
            enum=["duplicate", "fraudulent", "order_change", "product_unsatisfactory"],
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Internal memo",
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
            description="Credit note ID",
            example="cn_ABC123",
        ),
        "invoice": ReturnFieldSchema(type="string", description="Invoice ID"),
        "amount": ReturnFieldSchema(type="integer", description="Total credit"),
        "status": ReturnFieldSchema(type="string", description="Status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invoice not paid or already fully credited",
            recovery_hint="Check invoice status and existing credits",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CREDIT_NOTE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.credit_note.retrieve",
    service="stripe",
    category="credit_notes",
    description="Retrieve a credit note",
    parameters={
        "credit_note_id": ParameterSchema(
            type="string",
            required=True,
            description="Credit note ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Credit note ID"),
        "invoice": ReturnFieldSchema(type="string", description="Invoice"),
        "amount": ReturnFieldSchema(type="integer", description="Amount"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "lines": ReturnFieldSchema(type="object", description="Line items"),
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

CREDIT_NOTE_UPDATE = CapabilitySchema(
    capability_key="stripe.credit_note.update",
    service="stripe",
    category="credit_notes",
    description="Update a credit note",
    parameters={
        "credit_note_id": ParameterSchema(
            type="string",
            required=True,
            description="Credit note ID to update",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Update memo",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Credit note ID"),
        "memo": ReturnFieldSchema(type="string", description="Updated memo"),
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

CREDIT_NOTE_VOID = CapabilitySchema(
    capability_key="stripe.credit_note.void",
    service="stripe",
    category="credit_notes",
    description="Void a credit note",
    parameters={
        "credit_note_id": ParameterSchema(
            type="string",
            required=True,
            description="Credit note ID to void",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Credit note ID"),
        "status": ReturnFieldSchema(type="string", description="Should be void"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Credit note already voided",
            recovery_hint="Check credit note status",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CREDIT_NOTE_LIST = CapabilitySchema(
    capability_key="stripe.credit_note.list",
    service="stripe",
    category="credit_notes",
    description="List credit notes",
    parameters={
        "invoice": ParameterSchema(
            type="string",
            required=False,
            description="Filter by invoice",
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
        "data": ReturnFieldSchema(type="array", description="List of credit notes"),
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

CREDIT_NOTE_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.credit_note.create": CREDIT_NOTE_CREATE,
    "stripe.credit_note.retrieve": CREDIT_NOTE_RETRIEVE,
    "stripe.credit_note.update": CREDIT_NOTE_UPDATE,
    "stripe.credit_note.void": CREDIT_NOTE_VOID,
    "stripe.credit_note.list": CREDIT_NOTE_LIST,
}
