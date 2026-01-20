"""
NetSuite Journal Entry Capability Schemas.

Reference: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_159886587653.html
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ JOURNAL ENTRY CREATE ============

NETSUITE_JOURNAL_CREATE = CapabilitySchema(
    capability_key="netsuite.journal.create",
    service="netsuite",
    category="accounting",
    description="Create a journal entry in NetSuite",
    description_detailed=(
        "Creates a journal entry in NetSuite's general ledger. "
        "CRITICAL: Total debits must equal total credits or the entry will be rejected. "
        "Each line requires an account ID and either a debit or credit amount. "
        "Uses REST API with TBA or OAuth 2.0 authentication."
    ),
    parameters={
        "subsidiary_id": ParameterSchema(
            type="string",
            required=True,
            description="Internal ID of the subsidiary (OneWorld only)",
            example="1",
        ),
        "lines": ParameterSchema(
            type="array",
            required=True,
            description="Journal entry lines (each with account_id and debit OR credit)",
            items_type="object",
            example=[
                {"account_id": "58", "debit": 3200.00, "memo": "Cash deposit"},
                {"account_id": "4", "credit": 3200.00, "memo": "AR clearing"},
            ],
        ),
        "tran_date": ParameterSchema(
            type="string",
            required=False,
            description="Transaction date (YYYY-MM-DD). Defaults to today.",
            example="2025-10-15",
        ),
        "memo": ParameterSchema(
            type="string",
            required=False,
            description="Header memo for the journal entry",
        ),
        "doc_number": ParameterSchema(
            type="string",
            required=False,
            description="Custom document number (tranId)",
        ),
    },
    returns={
        "journal_entry_id": ReturnFieldSchema(
            type="string",
            description="NetSuite internal ID prefixed with 'ns:'",
            example="ns:12345",
        ),
        "tran_id": ReturnFieldSchema(
            type="string",
            description="Transaction number assigned by NetSuite",
        ),
        "tran_date": ReturnFieldSchema(
            type="string",
            description="Transaction date",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Journal entry status",
            example="posted",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Debits and credits do not balance",
            recovery_hint="Ensure total debits equal total credits before submitting",
        ),
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="NetSuite credentials not configured",
            recovery_hint="User must complete TBA or OAuth 2.0 authentication",
        ),
        ErrorHint(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            description="INVALID_KEY_OR_REF - Invalid account or subsidiary ID",
            recovery_hint="Verify account IDs exist using netsuite.account.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.account.list", "netsuite.subsidiary.list"],
        typically_followed_by=["netsuite.journal.get", "netsuite.gl.transactions"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ JOURNAL ENTRY GET ============

NETSUITE_JOURNAL_GET = CapabilitySchema(
    capability_key="netsuite.journal.get",
    service="netsuite",
    category="accounting",
    description="Get a journal entry by ID",
    description_detailed=(
        "Retrieves a journal entry from NetSuite by its internal ID. "
        "Returns full details including all line items with account information, "
        "debits, credits, and any segment values (department, class, location)."
    ),
    parameters={
        "journal_entry_id": ParameterSchema(
            type="string",
            required=True,
            description="NetSuite internal ID (with or without 'ns:' prefix)",
            example="ns:12345",
        ),
    },
    returns={
        "journal_entry_id": ReturnFieldSchema(
            type="string",
            description="NetSuite internal ID prefixed with 'ns:'",
        ),
        "tran_id": ReturnFieldSchema(
            type="string",
            description="Transaction number",
        ),
        "tran_date": ReturnFieldSchema(
            type="string",
            description="Transaction date",
        ),
        "memo": ReturnFieldSchema(
            type="string",
            description="Header memo",
        ),
        "subsidiary_id": ReturnFieldSchema(
            type="string",
            description="Subsidiary internal ID",
        ),
        "lines": ReturnFieldSchema(
            type="array",
            description="Line items with account, debit/credit amounts",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Approval/posting status",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Journal entry not found",
            recovery_hint="Verify the journal_entry_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.journal.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

NETSUITE_JOURNAL_SCHEMAS: dict[str, CapabilitySchema] = {
    "netsuite.journal.create": NETSUITE_JOURNAL_CREATE,
    "netsuite.journal.get": NETSUITE_JOURNAL_GET,
}

__all__ = ["NETSUITE_JOURNAL_SCHEMAS"]
