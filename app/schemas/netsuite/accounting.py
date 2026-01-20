"""
NetSuite Accounting Capability Schemas.

Chart of accounts, subsidiaries, GL transactions, and reconciliation.
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

NETSUITE_ACCOUNT_LIST = CapabilitySchema(
    capability_key="netsuite.account.list",
    service="netsuite",
    category="accounting",
    description="Get chart of accounts",
    description_detailed=(
        "Retrieves the chart of accounts from NetSuite using SuiteQL. "
        "Returns account numbers, names, types, and balances. "
        "Use to look up account IDs for journal entries and bills."
    ),
    parameters={
        "account_type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by account type (Bank, Expense, Income, etc.)",
            example="Bank",
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array",
            description="List of accounts with id, number, name, type, balance",
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of accounts returned",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="NetSuite credentials not configured",
            recovery_hint="Complete authentication setup",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["netsuite.journal.create", "netsuite.vendorbill.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ SUBSIDIARY LIST ============

NETSUITE_SUBSIDIARY_LIST = CapabilitySchema(
    capability_key="netsuite.subsidiary.list",
    service="netsuite",
    category="accounting",
    description="Get list of subsidiaries",
    description_detailed=(
        "Retrieves the list of subsidiaries from a NetSuite OneWorld account. "
        "Subsidiary IDs are required for journal entries and transactions. "
        "Non-OneWorld accounts have a single implicit subsidiary."
    ),
    parameters={},
    returns={
        "subsidiaries": ReturnFieldSchema(
            type="array",
            description="List of subsidiaries with id, name, country",
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of subsidiaries",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="NetSuite credentials not configured",
            recovery_hint="Complete authentication setup",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["netsuite.journal.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ GL TRANSACTIONS ============

NETSUITE_GL_TRANSACTIONS = CapabilitySchema(
    capability_key="netsuite.gl.transactions",
    service="netsuite",
    category="accounting",
    description="Get GL transactions for reconciliation",
    description_detailed=(
        "Retrieves general ledger transaction lines from NetSuite using SuiteQL. "
        "Essential for bank reconciliation workflows - matches bank statement "
        "lines to GL entries. Filter by account and date range."
    ),
    parameters={
        "account_ids": ParameterSchema(
            type="array",
            required=False,
            description="Account internal IDs to filter (omit for all accounts)",
            items_type="string",
        ),
        "from_date": ParameterSchema(
            type="string",
            required=True,
            description="Start date (YYYY-MM-DD)",
            example="2025-10-01",
        ),
        "to_date": ParameterSchema(
            type="string",
            required=True,
            description="End date (YYYY-MM-DD)",
            example="2025-10-31",
        ),
        "subsidiary_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter by subsidiary (OneWorld only)",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max results (default 1000)",
            default=1000,
        ),
    },
    returns={
        "transactions": ReturnFieldSchema(
            type="array",
            description="GL transaction lines with account, debit/credit, memo",
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of transactions returned",
        ),
        "has_more": ReturnFieldSchema(
            type="boolean",
            description="Whether more results exist",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid date range or account IDs",
            recovery_hint="Use YYYY-MM-DD format and verify account IDs",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.account.list"],
        typically_followed_by=["netsuite.reconcile.bank"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ BANK RECONCILIATION ============

NETSUITE_RECONCILE_BANK = CapabilitySchema(
    capability_key="netsuite.reconcile.bank",
    service="netsuite",
    category="accounting",
    description="Reconcile bank statement",
    description_detailed=(
        "Compares bank statement balance against NetSuite GL balance "
        "for a specific account and date. Returns variance information. "
        "Note: Actual reconciliation is typically done in NetSuite UI."
    ),
    parameters={
        "account_id": ParameterSchema(
            type="string",
            required=True,
            description="Bank account internal ID",
        ),
        "statement_date": ParameterSchema(
            type="string",
            required=True,
            description="Statement date (YYYY-MM-DD)",
        ),
        "ending_balance": ParameterSchema(
            type="number",
            required=True,
            description="Bank statement ending balance",
        ),
    },
    returns={
        "account_id": ReturnFieldSchema(
            type="string",
            description="Account ID",
        ),
        "statement_date": ReturnFieldSchema(
            type="string",
            description="Statement date",
        ),
        "statement_balance": ReturnFieldSchema(
            type="number",
            description="Bank statement balance",
        ),
        "gl_balance": ReturnFieldSchema(
            type="number",
            description="NetSuite GL balance",
        ),
        "variance": ReturnFieldSchema(
            type="number",
            description="Difference between statement and GL",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="'balanced' or 'variance_exists'",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid account_id or date",
            recovery_hint="Verify account exists using netsuite.account.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.gl.transactions"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ SUITEQL QUERY ============

NETSUITE_QUERY = CapabilitySchema(
    capability_key="netsuite.query",
    service="netsuite",
    category="data",
    description="Execute SuiteQL query",
    description_detailed=(
        "Executes a SuiteQL query against NetSuite. "
        "SuiteQL is NetSuite's SQL-like query language. "
        "Max 100,000 total results, 1,000 per page. "
        "Use for custom data retrieval not covered by other capabilities."
    ),
    parameters={
        "query": ParameterSchema(
            type="string",
            required=True,
            description="SuiteQL query string",
            example="SELECT id, companyname FROM vendor WHERE isinactive = 'F'",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max results per page (max 1000)",
            default=1000,
        ),
        "offset": ParameterSchema(
            type="integer",
            required=False,
            description="Pagination offset",
            default=0,
        ),
    },
    returns={
        "items": ReturnFieldSchema(
            type="array",
            description="Query result rows",
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of rows returned",
        ),
        "has_more": ReturnFieldSchema(
            type="boolean",
            description="Whether more results exist",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid SuiteQL syntax",
            recovery_hint="Check query syntax and table/column names",
        ),
        ErrorHint(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            description="Query execution error",
            recovery_hint="Verify table and column names exist in NetSuite",
        ),
    ],
    workflow=WorkflowHints(),
    idempotent=True,
    has_side_effects=False,
)

# ============ CUSTOM RECORD CREATE ============

NETSUITE_CUSTOMRECORD_CREATE = CapabilitySchema(
    capability_key="netsuite.customrecord.create",
    service="netsuite",
    category="data",
    description="Create a custom record",
    description_detailed=(
        "Creates a custom record in NetSuite. "
        "Custom records are user-defined record types created in NetSuite. "
        "Record type ID format: customrecord_XXX"
    ),
    parameters={
        "record_type": ParameterSchema(
            type="string",
            required=True,
            description="Custom record type ID (e.g., customrecord_myrecord)",
        ),
        "fields": ParameterSchema(
            type="object",
            required=False,
            description="Field values for the custom record",
            default={},
        ),
    },
    returns={
        "record_id": ReturnFieldSchema(
            type="string",
            description="Created record ID prefixed with 'ns:'",
        ),
        "record_type": ReturnFieldSchema(
            type="string",
            description="Record type ID",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Creation status ('created')",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid record_type or field values",
            recovery_hint="Verify record type exists and fields are valid",
        ),
    ],
    workflow=WorkflowHints(),
    idempotent=False,
    has_side_effects=True,
)

NETSUITE_ACCOUNTING_SCHEMAS: dict[str, CapabilitySchema] = {
    "netsuite.account.list": NETSUITE_ACCOUNT_LIST,
    "netsuite.subsidiary.list": NETSUITE_SUBSIDIARY_LIST,
    "netsuite.gl.transactions": NETSUITE_GL_TRANSACTIONS,
    "netsuite.reconcile.bank": NETSUITE_RECONCILE_BANK,
    "netsuite.query": NETSUITE_QUERY,
    "netsuite.customrecord.create": NETSUITE_CUSTOMRECORD_CREATE,
}

__all__ = ["NETSUITE_ACCOUNTING_SCHEMAS"]
