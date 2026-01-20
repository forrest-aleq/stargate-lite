"""
Chase/JPMorgan Banking Capability Schemas.

Business banking: accounts, transactions, ACH, wire transfers.
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

CHASE_ACCOUNT_LIST = CapabilitySchema(
    capability_key="chase.account.list",
    service="chase",
    category="banking",
    description="List all business banking accounts",
    description_detailed=(
        "Retrieves all business banking accounts linked to the Chase/JPMorgan credentials. "
        "Returns checking, savings, and other account types with balances and status. "
        "Use to get account IDs for transactions and payments."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Chase OAuth access token",
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description="List of accounts with id, number, type, currency, status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Invalid or expired access token",
            recovery_hint="Re-authenticate with Chase OAuth",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["chase.balance.get", "chase.transaction.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ ACCOUNT BALANCE ============

CHASE_BALANCE_GET = CapabilitySchema(
    capability_key="chase.balance.get",
    service="chase",
    category="banking",
    description="Get account balance",
    description_detailed=(
        "Retrieves current and available balance for a specific account. "
        "Current balance includes pending transactions; available balance is "
        "what can be withdrawn or transferred immediately."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Chase OAuth access token",
        ),
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Chase account ID from account.list",
        ),
    },
    returns={
        "account_id": ReturnFieldSchema(
            type="string",
            description="Account ID",
        ),
        "current_balance": ReturnFieldSchema(
            type="number",
            description="Current balance including pending",
        ),
        "available_balance": ReturnFieldSchema(
            type="number",
            description="Available balance for transactions",
        ),
        "currency": ReturnFieldSchema(
            type="string",
            description="Currency code (USD)",
        ),
        "as_of_date": ReturnFieldSchema(
            type="string",
            description="Balance timestamp",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid account_id",
            recovery_hint="Verify account_id from chase.account.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["chase.account.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ TRANSACTIONS GET ============

CHASE_TRANSACTION_GET = CapabilitySchema(
    capability_key="chase.transaction.get",
    service="chase",
    category="banking",
    description="Get account transactions",
    description_detailed=(
        "Retrieves transaction history for an account within a date range. "
        "Includes deposits, withdrawals, transfers, and payment details. "
        "Supports pagination for large transaction volumes."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Chase OAuth access token",
        ),
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Chase account ID",
        ),
        "from_date": ParameterSchema(
            type="string",
            required=False,
            description="Start date (YYYY-MM-DD)",
        ),
        "to_date": ParameterSchema(
            type="string",
            required=False,
            description="End date (YYYY-MM-DD)",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max transactions to return",
            default=100,
        ),
        "offset": ParameterSchema(
            type="integer",
            required=False,
            description="Pagination offset",
            default=0,
        ),
    },
    returns={
        "transactions": ReturnFieldSchema(
            type="array",
            description="List of transactions with id, amount, description, type, date",
        ),
        "total_count": ReturnFieldSchema(
            type="integer",
            description="Total transactions in date range",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid date range or account_id",
            recovery_hint="Verify dates are YYYY-MM-DD and account exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["chase.account.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ ACH PAYMENT CREATE ============

CHASE_ACH_CREATE = CapabilitySchema(
    capability_key="chase.ach.create",
    service="chase",
    category="banking",
    description="Create ACH payment (free for Chase Business)",
    description_detailed=(
        "Creates an ACH (Automated Clearing House) payment to a beneficiary. "
        "ACH is free for Chase Business customers and typically settles in 1-3 days. "
        "Supports same-day ACH for faster delivery at additional cost."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Chase OAuth access token",
        ),
        "source_account_id": ParameterSchema(
            type="string",
            required=True,
            description="Source Chase account ID",
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
            description="Currency code",
            default="USD",
        ),
        "beneficiary_name": ParameterSchema(
            type="string",
            required=True,
            description="Recipient name",
            example="Acme Corp",
        ),
        "beneficiary_account": ParameterSchema(
            type="string",
            required=True,
            description="Recipient bank account number",
        ),
        "beneficiary_routing": ParameterSchema(
            type="string",
            required=True,
            description="Recipient bank routing number (9 digits)",
        ),
        "beneficiary_account_type": ParameterSchema(
            type="string",
            required=False,
            description="Account type",
            default="checking",
            enum=["checking", "savings"],
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Payment description/memo",
            default="Payment via Stargate",
        ),
        "reference": ParameterSchema(
            type="string",
            required=False,
            description="Your reference number",
        ),
        "execution_date": ParameterSchema(
            type="string",
            required=False,
            description="Future payment date (YYYY-MM-DD)",
        ),
        "speed": ParameterSchema(
            type="string",
            required=False,
            description="ACH speed: STANDARD (1-3 days), SAME_DAY, REAL_TIME",
            default="STANDARD",
            enum=["STANDARD", "SAME_DAY", "REAL_TIME"],
        ),
        "idempotency_key": ParameterSchema(
            type="string",
            required=False,
            description="Unique key to prevent duplicate payments",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(
            type="string",
            description="Chase payment ID for tracking",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Payment status (PENDING, PROCESSING, COMPLETED)",
        ),
        "amount": ReturnFieldSchema(
            type="object",
            description="Amount and currency",
        ),
        "execution_date": ReturnFieldSchema(
            type="string",
            description="Scheduled execution date",
        ),
        "tracking_id": ReturnFieldSchema(
            type="string",
            description="ACH tracking ID",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid routing number or insufficient funds",
            recovery_hint="Verify routing number is 9 digits and account has sufficient balance",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["chase.account.list", "chase.balance.get"],
        typically_followed_by=["chase.payment.status"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ WIRE PAYMENT CREATE ============

CHASE_WIRE_CREATE = CapabilitySchema(
    capability_key="chase.wire.create",
    service="chase",
    category="banking",
    description="Create domestic or international wire transfer",
    description_detailed=(
        "Creates a wire transfer for same-day or international payments. "
        "Domestic wires typically complete same-day; international wires take 1-5 days. "
        "Wire transfers have fees but are faster and more secure than ACH."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Chase OAuth access token",
        ),
        "source_account_id": ParameterSchema(
            type="string",
            required=True,
            description="Source Chase account ID",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Wire amount",
            example=25000.00,
        ),
        "currency": ParameterSchema(
            type="string",
            required=False,
            description="Currency code",
            default="USD",
        ),
        "beneficiary_name": ParameterSchema(
            type="string",
            required=True,
            description="Recipient name",
        ),
        "beneficiary_account": ParameterSchema(
            type="string",
            required=True,
            description="Recipient account number or IBAN",
        ),
        "beneficiary_routing": ParameterSchema(
            type="string",
            required=True,
            description="Routing number (domestic) or leave empty for international",
        ),
        "bank_name": ParameterSchema(
            type="string",
            required=False,
            description="Beneficiary bank name",
        ),
        "bank_address": ParameterSchema(
            type="string",
            required=False,
            description="Beneficiary bank address",
        ),
        "wire_type": ParameterSchema(
            type="string",
            required=False,
            description="DOMESTIC or INTERNATIONAL",
            default="DOMESTIC",
            enum=["DOMESTIC", "INTERNATIONAL"],
        ),
        "swift_code": ParameterSchema(
            type="string",
            required=False,
            description="SWIFT/BIC code for international wires",
        ),
        "iban": ParameterSchema(
            type="string",
            required=False,
            description="IBAN for international wires",
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Wire reference/purpose",
        ),
        "reference": ParameterSchema(
            type="string",
            required=False,
            description="Your reference number",
        ),
        "execution_date": ParameterSchema(
            type="string",
            required=False,
            description="Execution date (YYYY-MM-DD)",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(
            type="string",
            description="Chase payment ID",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Wire status",
        ),
        "amount": ReturnFieldSchema(
            type="object",
            description="Amount and currency",
        ),
        "wire_reference": ReturnFieldSchema(
            type="string",
            description="Wire reference number",
        ),
        "estimated_delivery": ReturnFieldSchema(
            type="string",
            description="Estimated delivery date",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Missing SWIFT code for international wire",
            recovery_hint="International wires require swift_code and optionally iban",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["chase.account.list", "chase.balance.get"],
        typically_followed_by=["chase.payment.status"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ PAYMENT STATUS ============

CHASE_PAYMENT_STATUS = CapabilitySchema(
    capability_key="chase.payment.status",
    service="chase",
    category="banking",
    description="Get payment status and details",
    description_detailed=(
        "Retrieves the current status and details of an ACH or wire payment. "
        "Track progress from PENDING through PROCESSING to COMPLETED. "
        "Includes error details if payment failed."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Chase OAuth access token",
        ),
        "payment_id": ParameterSchema(
            type="string",
            required=True,
            description="Chase payment ID",
        ),
    },
    returns={
        "payment_id": ReturnFieldSchema(
            type="string",
            description="Payment ID",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Current status (PENDING, PROCESSING, COMPLETED, FAILED)",
        ),
        "payment_method": ReturnFieldSchema(
            type="string",
            description="ACH or WIRE",
        ),
        "amount": ReturnFieldSchema(
            type="object",
            description="Amount and currency",
        ),
        "beneficiary": ReturnFieldSchema(
            type="object",
            description="Beneficiary details",
        ),
        "execution_date": ReturnFieldSchema(
            type="string",
            description="Execution date",
        ),
        "completion_date": ReturnFieldSchema(
            type="string",
            description="Completion date (if completed)",
        ),
        "tracking_id": ReturnFieldSchema(
            type="string",
            description="ACH/wire tracking ID",
        ),
        "error_details": ReturnFieldSchema(
            type="object",
            description="Error details if payment failed",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Payment not found",
            recovery_hint="Verify payment_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["chase.ach.create", "chase.wire.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ PAYMENT LIST ============

CHASE_PAYMENT_LIST = CapabilitySchema(
    capability_key="chase.payment.list",
    service="chase",
    category="banking",
    description="List payment history",
    description_detailed=(
        "Retrieves a list of payments made through the Chase API. "
        "Filter by date range, status, or payment method. "
        "Use for reconciliation and payment tracking."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Chase OAuth access token",
        ),
        "from_date": ParameterSchema(
            type="string",
            required=False,
            description="Start date (YYYY-MM-DD)",
        ),
        "to_date": ParameterSchema(
            type="string",
            required=False,
            description="End date (YYYY-MM-DD)",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["PENDING", "COMPLETED", "FAILED"],
        ),
        "payment_method": ParameterSchema(
            type="string",
            required=False,
            description="Filter by method (ACH, WIRE)",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max payments to return",
            default=100,
        ),
        "offset": ParameterSchema(
            type="integer",
            required=False,
            description="Pagination offset",
            default=0,
        ),
    },
    returns={
        "payments": ReturnFieldSchema(
            type="array",
            description="List of payments with status, amount, beneficiary, dates",
        ),
        "total_count": ReturnFieldSchema(
            type="integer",
            description="Total payments matching criteria",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Invalid access token",
            recovery_hint="Re-authenticate with Chase OAuth",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["chase.ach.create", "chase.wire.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ RECIPIENT CREATE ============

CHASE_RECIPIENT_CREATE = CapabilitySchema(
    capability_key="chase.recipient.create",
    service="chase",
    category="banking",
    description="Create a payment recipient/beneficiary",
    description_detailed=(
        "Creates a saved recipient for recurring payments. "
        "Store beneficiary bank details securely for future ACH or wire payments. "
        "Reduces data entry errors and speeds up payment creation."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Chase OAuth access token",
        ),
        "name": ParameterSchema(
            type="string",
            required=True,
            description="Recipient name",
            example="Acme Suppliers Inc",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Recipient email for notifications",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Recipient phone number",
        ),
        "account_number": ParameterSchema(
            type="string",
            required=True,
            description="Bank account number",
        ),
        "routing_number": ParameterSchema(
            type="string",
            required=True,
            description="Bank routing number",
        ),
        "account_type": ParameterSchema(
            type="string",
            required=False,
            description="Account type",
            default="checking",
            enum=["checking", "savings"],
        ),
        "bank_name": ParameterSchema(
            type="string",
            required=False,
            description="Bank name",
        ),
        "address_line1": ParameterSchema(
            type="string",
            required=False,
            description="Address line 1",
        ),
        "city": ParameterSchema(
            type="string",
            required=False,
            description="City",
        ),
        "state": ParameterSchema(
            type="string",
            required=False,
            description="State code",
        ),
        "postal_code": ParameterSchema(
            type="string",
            required=False,
            description="Postal/ZIP code",
        ),
        "country": ParameterSchema(
            type="string",
            required=False,
            description="Country code",
            default="US",
        ),
    },
    returns={
        "recipient_id": ReturnFieldSchema(
            type="string",
            description="Chase recipient ID for future payments",
        ),
        "name": ReturnFieldSchema(
            type="string",
            description="Recipient name",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Recipient status (ACTIVE, PENDING)",
        ),
        "created_date": ReturnFieldSchema(
            type="string",
            description="Creation timestamp",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid routing number or account number",
            recovery_hint="Verify routing number is 9 digits",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["chase.ach.create", "chase.wire.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ EXPORT ALL SCHEMAS ============

CHASE_SCHEMAS: dict[str, CapabilitySchema] = {
    "chase.account.list": CHASE_ACCOUNT_LIST,
    "chase.balance.get": CHASE_BALANCE_GET,
    "chase.transaction.get": CHASE_TRANSACTION_GET,
    "chase.ach.create": CHASE_ACH_CREATE,
    "chase.wire.create": CHASE_WIRE_CREATE,
    "chase.payment.status": CHASE_PAYMENT_STATUS,
    "chase.payment.list": CHASE_PAYMENT_LIST,
    "chase.recipient.create": CHASE_RECIPIENT_CREATE,
}

__all__ = ["CHASE_SCHEMAS"]
