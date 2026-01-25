"""Sage Intacct Cash Management Schemas."""

from app.schemas.base import CapabilitySchema, ParameterSchema, ReturnFieldSchema, WorkflowHints

SAGE_BANK_ACCOUNTS_LIST = CapabilitySchema(
    capability_key="sage_intacct.bank_accounts.list",
    service="sage_intacct",
    category="cash_management",
    description="List bank accounts from Sage Intacct",
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["active", "inactive"],
        ),
    },
    returns={
        "bank_accounts": ReturnFieldSchema(type="array", description="Bank accounts"),
        "count": ReturnFieldSchema(type="integer", description="Account count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=[
            "sage_intacct.bank_accounts.balance",
            "sage_intacct.bill_payments.create",
        ],
    ),
    idempotent=True,
    has_side_effects=False,
)

SAGE_BANK_BALANCE = CapabilitySchema(
    capability_key="sage_intacct.bank_accounts.balance",
    service="sage_intacct",
    category="cash_management",
    description="Get bank account balance from Sage Intacct",
    parameters={
        "bank_account_id": ParameterSchema(
            type="string", required=True, description="Bank account ID to check"
        ),
        "as_of_date": ParameterSchema(
            type="string", required=False, description="Balance as of date (YYYY-MM-DD)"
        ),
    },
    returns={
        "bank_account_id": ReturnFieldSchema(type="string", description="Account ID"),
        "gl_balance": ReturnFieldSchema(type="number", description="GL balance"),
        "bank_balance": ReturnFieldSchema(type="number", description="Bank balance"),
        "uncleared_amount": ReturnFieldSchema(type="number", description="Uncleared"),
    },
    idempotent=True,
    has_side_effects=False,
)

SAGE_DEPOSITS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.deposits.create",
    service="sage_intacct",
    category="cash_management",
    description="Create a bank deposit in Sage Intacct",
    parameters={
        "bank_account_id": ParameterSchema(
            type="string", required=True, description="Bank account ID for deposit"
        ),
        "deposit_date": ParameterSchema(
            type="string", required=True, description="Deposit date (YYYY-MM-DD)"
        ),
        "entries": ParameterSchema(
            type="array",
            required=True,
            description="Deposit entries with gl_account and amount",
        ),
        "description": ParameterSchema(
            type="string", required=False, description="Deposit description or memo"
        ),
    },
    returns={
        "deposit": ReturnFieldSchema(type="object", description="Created deposit"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    idempotent=False,
    has_side_effects=True,
)

SAGE_TRANSFERS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.transfers.create",
    service="sage_intacct",
    category="cash_management",
    description="Create a bank transfer in Sage Intacct",
    parameters={
        "from_account_id": ParameterSchema(
            type="string", required=True, description="Source bank account ID"
        ),
        "to_account_id": ParameterSchema(
            type="string", required=True, description="Destination bank account ID"
        ),
        "transfer_date": ParameterSchema(
            type="string", required=True, description="Transfer date (YYYY-MM-DD)"
        ),
        "amount": ParameterSchema(type="number", required=True, description="Transfer amount"),
        "description": ParameterSchema(
            type="string", required=False, description="Transfer description or memo"
        ),
    },
    returns={
        "transfer": ReturnFieldSchema(type="object", description="Created transfer"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    idempotent=False,
    has_side_effects=True,
)

CASH_SCHEMAS = {
    "sage_intacct.bank_accounts.list": SAGE_BANK_ACCOUNTS_LIST,
    "sage_intacct.bank_accounts.balance": SAGE_BANK_BALANCE,
    "sage_intacct.deposits.create": SAGE_DEPOSITS_CREATE,
    "sage_intacct.transfers.create": SAGE_TRANSFERS_CREATE,
}
