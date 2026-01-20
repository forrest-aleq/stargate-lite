"""Sage Intacct General Ledger Schemas."""

from app.schemas.base import CapabilitySchema, ParameterSchema, ReturnFieldSchema, WorkflowHints

SAGE_ACCOUNTS_LIST = CapabilitySchema(
    capability_key="sage_intacct.accounts.list",
    service="sage_intacct",
    category="general_ledger",
    description="List chart of accounts from Sage Intacct",
    description_detailed="Lists GL accounts with optional filtering by type and status.",
    parameters={
        "account_type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by account type",
            enum=["asset", "liability", "equity", "revenue", "expense"],
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["active", "inactive"],
        ),
        "page_size": ParameterSchema(
            type="integer",
            required=False,
            description="Results per page (default 100)",
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(type="array", description="List of GL accounts"),
        "count": ReturnFieldSchema(type="integer", description="Number of accounts"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["sage_intacct.journals.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

SAGE_ACCOUNTS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.accounts.create",
    service="sage_intacct",
    category="general_ledger",
    description="Create a new GL account in Sage Intacct",
    parameters={
        "account_no": ParameterSchema(type="string", required=True, description="Account number"),
        "title": ParameterSchema(type="string", required=True, description="Account title"),
        "account_type": ParameterSchema(
            type="string",
            required=True,
            description="Account type",
            enum=["asset", "liability", "equity", "revenue", "expense"],
        ),
        "normal_balance": ParameterSchema(
            type="string",
            required=False,
            description="Normal balance (default: based on type)",
            enum=["debit", "credit"],
        ),
    },
    returns={
        "account": ReturnFieldSchema(type="object", description="Created account"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    idempotent=False,
    has_side_effects=True,
)

SAGE_JOURNALS_LIST = CapabilitySchema(
    capability_key="sage_intacct.journals.list",
    service="sage_intacct",
    category="general_ledger",
    description="List journal entries from Sage Intacct",
    parameters={
        "date_from": ParameterSchema(
            type="string", required=False, description="Start date (YYYY-MM-DD)"
        ),
        "date_to": ParameterSchema(
            type="string", required=False, description="End date (YYYY-MM-DD)"
        ),
        "state": ParameterSchema(
            type="string",
            required=False,
            description="Filter by state",
            enum=["draft", "posted"],
        ),
        "page_size": ParameterSchema(type="integer", required=False, description="Results per page"),
    },
    returns={
        "journals": ReturnFieldSchema(type="array", description="Journal entries"),
        "count": ReturnFieldSchema(type="integer", description="Number of entries"),
    },
    idempotent=True,
    has_side_effects=False,
)

SAGE_JOURNALS_CREATE = CapabilitySchema(
    capability_key="sage_intacct.journals.create",
    service="sage_intacct",
    category="general_ledger",
    description="Create a journal entry in Sage Intacct",
    description_detailed=(
        "Creates a journal entry with debit and credit lines. "
        "Total debits must equal total credits."
    ),
    parameters={
        "journal_date": ParameterSchema(
            type="string", required=True, description="Journal date (YYYY-MM-DD)"
        ),
        "description": ParameterSchema(type="string", required=False, description="Journal description"),
        "lines": ParameterSchema(
            type="array",
            required=True,
            description="Journal lines with account_no, amount, memo, debit/credit",
        ),
        "reference_number": ParameterSchema(type="string", required=False, description="External reference"),
    },
    returns={
        "journal_entry": ReturnFieldSchema(type="object", description="Created journal"),
        "status": ReturnFieldSchema(type="string", description="Should be 'success'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sage_intacct.accounts.list"],
        typically_followed_by=["sage_intacct.journals.post"],
    ),
    idempotent=False,
    has_side_effects=True,
)

SAGE_JOURNALS_POST = CapabilitySchema(
    capability_key="sage_intacct.journals.post",
    service="sage_intacct",
    category="general_ledger",
    description="Post a draft journal entry in Sage Intacct",
    parameters={
        "journal_key": ParameterSchema(type="string", required=True, description="Journal key to post"),
    },
    returns={
        "journal_key": ReturnFieldSchema(type="string", description="Posted journal key"),
        "status": ReturnFieldSchema(type="string", description="Should be 'posted'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["sage_intacct.journals.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

GL_SCHEMAS = {
    "sage_intacct.accounts.list": SAGE_ACCOUNTS_LIST,
    "sage_intacct.accounts.create": SAGE_ACCOUNTS_CREATE,
    "sage_intacct.journals.list": SAGE_JOURNALS_LIST,
    "sage_intacct.journals.create": SAGE_JOURNALS_CREATE,
    "sage_intacct.journals.post": SAGE_JOURNALS_POST,
}
