"""
Plaid Transfer Capability Schemas.

ACH transfers, transfer status, processor tokens.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ PLAID TRANSFER CREATE ============

PLAID_TRANSFER_CREATE = CapabilitySchema(
    capability_key="plaid.transfer.create",
    service="plaid",
    category="banking",
    description="Create ACH transfer via Plaid",
    description_detailed=(
        "Creates an ACH transfer to move money between accounts using Plaid Transfer. "
        "Supports debit (pull money from user) and credit (push money to user) transfers. "
        "Same-day ACH available with 'same-day-ach' network option."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Plaid access token for the source/destination account",
        ),
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Account ID for the transfer",
        ),
        "transfer_type": ParameterSchema(
            type="string",
            required=False,
            description="Transfer type: 'debit' (pull) or 'credit' (push)",
            default="debit",
            enum=["debit", "credit"],
        ),
        "network": ParameterSchema(
            type="string",
            required=False,
            description="Transfer network: 'ach' (standard) or 'same-day-ach'",
            default="ach",
            enum=["ach", "same-day-ach"],
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Transfer amount in dollars",
            example=100.00,
        ),
        "description": ParameterSchema(
            type="string",
            required=False,
            description="Transfer description (appears on bank statement)",
            default="Transfer",
        ),
        "ach_class": ParameterSchema(
            type="string",
            required=False,
            description="ACH class: 'ppd' (personal), 'ccd' (business), 'web' (internet)",
            default="ppd",
            enum=["ppd", "ccd", "web"],
        ),
        "user_legal_name": ParameterSchema(
            type="string",
            required=True,
            description="Legal name of the account holder",
        ),
        "idempotency_key": ParameterSchema(
            type="string",
            required=False,
            description="Unique key to prevent duplicate transfers",
        ),
    },
    returns={
        "transfer_id": ReturnFieldSchema(
            type="string",
            description="Unique transfer ID for tracking",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Transfer status (pending, posted, cancelled, failed)",
        ),
        "amount": ReturnFieldSchema(
            type="string",
            description="Transfer amount",
        ),
        "network": ReturnFieldSchema(
            type="string",
            description="Transfer network used",
        ),
        "expected_funds_available_date": ReturnFieldSchema(
            type="string",
            description="Expected date funds will be available",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid account, amount, or transfer configuration",
            recovery_hint="Verify account_id exists and amount is valid",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Insufficient funds for debit transfer",
            recovery_hint="Check balance before initiating transfer",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.auth.get", "plaid.balance.get"],
        typically_followed_by=["plaid.transfer.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ PLAID TRANSFER GET ============

PLAID_TRANSFER_GET = CapabilitySchema(
    capability_key="plaid.transfer.get",
    service="plaid",
    category="banking",
    description="Get transfer status",
    description_detailed=(
        "Retrieves the current status and details of a transfer. "
        "Use this to track transfer progress and handle failures."
    ),
    parameters={
        "transfer_id": ParameterSchema(
            type="string",
            required=True,
            description="Transfer ID from plaid.transfer.create",
        ),
    },
    returns={
        "transfer_id": ReturnFieldSchema(
            type="string",
            description="Transfer ID",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Current status (pending, posted, cancelled, failed, returned)",
        ),
        "amount": ReturnFieldSchema(
            type="string",
            description="Transfer amount",
        ),
        "type": ReturnFieldSchema(
            type="string",
            description="Transfer type (debit or credit)",
        ),
        "created": ReturnFieldSchema(
            type="string",
            description="Creation timestamp",
        ),
        "network": ReturnFieldSchema(
            type="string",
            description="Transfer network",
        ),
        "cancellable": ReturnFieldSchema(
            type="boolean",
            description="Whether transfer can still be cancelled",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="Transfer not found",
            recovery_hint="Verify transfer_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.transfer.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ PLAID PROCESSOR TOKEN CREATE ============

PLAID_PROCESSOR_TOKEN_CREATE = CapabilitySchema(
    capability_key="plaid.processor.token.create",
    service="plaid",
    category="banking",
    description="Create processor token for third-party",
    description_detailed=(
        "Creates a processor token to share account access with a third-party processor "
        "(Stripe, Dwolla, etc.) without exposing the access_token. The processor token "
        "is single-use and scoped to the specified account and processor."
    ),
    parameters={
        "access_token": ParameterSchema(
            type="string",
            required=True,
            description="Plaid access token for the account",
        ),
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Account ID to create token for",
        ),
        "processor": ParameterSchema(
            type="string",
            required=False,
            description="Processor name (stripe, dwolla, checkbook, etc.)",
            default="stripe",
            example="stripe",
        ),
    },
    returns={
        "processor_token": ReturnFieldSchema(
            type="string",
            description="Token to provide to the processor",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid account or unsupported processor",
            recovery_hint="Verify account_id and check processor is supported",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["plaid.accounts.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

PLAID_TRANSFERS_SCHEMAS: dict[str, CapabilitySchema] = {
    "plaid.transfer.create": PLAID_TRANSFER_CREATE,
    "plaid.transfer.get": PLAID_TRANSFER_GET,
    "plaid.processor.token.create": PLAID_PROCESSOR_TOKEN_CREATE,
}

__all__ = ["PLAID_TRANSFERS_SCHEMAS"]
