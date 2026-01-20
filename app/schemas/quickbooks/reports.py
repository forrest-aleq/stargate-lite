"""
QuickBooks Report Capability Schemas.

Rich metadata for financial reports: P&L, Balance Sheet, Cash Flow, Aging, etc.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ CORE FINANCIAL REPORTS ============

PROFIT_LOSS_REPORT = CapabilitySchema(
    capability_key="report.profitloss",
    service="quickbooks",
    category="reports",
    description="Get P&L report from QuickBooks",
    description_detailed=(
        "Generates a Profit & Loss (Income Statement) report showing revenue, expenses, "
        "and net income for a specified period. Can be filtered by class or location."
    ),
    parameters={
        "start_date": ParameterSchema(
            type="string",
            required=False,
            description="Report start date (YYYY-MM-DD)",
            example="2026-01-01",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="Report end date (YYYY-MM-DD)",
            example="2026-01-31",
        ),
        "class_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter by class ID",
        ),
        "location": ParameterSchema(
            type="string",
            required=False,
            description="Filter by location/department",
        ),
    },
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="Full P&L report with rows, columns, and summary",
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
        related_capabilities=[
            "report.profitloss.detail",
            "report.balancesheet",
            "report.cashflow",
        ],
    ),
    idempotent=True,
    has_side_effects=False,
)

BALANCE_SHEET = CapabilitySchema(
    capability_key="report.balancesheet",
    service="quickbooks",
    category="reports",
    description="Get Balance Sheet report from QuickBooks",
    description_detailed=(
        "Generates a Balance Sheet showing assets, liabilities, and equity as of a "
        "specific date. Provides a snapshot of financial position."
    ),
    parameters={
        "as_of_date": ParameterSchema(
            type="string",
            required=False,
            description="Report as-of date (YYYY-MM-DD, defaults to today)",
            example="2026-01-31",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="Alias for as_of_date",
        ),
    },
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="Balance sheet with assets, liabilities, equity sections",
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
        related_capabilities=["report.profitloss", "report.cashflow"],
    ),
    idempotent=True,
    has_side_effects=False,
)

PROFIT_LOSS_DETAIL = CapabilitySchema(
    capability_key="report.profitloss.detail",
    service="quickbooks",
    category="reports",
    description="Get detailed P&L report with individual transactions",
    description_detailed=(
        "Generates a detailed Profit & Loss report showing individual transactions "
        "that make up each account balance. More granular than standard P&L."
    ),
    parameters={
        "start_date": ParameterSchema(
            type="string",
            required=False,
            description="Report start date",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="Report end date",
        ),
    },
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="Detailed P&L with transaction-level detail",
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
        related_capabilities=["report.profitloss", "report.generalledger"],
    ),
    idempotent=True,
    has_side_effects=False,
)

CASHFLOW_REPORT = CapabilitySchema(
    capability_key="report.cashflow",
    service="quickbooks",
    category="reports",
    description="Get Cash Flow Statement report from QuickBooks",
    description_detailed=(
        "Generates a Cash Flow Statement showing cash from operating, investing, "
        "and financing activities. Shows how cash position changed over period."
    ),
    parameters={
        "start_date": ParameterSchema(
            type="string",
            required=False,
            description="Report start date",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="Report end date",
        ),
    },
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="Cash flow statement with operating/investing/financing sections",
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
        related_capabilities=["report.profitloss", "report.balancesheet"],
    ),
    idempotent=True,
    has_side_effects=False,
)

GENERAL_LEDGER = CapabilitySchema(
    capability_key="report.generalledger",
    service="quickbooks",
    category="reports",
    description="Get General Ledger report",
    description_detailed=(
        "Generates a General Ledger report showing all transactions by account. "
        "The most detailed transaction report available."
    ),
    parameters={
        "start_date": ParameterSchema(
            type="string",
            required=False,
            description="Report start date",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="Report end date",
        ),
    },
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="General ledger with all account transactions",
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
        related_capabilities=["transaction.list", "report.profitloss.detail"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ AGING REPORTS ============

AR_AGING = CapabilitySchema(
    capability_key="report.ar_aging",
    service="quickbooks",
    category="reports",
    description="Get AR Aging Summary report",
    description_detailed=(
        "Generates an Accounts Receivable Aging Summary showing customer balances "
        "grouped by aging buckets (Current, 1-30, 31-60, 61-90, 90+ days)."
    ),
    parameters={},
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="AR aging summary by customer and bucket",
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
        typically_followed_by=["qb.invoice.list_outstanding"],
        related_capabilities=["report.ar_aging_detail", "qb.customer.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

AP_AGING = CapabilitySchema(
    capability_key="report.ap_aging",
    service="quickbooks",
    category="reports",
    description="Get AP Aging Summary report",
    description_detailed=(
        "Generates an Accounts Payable Aging Summary showing vendor balances "
        "grouped by aging buckets. Helps prioritize vendor payments."
    ),
    parameters={},
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="AP aging summary by vendor and bucket",
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
        typically_followed_by=["bill.list"],
        related_capabilities=["report.ap_aging_detail", "vendor.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

AR_AGING_DETAIL = CapabilitySchema(
    capability_key="report.ar_aging_detail",
    service="quickbooks",
    category="reports",
    description="Get detailed AR Aging with individual invoices",
    description_detailed=(
        "Generates a detailed Accounts Receivable Aging report showing each "
        "individual invoice and its age. More granular than summary."
    ),
    parameters={},
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="Detailed AR aging with invoice-level detail",
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
        related_capabilities=["report.ar_aging", "qb.invoice.list_outstanding"],
    ),
    idempotent=True,
    has_side_effects=False,
)

AP_AGING_DETAIL = CapabilitySchema(
    capability_key="report.ap_aging_detail",
    service="quickbooks",
    category="reports",
    description="Get detailed AP Aging with individual bills",
    description_detailed=(
        "Generates a detailed Accounts Payable Aging report showing each "
        "individual bill and its age. Useful for payment prioritization."
    ),
    parameters={},
    returns={
        "report": ReturnFieldSchema(
            type="object",
            description="Detailed AP aging with bill-level detail",
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
        related_capabilities=["report.ap_aging", "bill.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

REPORT_SCHEMAS: dict[str, CapabilitySchema] = {
    "report.profitloss": PROFIT_LOSS_REPORT,
    "report.balancesheet": BALANCE_SHEET,
    "report.profitloss.detail": PROFIT_LOSS_DETAIL,
    "report.cashflow": CASHFLOW_REPORT,
    "report.generalledger": GENERAL_LEDGER,
    "report.ar_aging": AR_AGING,
    "report.ap_aging": AP_AGING,
    "report.ar_aging_detail": AR_AGING_DETAIL,
    "report.ap_aging_detail": AP_AGING_DETAIL,
}
