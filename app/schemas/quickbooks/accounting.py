"""
QuickBooks Accounting Capability Schemas.

Rich metadata for journal entries, chart of accounts, and account queries.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    UsageExample,
    WorkflowHints,
)

# ============ JOURNAL ENTRY ============

JOURNAL_CREATE = CapabilitySchema(
    capability_key="journal.create",
    service="quickbooks",
    category="accounting",
    description="Create a journal entry in QuickBooks",
    description_detailed=(
        "Creates a manual journal entry with debit and credit lines. Journal entries must "
        "balance (total debits = total credits). Use for adjustments, corrections, or "
        "transactions not captured by other transaction types."
    ),
    parameters={
        "lines": ParameterSchema(
            type="array",
            required=True,
            description="Journal lines with PostingType, Amount, and AccountRef",
            items_type="object",
            example=[
                {
                    "DetailType": "JournalEntryLineDetail",
                    "Amount": 1000.00,
                    "JournalEntryLineDetail": {
                        "PostingType": "Debit",
                        "AccountRef": {"value": "1"},
                    },
                },
                {
                    "DetailType": "JournalEntryLineDetail",
                    "Amount": 1000.00,
                    "JournalEntryLineDetail": {
                        "PostingType": "Credit",
                        "AccountRef": {"value": "2"},
                    },
                },
            ],
        ),
        "txn_date": ParameterSchema(
            type="string",
            required=False,
            description="Journal entry date (YYYY-MM-DD)",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Private memo/description",
        ),
        "doc_number": ParameterSchema(
            type="string",
            required=False,
            description="Reference number",
        ),
    },
    returns={
        "journal_entry_id": ReturnFieldSchema(type="string", description="Journal entry ID"),
        "doc_number": ReturnFieldSchema(type="string", description="Reference number"),
        "txn_date": ReturnFieldSchema(type="string", description="Entry date"),
        "total_amount": ReturnFieldSchema(type="number", description="Total amount"),
        "memo": ReturnFieldSchema(type="string", description="Memo"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this journal entry in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/journal?txnId=100",
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
            description="Journal entry doesn't balance or invalid account",
            recovery_hint="Ensure debits = credits and verify account IDs",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["chartofaccounts.get", "account.list"],
        related_capabilities=["report.generalledger", "transaction.list"],
    ),
    examples=[
        UsageExample(
            description="Create adjusting entry for accrued expenses",
            args={
                "lines": [
                    {
                        "DetailType": "JournalEntryLineDetail",
                        "Amount": 500,
                        "JournalEntryLineDetail": {
                            "PostingType": "Debit",
                            "AccountRef": {"value": "66"},
                            "Description": "Accrued utilities expense",
                        },
                    },
                    {
                        "DetailType": "JournalEntryLineDetail",
                        "Amount": 500,
                        "JournalEntryLineDetail": {
                            "PostingType": "Credit",
                            "AccountRef": {"value": "92"},
                            "Description": "Accrued liabilities",
                        },
                    },
                ],
                "memo": "Month-end accrual for utilities",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

# ============ QUERY ============

QB_QUERY = CapabilitySchema(
    capability_key="qb.query",
    service="quickbooks",
    category="accounting",
    description="Query QuickBooks entities using SQL-like syntax",
    description_detailed=(
        "Execute SQL-like queries against QuickBooks entities. Supports SELECT with "
        "WHERE, ORDERBY, STARTPOSITION, and MAXRESULTS. Useful for complex queries "
        "not covered by other endpoints."
    ),
    parameters={
        "query": ParameterSchema(
            type="string",
            required=True,
            description="SQL-like query string",
            example="SELECT * FROM Invoice WHERE Balance > 0 MAXRESULTS 50",
        ),
    },
    returns={
        "results": ReturnFieldSchema(
            type="object",
            description="QueryResponse object with entity data",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid query syntax",
            recovery_hint="Check QuickBooks query language documentation",
        ),
    ],
    workflow=WorkflowHints(
        related_capabilities=["qb.invoice.list", "vendor.list", "qb.customer.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ CHART OF ACCOUNTS ============

CHART_OF_ACCOUNTS_GET = CapabilitySchema(
    capability_key="chartofaccounts.get",
    service="quickbooks",
    category="accounting",
    description="Get chart of accounts from QuickBooks",
    description_detailed=(
        "Retrieves the full chart of accounts with optional filtering by account type. "
        "Use to get account IDs needed for journal entries, bills, and other transactions."
    ),
    parameters={
        "account_type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by account type",
            enum=[
                "Bank",
                "AccountsReceivable",
                "AccountsPayable",
                "CreditCard",
                "Income",
                "Expense",
                "OtherCurrentAsset",
                "FixedAsset",
                "OtherAsset",
                "OtherCurrentLiability",
                "LongTermLiability",
                "Equity",
            ],
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description="List of account objects (each includes deep_link URL to QBO)",
            items_type="object",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of accounts"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["journal.create", "bill.create", "deposit.create"],
        related_capabilities=["account.get", "account.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

ACCOUNT_LIST = CapabilitySchema(
    capability_key="account.list",
    service="quickbooks",
    category="accounting",
    description="List all accounts (chart of accounts)",
    description_detailed="Alias for chartofaccounts.get - retrieves all accounts.",
    parameters=CHART_OF_ACCOUNTS_GET.parameters,
    returns=CHART_OF_ACCOUNTS_GET.returns,
    errors=CHART_OF_ACCOUNTS_GET.errors,
    workflow=CHART_OF_ACCOUNTS_GET.workflow,
    idempotent=True,
    has_side_effects=False,
)

ACCOUNT_GET = CapabilitySchema(
    capability_key="account.get",
    service="quickbooks",
    category="accounting",
    description="Get single account details with balance",
    description_detailed=(
        "Retrieves detailed information about a specific account including current balance."
    ),
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Account ID with 'qb:' prefix",
            example="qb:35",
        ),
    },
    returns={
        "account_id": ReturnFieldSchema(type="string", description="Account ID"),
        "name": ReturnFieldSchema(type="string", description="Account name"),
        "type": ReturnFieldSchema(type="string", description="Account type"),
        "sub_type": ReturnFieldSchema(type="string", description="Account sub-type"),
        "number": ReturnFieldSchema(type="string", description="Account number"),
        "balance": ReturnFieldSchema(type="number", description="Current balance"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this account register in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/register?accountId=35",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Account not found",
            recovery_hint="Verify account_id with account.list",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

ACCOUNTING_SCHEMAS: dict[str, CapabilitySchema] = {
    "journal.create": JOURNAL_CREATE,
    "qb.query": QB_QUERY,
    "chartofaccounts.get": CHART_OF_ACCOUNTS_GET,
    "account.list": ACCOUNT_LIST,
    "account.get": ACCOUNT_GET,
}
