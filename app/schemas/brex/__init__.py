"""
Brex Capability Schemas.

Rich metadata for Brex corporate card, expense management, and payment operations.
Finance teams use Brex for corporate cards, spend management, and vendor payments.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ TRANSACTION LIST ============

BREX_TRANSACTION_LIST = CapabilitySchema(
    capability_key="brex.transaction.list",
    service="brex",
    category="transactions",
    description="List card transactions in Brex",
    description_detailed=(
        "List card transactions within a date range. Includes merchant details, "
        "card info, and posting status. Supports cursor-based pagination."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Brex OAuth access token",
        ),
        "start_date": ParameterSchema(
            type="string",
            required=False,
            description="Start date (ISO 8601)",
            example="2025-01-01T00:00:00Z",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="End date (ISO 8601)",
            example="2025-01-31T23:59:59Z",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max transactions to return (default: 100)",
        ),
    },
    returns={
        "transactions": ReturnFieldSchema(
            type="array",
            description=(
                "Transactions with id, amount, merchant_name, card_id, user_id, status, posted_at"
            ),
        ),
        "next_cursor": ReturnFieldSchema(
            type="string",
            description="Cursor for next page (null if no more)",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Brex OAuth token not provided",
            recovery_hint="User must connect Brex account",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["brex.expense.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ EXPENSE LIST ============

BREX_EXPENSE_LIST = CapabilitySchema(
    capability_key="brex.expense.list",
    service="brex",
    category="expenses",
    description="List expenses with categories in Brex",
    description_detailed=(
        "List expenses with category assignments, memos, and receipts. "
        "Useful for expense reporting and reconciliation."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Brex OAuth access token",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max expenses to return (default: 100)",
        ),
    },
    returns={
        "expenses": ReturnFieldSchema(
            type="array",
            description="Expenses with id, amount, memo, category, receipts, purchase_date",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Brex OAuth token not provided",
            recovery_hint="User must connect Brex account",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["brex.transaction.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ VIRTUAL CARD CREATE ============

BREX_CARD_VIRTUAL_CREATE = CapabilitySchema(
    capability_key="brex.card.virtual.create",
    service="brex",
    category="cards",
    description="Create virtual card with spending limits",
    description_detailed=(
        "Create a new virtual card with configurable spending limits. "
        "Assign to a user and set monthly or per-transaction limits."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Brex OAuth access token",
        ),
        "user_id": ParameterSchema(
            type="string",
            required=True,
            description="Brex user ID to assign card to",
        ),
        "display_name": ParameterSchema(
            type="string",
            required=True,
            description="Card display name",
            example="Software Subscriptions",
        ),
        "spend_limit": ParameterSchema(
            type="number",
            required=True,
            description="Spending limit amount",
            example=5000.00,
        ),
        "limit_duration": ParameterSchema(
            type="string",
            required=False,
            description="Limit duration (default: MONTHLY)",
            enum=["MONTHLY", "QUARTERLY", "YEARLY", "PER_TRANSACTION"],
        ),
    },
    returns={
        "card_id": ReturnFieldSchema(type="string", description="Created card ID"),
        "last_four": ReturnFieldSchema(type="string", description="Last 4 digits of card number"),
        "status": ReturnFieldSchema(type="string", description="Card status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Brex OAuth token not provided",
            recovery_hint="User must connect Brex account",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid user_id or spend limit",
            recovery_hint="Verify user exists and limit is within account allowance",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["brex.card.limit.update"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ CARD LOCK ============

BREX_CARD_LOCK = CapabilitySchema(
    capability_key="brex.card.lock",
    service="brex",
    category="cards",
    description="Lock a card in Brex",
    description_detailed=(
        "Lock a card to prevent new transactions. Useful for suspected fraud, "
        "employee offboarding, or temporary spend freezes."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Brex OAuth access token",
        ),
        "card_id": ParameterSchema(
            type="string",
            required=True,
            description="Card ID to lock",
            example="card_123456789",
        ),
    },
    returns={
        "card_id": ReturnFieldSchema(type="string", description="Locked card ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'locked'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Brex OAuth token not provided",
            recovery_hint="User must connect Brex account",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Card not found",
            recovery_hint="Verify card_id exists",
        ),
    ],
    workflow=WorkflowHints(
        related_capabilities=["brex.card.unlock"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ CARD UNLOCK ============

BREX_CARD_UNLOCK = CapabilitySchema(
    capability_key="brex.card.unlock",
    service="brex",
    category="cards",
    description="Unlock a card in Brex",
    description_detailed=(
        "Unlock a previously locked card to resume transactions. " "Card returns to active status."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Brex OAuth access token",
        ),
        "card_id": ParameterSchema(
            type="string",
            required=True,
            description="Card ID to unlock",
            example="card_123456789",
        ),
    },
    returns={
        "card_id": ReturnFieldSchema(type="string", description="Unlocked card ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'active'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Brex OAuth token not provided",
            recovery_hint="User must connect Brex account",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Card not found or cannot be unlocked",
            recovery_hint="Verify card_id exists and card is in locked state",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["brex.card.lock"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ CARD LIMIT UPDATE ============

BREX_CARD_LIMIT_UPDATE = CapabilitySchema(
    capability_key="brex.card.limit.update",
    service="brex",
    category="cards",
    description="Update card spending limit",
    description_detailed=(
        "Update the spending limit for an existing card. " "Can increase or decrease the limit."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Brex OAuth access token",
        ),
        "card_id": ParameterSchema(
            type="string",
            required=True,
            description="Card ID to update",
            example="card_123456789",
        ),
        "new_limit": ParameterSchema(
            type="number",
            required=True,
            description="New spending limit amount",
            example=10000.00,
        ),
    },
    returns={
        "card_id": ReturnFieldSchema(type="string", description="Updated card ID"),
        "new_limit": ReturnFieldSchema(type="number", description="New spending limit"),
        "status": ReturnFieldSchema(type="string", description="Should be 'updated'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Brex OAuth token not provided",
            recovery_hint="User must connect Brex account",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Card not found or limit exceeds account allowance",
            recovery_hint="Verify card_id exists and limit is within bounds",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["brex.card.virtual.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ PAYMENT CREATE ============

BREX_PAYMENT_CREATE = CapabilitySchema(
    capability_key="brex.payment.create",
    service="brex",
    category="payments",
    description="Create vendor payment in Brex",
    description_detailed=(
        "Create a vendor payment from Brex Cash account. "
        "Requires a counterparty (vendor) to be set up in Brex."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Brex OAuth access token",
        ),
        "counterparty_id": ParameterSchema(
            type="string",
            required=True,
            description="Brex counterparty (vendor) ID",
            example="cpty_123456789",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Payment amount",
            example=5000.00,
        ),
        "currency": ParameterSchema(
            type="string",
            required=False,
            description="Payment currency (default: USD)",
            example="USD",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Payment description/memo",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(type="string", description="Created payment ID"),
        "status": ReturnFieldSchema(type="string", description="Payment status"),
        "amount": ReturnFieldSchema(type="object", description="Payment amount with currency"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Brex OAuth token not provided",
            recovery_hint="User must connect Brex account",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Insufficient funds or invalid counterparty",
            recovery_hint="Check cash balance and verify counterparty_id",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["brex.balance.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ BALANCE GET ============

BREX_BALANCE_GET = CapabilitySchema(
    capability_key="brex.balance.get",
    service="brex",
    category="accounts",
    description="Get cash account balance",
    description_detailed=(
        "Get current and available balances for Brex Cash accounts. "
        "Shows all cash accounts with their respective balances."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Brex OAuth access token",
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description=(
                "Cash accounts with account_id, name, current_balance, available_balance, currency"
            ),
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Brex OAuth token not provided",
            recovery_hint="User must connect Brex account",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["brex.payment.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# Export all schemas
BREX_SCHEMAS: dict[str, CapabilitySchema] = {
    "brex.transaction.list": BREX_TRANSACTION_LIST,
    "brex.expense.list": BREX_EXPENSE_LIST,
    "brex.card.virtual.create": BREX_CARD_VIRTUAL_CREATE,
    "brex.card.lock": BREX_CARD_LOCK,
    "brex.card.unlock": BREX_CARD_UNLOCK,
    "brex.card.limit.update": BREX_CARD_LIMIT_UPDATE,
    "brex.payment.create": BREX_PAYMENT_CREATE,
    "brex.balance.get": BREX_BALANCE_GET,
}

__all__ = ["BREX_SCHEMAS"]
