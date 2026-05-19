"""
Stripe Financial Connections Capability Schemas.

Rich metadata for linked bank accounts and financial data access.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ SESSIONS ============

FC_SESSION_CREATE = CapabilitySchema(
    capability_key="stripe.financial_connections.session.create",
    service="stripe",
    category="financial_connections",
    description="Create a Financial Connections session",
    description_detailed=(
        "Creates a session for a customer to connect their bank account. "
        "The session provides a secure interface for account linking."
    ),
    parameters={
        "account_holder": ParameterSchema(
            type="object",
            required=True,
            description="Account holder info",
            example={"type": "customer", "customer": "cus_ABC123"},
        ),
        "permissions": ParameterSchema(
            type="array",
            required=True,
            description="Permissions to request",
            items_type="string",
            example=["balances", "transactions", "payment_method"],
        ),
        "filters": ParameterSchema(
            type="object",
            required=False,
            description="Account filters",
            example={"countries": ["US"]},
        ),
        "return_url": ParameterSchema(
            type="string",
            required=False,
            description="URL to return to after linking",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Session ID"),
        "client_secret": ReturnFieldSchema(type="string", description="Client secret"),
        "accounts": ReturnFieldSchema(type="array", description="Linked accounts"),
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

FC_SESSION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.financial_connections.session.retrieve",
    service="stripe",
    category="financial_connections",
    description="Retrieve a Financial Connections session",
    parameters={
        "session_id": ParameterSchema(
            type="string",
            required=True,
            description="Session ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Session ID"),
        "accounts": ReturnFieldSchema(type="array", description="Linked accounts"),
        "permissions": ReturnFieldSchema(type="array", description="Permissions"),
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

# ============ ACCOUNTS ============

FC_ACCOUNT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.financial_connections.account.retrieve",
    service="stripe",
    category="financial_connections",
    description="Retrieve a linked financial account",
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Account ID"),
        "institution_name": ReturnFieldSchema(type="string", description="Bank name"),
        "last4": ReturnFieldSchema(type="string", description="Last 4 digits"),
        "display_name": ReturnFieldSchema(type="string", description="Account name"),
        "status": ReturnFieldSchema(type="string", description="Connection status"),
        "balance": ReturnFieldSchema(type="object", description="Account balance"),
        "ownership": ReturnFieldSchema(type="object", description="Ownership info"),
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

FC_ACCOUNT_REFRESH = CapabilitySchema(
    capability_key="stripe.financial_connections.account.refresh",
    service="stripe",
    category="financial_connections",
    description="Refresh financial account data",
    description_detailed=(
        "Refreshes the data for a linked account including balance and transaction information."
    ),
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID",
        ),
        "features": ParameterSchema(
            type="array",
            required=True,
            description="Data to refresh",
            items_type="string",
            example=["balance", "transactions"],
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Account ID"),
        "balance_refresh": ReturnFieldSchema(type="object", description="Balance refresh"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Account disconnected or refresh not permitted",
            recovery_hint="Check account status and permissions",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

FC_ACCOUNT_DISCONNECT = CapabilitySchema(
    capability_key="stripe.financial_connections.account.disconnect",
    service="stripe",
    category="financial_connections",
    description="Disconnect a financial account",
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID to disconnect",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Account ID"),
        "status": ReturnFieldSchema(type="string", description="Should be disconnected"),
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

FC_ACCOUNT_LIST = CapabilitySchema(
    capability_key="stripe.financial_connections.account.list",
    service="stripe",
    category="financial_connections",
    description="List linked financial accounts",
    parameters={
        "account_holder": ParameterSchema(
            type="object",
            required=False,
            description="Filter by account holder",
        ),
        "session": ParameterSchema(
            type="string",
            required=False,
            description="Filter by session ID",
        ),
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

FC_ACCOUNT_OWNERS_LIST = CapabilitySchema(
    capability_key="stripe.financial_connections.account.owners.list",
    service="stripe",
    category="financial_connections",
    description="List account owners",
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID",
        ),
        "ownership": ParameterSchema(
            type="string",
            required=True,
            description="Ownership object ID",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of owners"),
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

FC_TRANSACTION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.financial_connections.transaction.retrieve",
    service="stripe",
    category="financial_connections",
    description="Retrieve a financial transaction",
    parameters={
        "transaction_id": ParameterSchema(
            type="string",
            required=True,
            description="Transaction ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Transaction ID"),
        "account": ReturnFieldSchema(type="string", description="Account ID"),
        "amount": ReturnFieldSchema(type="integer", description="Amount in cents"),
        "currency": ReturnFieldSchema(type="string", description="Currency"),
        "description": ReturnFieldSchema(type="string", description="Description"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "transacted_at": ReturnFieldSchema(type="integer", description="Timestamp"),
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

FC_TRANSACTION_LIST = CapabilitySchema(
    capability_key="stripe.financial_connections.transaction.list",
    service="stripe",
    category="financial_connections",
    description="List financial transactions",
    parameters={
        "account": ParameterSchema(
            type="string",
            required=True,
            description="Financial account ID",
        ),
        "transacted_at": ParameterSchema(
            type="object",
            required=False,
            description="Filter by transaction date",
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

FINANCIAL_CONNECTIONS_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.financial_connections.session.create": FC_SESSION_CREATE,
    "stripe.financial_connections.session.retrieve": FC_SESSION_RETRIEVE,
    "stripe.financial_connections.account.retrieve": FC_ACCOUNT_RETRIEVE,
    "stripe.financial_connections.account.refresh": FC_ACCOUNT_REFRESH,
    "stripe.financial_connections.account.disconnect": FC_ACCOUNT_DISCONNECT,
    "stripe.financial_connections.account.list": FC_ACCOUNT_LIST,
    "stripe.financial_connections.account.owners.list": FC_ACCOUNT_OWNERS_LIST,
    "stripe.financial_connections.transaction.retrieve": FC_TRANSACTION_RETRIEVE,
    "stripe.financial_connections.transaction.list": FC_TRANSACTION_LIST,
}
