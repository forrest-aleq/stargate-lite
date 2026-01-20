"""
Plaid Accounts Capability Schemas.

Account listing, balances, auth (account numbers), and identity.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ PLAID ACCOUNTS GET ============

PLAID_ACCOUNTS_GET = CapabilitySchema(
    capability_key="plaid.accounts.get",
    service="plaid",
    category="banking",
    description="Get linked accounts",
    description_detailed=(
        "Retrieves the list of accounts associated with an Item (linked institution). "
        "Returns account names, types, subtypes, and masked account numbers. "
        "Use this to display available accounts before fetching balances or transactions."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Plaid access token for the linked account",
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description="List of accounts with id, name, type, subtype, mask",
        ),
        "item_id": ReturnFieldSchema(
            type="string",
            description="Unique identifier for the Item",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid or expired access token",
            recovery_hint="Re-authenticate user through Plaid Link",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.accesstoken.exchange"],
        typically_followed_by=["plaid.balance.get", "plaid.transactions.sync"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ PLAID BALANCE GET ============

PLAID_BALANCE_GET = CapabilitySchema(
    capability_key="plaid.balance.get",
    service="plaid",
    category="banking",
    description="Get account balances",
    description_detailed=(
        "Retrieves real-time balance information for accounts. Unlike cached data, "
        "this makes a live request to the institution. Returns current balance, "
        "available balance, and credit limit where applicable."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Plaid access token for the linked account",
        ),
        "account_ids": ParameterSchema(
            type="array",
            required=False,
            description="Specific account IDs to fetch (all if omitted)",
            items_type="string",
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description="Accounts with current_balance, available_balance, limit, currency",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid access token or account_ids",
            recovery_hint="Verify access_token and that account_ids exist",
        ),
        ErrorHint(
            error_code=ErrorCode.NETWORK_ERROR,
            description="Institution temporarily unavailable",
            recovery_hint="Retry after a few minutes; check Plaid status page",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.accounts.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ PLAID AUTH GET ============

PLAID_AUTH_GET = CapabilitySchema(
    capability_key="plaid.auth.get",
    service="plaid",
    category="banking",
    description="Get bank account numbers (with TANs support)",
    description_detailed=(
        "Retrieves account and routing numbers for ACH and wire transfers. "
        "Some institutions use tokenized account numbers (TANs) for security. "
        "Requires the 'auth' product to be enabled during Link initialization."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Plaid access token with auth product enabled",
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description="Accounts with routing, account, wire_routing numbers",
        ),
        "numbers": ReturnFieldSchema(
            type="object",
            description="Raw ACH, EFT, and international numbers",
        ),
        "item_id": ReturnFieldSchema(
            type="string",
            description="Unique identifier for the Item",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Auth product not enabled or invalid token",
            recovery_hint="Ensure auth product was requested during Link initialization",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.accounts.get"],
        typically_followed_by=["plaid.transfer.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ PLAID IDENTITY GET ============

PLAID_IDENTITY_GET = CapabilitySchema(
    capability_key="plaid.identity.get",
    service="plaid",
    category="banking",
    description="Get identity information",
    description_detailed=(
        "Retrieves identity information for account holders including names, "
        "addresses, phone numbers, and email addresses. Useful for KYC/AML "
        "verification. Requires the 'identity' product to be enabled."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Plaid access token with identity product enabled",
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description="Accounts with owners array containing identity data",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Identity product not enabled or invalid token",
            recovery_hint="Ensure identity product was requested during Link initialization",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.accesstoken.exchange"],
    ),
    idempotent=True,
    has_side_effects=False,
)

PLAID_ACCOUNTS_SCHEMAS: dict[str, CapabilitySchema] = {
    "plaid.accounts.get": PLAID_ACCOUNTS_GET,
    "plaid.balance.get": PLAID_BALANCE_GET,
    "plaid.auth.get": PLAID_AUTH_GET,
    "plaid.identity.get": PLAID_IDENTITY_GET,
}

__all__ = ["PLAID_ACCOUNTS_SCHEMAS"]
