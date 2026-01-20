"""
Stripe Connect & Balance Capability Schemas.

Rich metadata for balance, payouts, transfers, and balance transactions.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ BALANCE ============

BALANCE_GET = CapabilitySchema(
    capability_key="stripe.balance.get",
    service="stripe",
    category="connect",
    description="Get current Stripe balance",
    description_detailed=(
        "Retrieves the current account balance, showing available and pending amounts "
        "by currency. Use to check how much can be paid out."
    ),
    parameters={},
    returns={
        "available": ReturnFieldSchema(
            type="array",
            description="Available balance by currency",
            example=[{"amount": 50000, "currency": "usd"}],
        ),
        "pending": ReturnFieldSchema(
            type="array",
            description="Pending balance by currency",
        ),
        "connect_reserved": ReturnFieldSchema(
            type="array",
            description="Reserved funds for Connect (platform accounts)",
        ),
        "livemode": ReturnFieldSchema(type="boolean", description="Live or test mode"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.payout.list", "stripe.balance.transactions.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

BALANCE_TRANSACTIONS_LIST = CapabilitySchema(
    capability_key="stripe.balance.transactions.list",
    service="stripe",
    category="connect",
    description="List Stripe balance transactions",
    description_detailed=(
        "Returns a list of transactions that have contributed to the Stripe account "
        "balance. Includes charges, payouts, refunds, transfers, etc."
    ),
    parameters={
        "type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by transaction type",
            enum=[
                "charge",
                "refund",
                "adjustment",
                "payout",
                "transfer",
                "stripe_fee",
            ],
        ),
        "payout": ParameterSchema(
            type="string",
            required=False,
            description="Filter by payout ID",
        ),
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Filter by source ID (charge, refund, etc.)",
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
        "data": ReturnFieldSchema(
            type="array",
            description="List of balance transactions",
        ),
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

# ============ PAYOUTS ============

PAYOUT_LIST = CapabilitySchema(
    capability_key="stripe.payout.list",
    service="stripe",
    category="connect",
    description="List Stripe payouts",
    description_detailed=(
        "Returns a list of payouts to your bank account. Payouts are the movement "
        "of funds from Stripe to your external account."
    ),
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by payout status",
            enum=["pending", "paid", "failed", "canceled"],
        ),
        "arrival_date": ParameterSchema(
            type="object",
            required=False,
            description="Filter by arrival date (gte, lte)",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of payouts"),
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

PAYOUT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.payout.retrieve",
    service="stripe",
    category="connect",
    description="Retrieve a specific Stripe payout",
    parameters={
        "payout_id": ParameterSchema(
            type="string",
            required=True,
            description="Payout ID",
            example="po_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Payout ID"),
        "status": ReturnFieldSchema(type="string", description="Payout status"),
        "amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "arrival_date": ReturnFieldSchema(type="integer", description="Arrival timestamp"),
        "destination": ReturnFieldSchema(type="string", description="Bank account ID"),
        "failure_code": ReturnFieldSchema(type="string", description="Failure code if failed"),
        "failure_message": ReturnFieldSchema(type="string", description="Failure message"),
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

# ============ TRANSFERS (Connect) ============

TRANSFER_CREATE = CapabilitySchema(
    capability_key="stripe.transfer.create",
    service="stripe",
    category="connect",
    description="Create a transfer to connected account (Connect)",
    description_detailed=(
        "Creates a transfer to a connected Stripe account. Requires Stripe Connect. "
        "Use for marketplace payouts to sellers or service providers."
    ),
    parameters={
        "amount": ParameterSchema(
            type="integer",
            required=True,
            description="Amount in cents to transfer",
            example=1000,
        ),
        "currency": ParameterSchema(
            type="string",
            required=True,
            description="Three-letter ISO currency code",
            example="usd",
        ),
        "destination": ParameterSchema(
            type="string",
            required=True,
            description="Connected account ID",
            example="acct_ABC123",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Description for the transfer",
        ),
        "source_transaction": ParameterSchema(
            type="string",
            required=False,
            description="Charge ID to transfer from",
        ),
        "transfer_group": ParameterSchema(
            type="string",
            required=False,
            description="Group ID for related transfers",
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
            description="Transfer ID",
            example="tr_ABC123",
        ),
        "amount": ReturnFieldSchema(type="integer", description="Amount transferred"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "destination": ReturnFieldSchema(type="string", description="Connected account"),
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
            description="Insufficient balance or invalid destination",
            recovery_hint="Check balance and verify connected account ID",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.balance.get"],
        typically_followed_by=["stripe.transfer.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

TRANSFER_LIST = CapabilitySchema(
    capability_key="stripe.transfer.list",
    service="stripe",
    category="connect",
    description="List transfers to connected accounts",
    parameters={
        "destination": ParameterSchema(
            type="string",
            required=False,
            description="Filter by destination account",
        ),
        "transfer_group": ParameterSchema(
            type="string",
            required=False,
            description="Filter by transfer group",
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

CONNECT_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.balance.get": BALANCE_GET,
    "stripe.balance.transactions.list": BALANCE_TRANSACTIONS_LIST,
    "stripe.payout.list": PAYOUT_LIST,
    "stripe.payout.retrieve": PAYOUT_RETRIEVE,
    "stripe.transfer.create": TRANSFER_CREATE,
    "stripe.transfer.list": TRANSFER_LIST,
}
