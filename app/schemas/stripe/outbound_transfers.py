"""
Stripe Treasury Outbound Transfers & Transactions Capability Schemas.

Rich metadata for Treasury fund movements and transaction history.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ OUTBOUND TRANSFERS ============

OUTBOUND_TRANSFER_CREATE = CapabilitySchema(
    capability_key="stripe.treasury.outbound_transfer.create",
    service="stripe",
    category="treasury",
    description="Create a Treasury outbound transfer",
    description_detailed=(
        "Creates an outbound transfer from a FinancialAccount to a connected "
        "Stripe account's external bank account."
    ),
    parameters={
        "financial_account": ParameterSchema(
            type="string",
            required=True,
            description="Source financial account ID",
        ),
        "destination_payment_method": ParameterSchema(
            type="string",
            required=True,
            description="Destination payment method ID",
        ),
        "amount": ParameterSchema(
            type="integer",
            required=True,
            description="Amount in cents",
        ),
        "currency": ParameterSchema(
            type="string",
            required=True,
            description="Currency code",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Transfer description",
        ),
        "statement_descriptor": ParameterSchema(
            type="string",
            required=False,
            description="Statement descriptor",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transfer ID"),
        "amount": ReturnFieldSchema(type="integer", description="Amount"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "financial_account": ReturnFieldSchema(type="string", description="Source"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Insufficient funds or invalid destination",
            recovery_hint="Check balance and verify destination",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

OUTBOUND_TRANSFER_RETRIEVE = CapabilitySchema(
    capability_key="stripe.treasury.outbound_transfer.retrieve",
    service="stripe",
    category="treasury",
    description="Retrieve a Treasury outbound transfer",
    parameters={
        "outbound_transfer_id": ParameterSchema(
            type="string",
            required=True,
            description="Outbound transfer ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transfer ID"),
        "amount": ReturnFieldSchema(type="integer", description="Amount"),
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
    has_side_effects=False,
)

OUTBOUND_TRANSFER_CANCEL = CapabilitySchema(
    capability_key="stripe.treasury.outbound_transfer.cancel",
    service="stripe",
    category="treasury",
    description="Cancel a Treasury outbound transfer",
    parameters={
        "outbound_transfer_id": ParameterSchema(
            type="string",
            required=True,
            description="Outbound transfer ID to cancel",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transfer ID"),
        "status": ReturnFieldSchema(type="string", description="Should be canceled"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Transfer already processed",
            recovery_hint="Only pending transfers can be canceled",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

OUTBOUND_TRANSFER_LIST = CapabilitySchema(
    capability_key="stripe.treasury.outbound_transfer.list",
    service="stripe",
    category="treasury",
    description="List Treasury outbound transfers",
    parameters={
        "financial_account": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of transfers"),
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

TREASURY_TRANSACTION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.treasury.transaction.retrieve",
    service="stripe",
    category="treasury",
    description="Retrieve a Treasury transaction",
    parameters={
        "transaction_id": ParameterSchema(
            type="string",
            required=True,
            description="Transaction ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transaction ID"),
        "amount": ReturnFieldSchema(type="integer", description="Amount"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "financial_account": ReturnFieldSchema(type="string", description="Account"),
        "flow_type": ReturnFieldSchema(type="string", description="Flow type"),
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
    has_side_effects=False,
)

TREASURY_TRANSACTION_LIST = CapabilitySchema(
    capability_key="stripe.treasury.transaction.list",
    service="stripe",
    category="treasury",
    description="List Treasury transactions",
    parameters={
        "financial_account": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["open", "posted", "void"],
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

OUTBOUND_TRANSFER_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.treasury.outbound_transfer.create": OUTBOUND_TRANSFER_CREATE,
    "stripe.treasury.outbound_transfer.retrieve": OUTBOUND_TRANSFER_RETRIEVE,
    "stripe.treasury.outbound_transfer.cancel": OUTBOUND_TRANSFER_CANCEL,
    "stripe.treasury.outbound_transfer.list": OUTBOUND_TRANSFER_LIST,
    "stripe.treasury.transaction.retrieve": TREASURY_TRANSACTION_RETRIEVE,
    "stripe.treasury.transaction.list": TREASURY_TRANSACTION_LIST,
}
