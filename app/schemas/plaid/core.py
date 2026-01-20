"""
Plaid Core Capability Schemas.

Link token creation, access token exchange, transactions sync.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ PLAID LINK TOKEN CREATE ============

PLAID_LINK_CREATE = CapabilitySchema(
    capability_key="plaid.link.create",
    service="plaid",
    category="banking",
    description="Create Link token for Plaid initialization",
    description_detailed=(
        "Creates a Link token to initialize Plaid Link in the client application. "
        "Link is the client-side component that users interact with to connect their "
        "bank accounts. The token is short-lived and must be used immediately."
    ),
    parameters={
        "products": ParameterSchema(
            type="array",
            required=False,
            description="Plaid products to enable (transactions, auth, identity, balance)",
            items_type="string",
            default=["transactions", "auth", "identity"],
            example=["transactions", "auth"],
        ),
        "client_name": ParameterSchema(
            type="string",
            required=False,
            description="Name displayed to user during Link flow",
            default="Stargate Lite",
        ),
        "webhook": ParameterSchema(
            type="string",
            required=False,
            description="Webhook URL for transaction updates",
        ),
    },
    returns={
        "link_token": ReturnFieldSchema(
            type="string",
            description="Token for initializing Plaid Link",
        ),
        "expiration": ReturnFieldSchema(
            type="string",
            description="Token expiration timestamp (typically 30 minutes)",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Plaid client ID or secret not configured",
            recovery_hint="Ensure PLAID_CLIENT_ID and PLAID_SECRET are set",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["plaid.accesstoken.exchange"],
    ),
    idempotent=False,
    has_side_effects=False,
)

# ============ PLAID ACCESS TOKEN EXCHANGE ============

PLAID_ACCESSTOKEN_EXCHANGE = CapabilitySchema(
    capability_key="plaid.accesstoken.exchange",
    service="plaid",
    category="banking",
    description="Exchange public token for access token",
    description_detailed=(
        "Exchanges the public_token returned by Plaid Link for a permanent access_token. "
        "This access_token is used for all subsequent API calls to retrieve account data. "
        "Must be stored securely - it provides full access to the linked account."
    ),
    parameters={
        "public_token": ParameterSchema(
            type="string",
            required=True,
            description="Public token from Plaid Link onSuccess callback",
        ),
    },
    returns={
        "access_token": ReturnFieldSchema(
            type="string",
            description="Permanent access token for API calls (store securely)",
        ),
        "item_id": ReturnFieldSchema(
            type="string",
            description="Unique identifier for the Item (linked institution)",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid or expired public token",
            recovery_hint="Public tokens expire quickly - re-initiate Link flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.link.create"],
        typically_followed_by=["plaid.accounts.get", "plaid.transactions.sync"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ PLAID TRANSACTIONS SYNC ============

PLAID_TRANSACTIONS_SYNC = CapabilitySchema(
    capability_key="plaid.transactions.sync",
    service="plaid",
    category="banking",
    description="Get transactions using sync (2025 recommended)",
    description_detailed=(
        "Retrieves transactions using the /transactions/sync endpoint (recommended method). "
        "Returns added, modified, and removed transactions since the last sync. "
        "Use cursor-based pagination for efficient incremental updates."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Plaid access token for the linked account",
        ),
        "cursor": ParameterSchema(
            type="string",
            required=False,
            description="Cursor from previous sync for incremental updates",
        ),
        "count": ParameterSchema(
            type="integer",
            required=False,
            description="Number of transactions to fetch per page",
            default=100,
        ),
    },
    returns={
        "transactions_added": ReturnFieldSchema(
            type="array",
            description="New transactions since last sync",
        ),
        "transactions_modified": ReturnFieldSchema(
            type="array",
            description="Transactions that have been modified",
        ),
        "transactions_removed": ReturnFieldSchema(
            type="array",
            description="Transaction IDs that have been removed",
        ),
        "next_cursor": ReturnFieldSchema(
            type="string",
            description="Cursor for next page (save for incremental sync)",
        ),
        "has_more": ReturnFieldSchema(
            type="boolean",
            description="Whether more transactions are available",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid access token or cursor",
            recovery_hint="Verify access_token is valid; if cursor expired, start fresh sync",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.accesstoken.exchange"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# Legacy alias - transactions.get uses the same underlying sync method
PLAID_TRANSACTIONS_GET = CapabilitySchema(
    capability_key="plaid.transactions.get",
    service="plaid",
    category="banking",
    description="Get transactions (legacy method - uses sync)",
    description_detailed=PLAID_TRANSACTIONS_SYNC.description_detailed,
    parameters=PLAID_TRANSACTIONS_SYNC.parameters,
    returns=PLAID_TRANSACTIONS_SYNC.returns,
    errors=PLAID_TRANSACTIONS_SYNC.errors,
    workflow=PLAID_TRANSACTIONS_SYNC.workflow,
    idempotent=True,
    has_side_effects=False,
)

PLAID_CORE_SCHEMAS: dict[str, CapabilitySchema] = {
    "plaid.link.create": PLAID_LINK_CREATE,
    "plaid.accesstoken.exchange": PLAID_ACCESSTOKEN_EXCHANGE,
    "plaid.transactions.sync": PLAID_TRANSACTIONS_SYNC,
    "plaid.transactions.get": PLAID_TRANSACTIONS_GET,
}

__all__ = ["PLAID_CORE_SCHEMAS"]
