"""
Stripe Treasury Capability Schemas.

Rich metadata for embedded banking and financial accounts.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ FINANCIAL ACCOUNTS ============

FINANCIAL_ACCOUNT_CREATE = CapabilitySchema(
    capability_key="stripe.treasury.financial_account.create",
    service="stripe",
    category="treasury",
    description="Create a Treasury financial account",
    description_detailed=(
        "Creates a FinancialAccount for holding funds. Treasury financial accounts "
        "provide banking-like functionality including account numbers and routing numbers."
    ),
    parameters={
        "supported_currencies": ParameterSchema(
            type="array",
            required=True,
            description="Currencies the account will support",
            items_type="string",
            example=["usd"],
        ),
        "features": ParameterSchema(
            type="object",
            required=False,
            description="Features to enable",
            example={
                "card_issuing": {"requested": True},
                "deposit_insurance": {"requested": True},
                "financial_addresses": {"aba": {"requested": True}},
            },
        ),
        "platform_restrictions": ParameterSchema(
            type="object",
            required=False,
            description="Platform-level restrictions",
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
            description="Financial account ID",
            example="fa_ABC123",
        ),
        "supported_currencies": ReturnFieldSchema(type="array", description="Currencies"),
        "balance": ReturnFieldSchema(type="object", description="Current balance"),
        "financial_addresses": ReturnFieldSchema(type="array", description="Bank details"),
        "status": ReturnFieldSchema(type="string", description="Account status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

FINANCIAL_ACCOUNT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.treasury.financial_account.retrieve",
    service="stripe",
    category="treasury",
    description="Retrieve a Treasury financial account",
    parameters={
        "financial_account_id": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Account ID"),
        "balance": ReturnFieldSchema(type="object", description="Balance"),
        "financial_addresses": ReturnFieldSchema(type="array", description="Addresses"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "features": ReturnFieldSchema(type="object", description="Features"),
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

FINANCIAL_ACCOUNT_UPDATE = CapabilitySchema(
    capability_key="stripe.treasury.financial_account.update",
    service="stripe",
    category="treasury",
    description="Update a Treasury financial account",
    parameters={
        "financial_account_id": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID to update",
        ),
        "features": ParameterSchema(
            type="object",
            required=False,
            description="Update features",
        ),
        "platform_restrictions": ParameterSchema(
            type="object",
            required=False,
            description="Update restrictions",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Account ID"),
        "features": ReturnFieldSchema(type="object", description="Updated features"),
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

FINANCIAL_ACCOUNT_LIST = CapabilitySchema(
    capability_key="stripe.treasury.financial_account.list",
    service="stripe",
    category="treasury",
    description="List Treasury financial accounts",
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of accounts"),
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

# ============ OUTBOUND PAYMENTS ============

OUTBOUND_PAYMENT_CREATE = CapabilitySchema(
    capability_key="stripe.treasury.outbound_payment.create",
    service="stripe",
    category="treasury",
    description="Create a Treasury outbound payment",
    description_detailed=(
        "Creates an outbound payment from a FinancialAccount to an external "
        "destination (bank account, debit card, or Stripe account)."
    ),
    parameters={
        "financial_account": ParameterSchema(
            type="string",
            required=True,
            description="Source financial account ID",
        ),
        "amount": ParameterSchema(
            type="integer",
            required=True,
            description="Amount in cents",
            example=10000,
        ),
        "currency": ParameterSchema(
            type="string",
            required=True,
            description="Currency code",
            example="usd",
        ),
        "destination_payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Destination payment method ID",
        ),
        "destination_payment_method_data": ParameterSchema(
            type="object",
            required=False,
            description="Inline destination data",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Description for the payment",
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
        "id": ReturnFieldSchema(type="string", description="Outbound payment ID"),
        "amount": ReturnFieldSchema(type="integer", description="Amount"),
        "status": ReturnFieldSchema(type="string", description="Payment status"),
        "financial_account": ReturnFieldSchema(type="string", description="Source"),
        "expected_arrival_date": ReturnFieldSchema(type="integer", description="ETA"),
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

OUTBOUND_PAYMENT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.treasury.outbound_payment.retrieve",
    service="stripe",
    category="treasury",
    description="Retrieve a Treasury outbound payment",
    parameters={
        "outbound_payment_id": ParameterSchema(
            type="string",
            required=True,
            description="Outbound payment ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Payment ID"),
        "amount": ReturnFieldSchema(type="integer", description="Amount"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "financial_account": ReturnFieldSchema(type="string", description="Source"),
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

OUTBOUND_PAYMENT_CANCEL = CapabilitySchema(
    capability_key="stripe.treasury.outbound_payment.cancel",
    service="stripe",
    category="treasury",
    description="Cancel a Treasury outbound payment",
    parameters={
        "outbound_payment_id": ParameterSchema(
            type="string",
            required=True,
            description="Outbound payment ID to cancel",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Payment ID"),
        "status": ReturnFieldSchema(type="string", description="Should be canceled"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Payment already processed",
            recovery_hint="Only pending payments can be canceled",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

OUTBOUND_PAYMENT_LIST = CapabilitySchema(
    capability_key="stripe.treasury.outbound_payment.list",
    service="stripe",
    category="treasury",
    description="List Treasury outbound payments",
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
        "data": ReturnFieldSchema(type="array", description="List of payments"),
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

TREASURY_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.treasury.financial_account.create": FINANCIAL_ACCOUNT_CREATE,
    "stripe.treasury.financial_account.retrieve": FINANCIAL_ACCOUNT_RETRIEVE,
    "stripe.treasury.financial_account.update": FINANCIAL_ACCOUNT_UPDATE,
    "stripe.treasury.financial_account.list": FINANCIAL_ACCOUNT_LIST,
    "stripe.treasury.outbound_payment.create": OUTBOUND_PAYMENT_CREATE,
    "stripe.treasury.outbound_payment.retrieve": OUTBOUND_PAYMENT_RETRIEVE,
    "stripe.treasury.outbound_payment.cancel": OUTBOUND_PAYMENT_CANCEL,
    "stripe.treasury.outbound_payment.list": OUTBOUND_PAYMENT_LIST,
}
