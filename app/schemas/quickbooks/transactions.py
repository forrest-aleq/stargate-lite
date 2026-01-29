"""
QuickBooks Transaction Capability Schemas.

Rich metadata for purchase orders, expenses, deposits, transfers, and transactions.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ PURCHASE ORDER & EXPENSE ============

PURCHASE_ORDER_CREATE = CapabilitySchema(
    capability_key="purchaseorder.create",
    service="quickbooks",
    category="accounting",
    description="Create a purchase order in QuickBooks",
    description_detailed=(
        "Creates a purchase order for a vendor. Purchase orders are used to order goods "
        "before receiving them and can be converted to bills upon receipt."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor ID",
            example="qb:123",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Items being ordered",
            items_type="object",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Order date",
        ),
        "ship_address": ParameterSchema(
            type="object",
            required=False,
            description="Shipping address",
        ),
    },
    returns={
        "purchase_order_id": ReturnFieldSchema(type="string", description="PO ID"),
        "doc_number": ReturnFieldSchema(type="string", description="PO number"),
        "total_amount": ReturnFieldSchema(type="number", description="Total"),
        "vendor_id": ReturnFieldSchema(type="string", description="Vendor"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this purchase order in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/purchaseorder?txnId=100",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["vendor.search", "item.list"],
        typically_followed_by=["bill.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

EXPENSE_CREATE = CapabilitySchema(
    capability_key="expense.create",
    service="quickbooks",
    category="accounting",
    description="Create an expense in QuickBooks",
    description_detailed=(
        "Creates a purchase/expense transaction. Unlike bills, expenses are paid immediately "
        "(cash, credit card, etc.) rather than on account."
    ),
    parameters={
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Expense line items",
        ),
        "payment_type": ParameterSchema(
            type="string",
            required=False,
            description="Payment type used",
            default="Cash",
            enum=["Cash", "Check", "CreditCard"],
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Expense date",
        ),
        "vendor_id": ParameterSchema(
            type="string",
            required=False,
            description="Vendor (optional)",
        ),
        "account_ref": ParameterSchema(
            type="string",
            required=False,
            description="Payment account ID",
        ),
    },
    returns={
        "expense_id": ReturnFieldSchema(type="string", description="Expense ID"),
        "total_amount": ReturnFieldSchema(type="number", description="Total"),
        "payment_type": ReturnFieldSchema(type="string", description="Payment type"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this expense in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/expense?txnId=200",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["chartofaccounts.get", "vendor.search"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ DEPOSIT & TRANSFER ============

DEPOSIT_CREATE = CapabilitySchema(
    capability_key="deposit.create",
    service="quickbooks",
    category="accounting",
    description="Create a bank deposit",
    description_detailed=(
        "Creates a deposit to record money received into a bank account. Can include "
        "multiple line items from different sources."
    ),
    parameters={
        "deposit_account_id": ParameterSchema(
            type="string",
            required=True,
            description="Bank account ID to deposit into",
        ),
        "line_items": ParameterSchema(
            type="array",
            required=True,
            description="Deposit line items with amounts and sources",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Deposit date",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Private note",
        ),
    },
    returns={
        "deposit_id": ReturnFieldSchema(type="string", description="Deposit ID"),
        "total_amount": ReturnFieldSchema(type="number", description="Total deposited"),
        "txn_date": ReturnFieldSchema(type="string", description="Date"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this deposit in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/deposit?txnId=300",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["account.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

TRANSFER_CREATE = CapabilitySchema(
    capability_key="qb.transfer.create",
    service="quickbooks",
    category="accounting",
    description="Create account-to-account transfer",
    description_detailed=(
        "Creates a transfer between two accounts (typically bank accounts). "
        "Records money moving from one account to another."
    ),
    parameters={
        "from_account_id": ParameterSchema(
            type="string",
            required=True,
            description="Source account ID",
        ),
        "to_account_id": ParameterSchema(
            type="string",
            required=True,
            description="Destination account ID",
        ),
        "amount": ParameterSchema(
            type="number",
            required=True,
            description="Transfer amount",
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Transfer date",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Private note",
        ),
    },
    returns={
        "transfer_id": ReturnFieldSchema(type="string", description="Transfer ID"),
        "amount": ReturnFieldSchema(type="number", description="Amount transferred"),
        "from_account": ReturnFieldSchema(type="string", description="Source account name"),
        "to_account": ReturnFieldSchema(type="string", description="Destination account name"),
        "txn_date": ReturnFieldSchema(type="string", description="Date"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this transfer in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/transfer?txnId=400",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid account IDs or insufficient funds",
            recovery_hint="Verify account IDs with account.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["account.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

TRANSACTION_LIST = CapabilitySchema(
    capability_key="transaction.list",
    service="quickbooks",
    category="accounting",
    description="List GL transactions for reconciliation",
    description_detailed=(
        "Returns a transaction list report showing all transactions within a date range. "
        "Useful for reconciliation and audit purposes."
    ),
    parameters={
        "start_date": ParameterSchema(
            type="string",
            required=False,
            description="Start date (YYYY-MM-DD)",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="End date (YYYY-MM-DD)",
        ),
    },
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="Transaction list report data",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        related_capabilities=["report.generalledger"],
    ),
    idempotent=True,
    has_side_effects=False,
)

TRANSACTION_SCHEMAS: dict[str, CapabilitySchema] = {
    "purchaseorder.create": PURCHASE_ORDER_CREATE,
    "expense.create": EXPENSE_CREATE,
    "deposit.create": DEPOSIT_CREATE,
    "qb.transfer.create": TRANSFER_CREATE,
    "transaction.list": TRANSACTION_LIST,
}
