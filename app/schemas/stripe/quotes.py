"""
Stripe Quotes Capability Schemas.

Rich metadata for pricing proposals and quote management.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ QUOTES ============

QUOTE_CREATE = CapabilitySchema(
    capability_key="stripe.quote.create",
    service="stripe",
    category="quotes",
    description="Create a quote in Stripe",
    description_detailed=(
        "Creates a quote for a customer. Quotes allow you to send pricing "
        "proposals that customers can accept to start a subscription or payment."
    ),
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=False,
            description="Items to quote",
            items_type="object",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Quote description",
        ),
        "header": ParameterSchema(
            type="string",
            required=False,
            description="Header text",
        ),
        "footer": ParameterSchema(
            type="string",
            required=False,
            description="Footer text",
        ),
        "expires_at": ParameterSchema(
            type="integer",
            required=False,
            description="Expiration timestamp",
        ),
        "collection_method": ParameterSchema(
            type="string",
            required=False,
            description="How to collect payment",
            enum=["charge_automatically", "send_invoice"],
        ),
        "automatic_tax": ParameterSchema(
            type="object",
            required=False,
            description="Automatic tax settings",
        ),
        "discounts": ParameterSchema(
            type="array",
            required=False,
            description="Discounts to apply",
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
            description="Quote ID",
            example="qt_ABC123",
        ),
        "status": ReturnFieldSchema(type="string", description="Quote status"),
        "amount_total": ReturnFieldSchema(type="integer", description="Total amount"),
        "customer": ReturnFieldSchema(type="string", description="Customer ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.quote.finalize"],
    ),
    idempotent=False,
    has_side_effects=True,
)

QUOTE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.quote.retrieve",
    service="stripe",
    category="quotes",
    description="Retrieve a quote",
    parameters={
        "quote_id": ParameterSchema(
            type="string",
            required=True,
            description="Quote ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Quote ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "customer": ReturnFieldSchema(type="string", description="Customer"),
        "amount_total": ReturnFieldSchema(type="integer", description="Total"),
        "line_items": ReturnFieldSchema(type="object", description="Items"),
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

QUOTE_UPDATE = CapabilitySchema(
    capability_key="stripe.quote.update",
    service="stripe",
    category="quotes",
    description="Update a quote",
    parameters={
        "quote_id": ParameterSchema(
            type="string",
            required=True,
            description="Quote ID to update",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=False,
            description="Update line items",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Update description",
        ),
        "expires_at": ParameterSchema(
            type="integer",
            required=False,
            description="Update expiration",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Quote ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Cannot update finalized quote",
            recovery_hint="Only draft quotes can be updated",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

QUOTE_FINALIZE = CapabilitySchema(
    capability_key="stripe.quote.finalize",
    service="stripe",
    category="quotes",
    description="Finalize a quote",
    description_detailed=(
        "Finalizes a quote, preventing further edits and generating a PDF. "
        "Finalized quotes can be sent to customers for acceptance."
    ),
    parameters={
        "quote_id": ParameterSchema(
            type="string",
            required=True,
            description="Quote ID to finalize",
        ),
        "expires_at": ParameterSchema(
            type="integer",
            required=False,
            description="Set expiration when finalizing",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Quote ID"),
        "status": ReturnFieldSchema(type="string", description="Should be open"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Quote already finalized or has errors",
            recovery_hint="Check quote has valid line items",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

QUOTE_ACCEPT = CapabilitySchema(
    capability_key="stripe.quote.accept",
    service="stripe",
    category="quotes",
    description="Accept a quote",
    description_detailed=(
        "Accepts a quote on behalf of the customer, creating a subscription "
        "or invoice based on the quote configuration."
    ),
    parameters={
        "quote_id": ParameterSchema(
            type="string",
            required=True,
            description="Quote ID to accept",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Quote ID"),
        "status": ReturnFieldSchema(type="string", description="Should be accepted"),
        "invoice": ReturnFieldSchema(type="string", description="Created invoice"),
        "subscription": ReturnFieldSchema(type="string", description="Created sub"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Quote not open or expired",
            recovery_hint="Finalize quote first and check expiration",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

QUOTE_CANCEL = CapabilitySchema(
    capability_key="stripe.quote.cancel",
    service="stripe",
    category="quotes",
    description="Cancel a quote",
    parameters={
        "quote_id": ParameterSchema(
            type="string",
            required=True,
            description="Quote ID to cancel",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Quote ID"),
        "status": ReturnFieldSchema(type="string", description="Should be canceled"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Quote already accepted",
            recovery_hint="Accepted quotes cannot be canceled",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

QUOTE_LIST = CapabilitySchema(
    capability_key="stripe.quote.list",
    service="stripe",
    category="quotes",
    description="List quotes",
    parameters={
        "customer": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["draft", "open", "accepted", "canceled"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of quotes"),
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

QUOTE_PDF = CapabilitySchema(
    capability_key="stripe.quote.pdf",
    service="stripe",
    category="quotes",
    description="Download quote PDF",
    parameters={
        "quote_id": ParameterSchema(
            type="string",
            required=True,
            description="Quote ID",
        ),
    },
    returns={
        "pdf_content": ReturnFieldSchema(type="string", description="PDF binary data"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Quote not finalized",
            recovery_hint="Finalize quote to generate PDF",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

QUOTE_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.quote.create": QUOTE_CREATE,
    "stripe.quote.retrieve": QUOTE_RETRIEVE,
    "stripe.quote.update": QUOTE_UPDATE,
    "stripe.quote.finalize": QUOTE_FINALIZE,
    "stripe.quote.accept": QUOTE_ACCEPT,
    "stripe.quote.cancel": QUOTE_CANCEL,
    "stripe.quote.list": QUOTE_LIST,
    "stripe.quote.pdf": QUOTE_PDF,
}
