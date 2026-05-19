"""
Mercury Capability Schemas.

Rich metadata for Mercury startup banking operations.
Startups use Mercury for accounts, payments, wire transfers, and treasury management.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ ACCOUNT LIST ============

MERCURY_ACCOUNT_LIST = CapabilitySchema(
    capability_key="mercury.account.list",
    service="mercury",
    category="accounts",
    description="List Mercury banking accounts",
    description_detailed=(
        "List all Mercury bank accounts for the organization. Returns account "
        "details including balances, account types, and status."
    ),
    parameters={},
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description="Accounts with account_id, name, type, balance, currency, status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Mercury API key not configured",
            recovery_hint="Set MERCURY_API_KEY in environment",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["mercury.transaction.get", "mercury.payment.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ TRANSACTION GET ============

MERCURY_TRANSACTION_GET = CapabilitySchema(
    capability_key="mercury.transaction.get",
    service="mercury",
    category="transactions",
    description="Get transactions from Mercury",
    description_detailed=(
        "Get transactions for a Mercury account within a date range. "
        "Supports pagination via offset parameter."
    ),
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Mercury account ID",
            example="acct_123456789",
        ),
        "start_date": ParameterSchema(
            type="string",
            required=False,
            description="Start date (YYYY-MM-DD)",
            example="2025-01-01",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="End date (YYYY-MM-DD)",
            example="2025-01-31",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max transactions to return (default: 100)",
        ),
        "offset": ParameterSchema(
            type="integer",
            required=False,
            description="Pagination offset (default: 0)",
        ),
    },
    returns={
        "transactions": ReturnFieldSchema(
            type="array",
            description=(
                "Transactions with transaction_id, amount, description, status, "
                "posted_at, counterparty_name"
            ),
        ),
        "total": ReturnFieldSchema(type="integer", description="Total transaction count"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Mercury API key not configured",
            recovery_hint="Set MERCURY_API_KEY in environment",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Account not found",
            recovery_hint="Verify account_id exists using mercury.account.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["mercury.account.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ PAYMENT CREATE ============

MERCURY_PAYMENT_CREATE = CapabilitySchema(
    capability_key="mercury.payment.create",
    service="mercury",
    category="payments",
    description="Create ACH payment (100 free/month)",
    description_detailed=(
        "Create an ACH payment from a Mercury account to a recipient. "
        "Mercury offers 100 free ACH payments per month. Use idempotency_key "
        "to prevent duplicate payments."
    ),
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Mercury account ID to pay from",
            example="acct_123456789",
        ),
        "recipient_id": ParameterSchema(
            type="string",
            required=True,
            description="Recipient ID (create with mercury.recipient.create)",
            example="rcpt_987654321",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Payment amount in USD",
            example=1500.00,
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Payment description (default: 'Payment via Stargate')",
        ),
        "idempotency_key": ParameterSchema(
            type="string",
            required=False,
            description="Unique key to prevent duplicate payments",
            example="pay_inv_2025_001",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(type="string", description="Created payment ID"),
        "status": ReturnFieldSchema(type="string", description="Payment status"),
        "amount": ReturnFieldSchema(type="number", description="Payment amount"),
        "estimated_delivery": ReturnFieldSchema(
            type="string",
            description="Estimated delivery date",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Mercury API key not configured",
            recovery_hint="Set MERCURY_API_KEY in environment",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Insufficient funds or invalid recipient",
            recovery_hint="Check account balance and verify recipient_id",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["mercury.recipient.create", "mercury.account.list"],
        related_capabilities=["mercury.wire.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ RECIPIENT CREATE ============

MERCURY_RECIPIENT_CREATE = CapabilitySchema(
    capability_key="mercury.recipient.create",
    service="mercury",
    category="recipients",
    description="Create payment recipient",
    description_detailed=(
        "Create a payment recipient in Mercury with bank account details. "
        "Required before creating ACH payments or wire transfers."
    ),
    parameters={
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Recipient name",
            example="Acme Consulting Inc",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Recipient email address",
            example="accounting@acme.com",
        ),
        "routing_number": ParameterSchema(
            type="string",
            required=True,
            description="Bank routing number (9 digits)",
            example="021000021",
        ),
        "account_number": ParameterSchema(
            type="string",
            required=True,
            description="Bank account number",
            example="123456789012",
        ),
        "account_type": ParameterSchema(
            type="string",
            required=False,
            description="Account type (default: checking)",
            enum=["checking", "savings"],
        ),
    },
    returns={
        "recipient_id": ReturnFieldSchema(type="string", description="Created recipient ID"),
        "name": ReturnFieldSchema(type="string", description="Recipient name"),
        "status": ReturnFieldSchema(type="string", description="Recipient status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Mercury API key not configured",
            recovery_hint="Set MERCURY_API_KEY in environment",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid routing number or account number",
            recovery_hint="Verify bank account details are correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["mercury.payment.create", "mercury.wire.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ RECIPIENT LIST ============

MERCURY_RECIPIENT_LIST = CapabilitySchema(
    capability_key="mercury.recipient.list",
    service="mercury",
    category="recipients",
    description="List payment recipients",
    description_detailed=(
        "List all payment recipients configured in Mercury. Use to find recipient_id for payments."
    ),
    parameters={},
    returns={
        "recipients": ReturnFieldSchema(
            type="array",
            description="Recipients with recipient_id, name, email, status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Mercury API key not configured",
            recovery_hint="Set MERCURY_API_KEY in environment",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["mercury.payment.create", "mercury.wire.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ WIRE CREATE ============

MERCURY_WIRE_CREATE = CapabilitySchema(
    capability_key="mercury.wire.create",
    service="mercury",
    category="payments",
    description="Create wire transfer (domestic/international)",
    description_detailed=(
        "Create a wire transfer from a Mercury account. Mercury offers free "
        "domestic and international wire transfers. Faster than ACH but "
        "typically used for larger or time-sensitive payments."
    ),
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Mercury account ID to wire from",
            example="acct_123456789",
        ),
        "recipient_id": ParameterSchema(
            type="string",
            required=True,
            description="Recipient ID (create with mercury.recipient.create)",
            example="rcpt_987654321",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Wire amount in USD",
            example=50000.00,
        ),
        "wire_type": ParameterSchema(
            type="string",
            required=False,
            description="Wire type (default: domestic)",
            enum=["domestic", "international"],
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Wire transfer description/reference",
        ),
    },
    returns={
        "wire_id": ReturnFieldSchema(type="string", description="Created wire transfer ID"),
        "status": ReturnFieldSchema(type="string", description="Wire status"),
        "amount": ReturnFieldSchema(type="number", description="Wire amount"),
        "fee": ReturnFieldSchema(type="number", description="Wire fee (typically $0 for Mercury)"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Mercury API key not configured",
            recovery_hint="Set MERCURY_API_KEY in environment",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Insufficient funds or invalid recipient",
            recovery_hint="Check account balance and verify recipient has wire-compatible details",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["mercury.recipient.create", "mercury.account.list"],
        related_capabilities=["mercury.payment.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# Export all schemas
MERCURY_SCHEMAS: dict[str, CapabilitySchema] = {
    "mercury.account.list": MERCURY_ACCOUNT_LIST,
    "mercury.transaction.get": MERCURY_TRANSACTION_GET,
    "mercury.payment.create": MERCURY_PAYMENT_CREATE,
    "mercury.recipient.create": MERCURY_RECIPIENT_CREATE,
    "mercury.recipient.list": MERCURY_RECIPIENT_LIST,
    "mercury.wire.create": MERCURY_WIRE_CREATE,
}

__all__ = ["MERCURY_SCHEMAS"]
