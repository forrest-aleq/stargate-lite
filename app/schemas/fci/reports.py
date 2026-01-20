"""
FCI Report Schemas.

These are direct mappings to accounting report capabilities,
wrapped in the FCI interface for frontend consistency.

All reports are Layer 1 (direct) - pure data pulls with no AI reasoning.
"""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# =============================================================================
# Profit & Loss Report
# =============================================================================
FCI_PROFITLOSS = CapabilitySchema(
    capability_key="fci.report.profitloss",
    service="fci",
    category="reports",
    description="Get Profit & Loss report",
    description_detailed="""
    Pulls P&L report from connected accounting system.
    Returns income, expenses, and net income with optional detail levels.
    Underlying: report.profitloss (QuickBooks), xero.report.profit_loss, etc.
    """,
    parameters={
        "start_date": ParameterSchema(
            type="string",
            required=False,
            description="Start date (YYYY-MM-DD), defaults to first of month",
        ),
        "end_date": ParameterSchema(
            type="string",
            required=False,
            description="End date (YYYY-MM-DD), defaults to today",
        ),
        "summarize_by": ParameterSchema(
            type="string",
            required=False,
            description="Summarization level",
            enum=["total", "month", "quarter", "year"],
            default="total",
        ),
        "class_id": ParameterSchema(
            type="string",
            required=False,
            description="Filter by class/department (for multi-entity)",
        ),
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Accounting system (auto-detected if not specified)",
            enum=["quickbooks", "xero", "netsuite", "sage_intacct"],
        ),
    },
    returns={
        "total_income": ReturnFieldSchema(type="number", description="Total revenue"),
        "total_expenses": ReturnFieldSchema(type="number", description="Total expenses"),
        "net_income": ReturnFieldSchema(type="number", description="Net income (profit/loss)"),
        "gross_profit": ReturnFieldSchema(
            type="number", description="Gross profit if COGS tracked"
        ),
        "income_breakdown": ReturnFieldSchema(
            type="array",
            description="Income by category: {category, amount}",
        ),
        "expense_breakdown": ReturnFieldSchema(
            type="array",
            description="Expenses by category: {category, amount}",
        ),
        "period": ReturnFieldSchema(type="object", description="Report period: {start, end}"),
    },
    workflow=WorkflowHints(
        related_capabilities=["fci.revenue", "fci.expenses", "fci.burn"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# Balance Sheet Report
# =============================================================================
FCI_BALANCESHEET = CapabilitySchema(
    capability_key="fci.report.balancesheet",
    service="fci",
    category="reports",
    description="Get Balance Sheet report",
    description_detailed="""
    Pulls Balance Sheet from connected accounting system.
    Returns assets, liabilities, and equity totals with breakdowns.
    Underlying: report.balancesheet (QuickBooks), xero.report.balance_sheet, etc.
    """,
    parameters={
        "as_of_date": ParameterSchema(
            type="string",
            required=False,
            description="Report as-of date (YYYY-MM-DD), defaults to today",
        ),
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Accounting system (auto-detected if not specified)",
            enum=["quickbooks", "xero", "netsuite", "sage_intacct"],
        ),
    },
    returns={
        "total_assets": ReturnFieldSchema(type="number", description="Total assets"),
        "total_liabilities": ReturnFieldSchema(type="number", description="Total liabilities"),
        "total_equity": ReturnFieldSchema(type="number", description="Total equity"),
        "current_assets": ReturnFieldSchema(type="number", description="Current assets"),
        "fixed_assets": ReturnFieldSchema(type="number", description="Fixed/long-term assets"),
        "current_liabilities": ReturnFieldSchema(type="number", description="Current liabilities"),
        "long_term_liabilities": ReturnFieldSchema(
            type="number", description="Long-term liabilities"
        ),
        "asset_breakdown": ReturnFieldSchema(
            type="array",
            description="Assets by account: {account, balance}",
        ),
        "liability_breakdown": ReturnFieldSchema(
            type="array",
            description="Liabilities by account: {account, balance}",
        ),
        "as_of": ReturnFieldSchema(type="string", description="Report date"),
    },
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# AR Aging Report
# =============================================================================
FCI_AR_AGING = CapabilitySchema(
    capability_key="fci.report.ar_aging",
    service="fci",
    category="reports",
    description="Get detailed AR Aging report",
    description_detailed="""
    Pulls detailed AR Aging from connected accounting system.
    Returns customer-level aging with invoice details.
    More detailed than fci.ar primitive - includes per-customer breakdown.
    Underlying: report.ar_aging (QuickBooks), xero.ar.aging, etc.
    """,
    parameters={
        "as_of_date": ParameterSchema(
            type="string",
            required=False,
            description="Report as-of date (YYYY-MM-DD), defaults to today",
        ),
        "aging_periods": ParameterSchema(
            type="string",
            required=False,
            description="Aging bucket configuration",
            enum=["standard", "weekly", "custom"],
            default="standard",
        ),
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Accounting system (auto-detected if not specified)",
            enum=["quickbooks", "xero", "netsuite", "sage_intacct"],
        ),
    },
    returns={
        "total": ReturnFieldSchema(type="number", description="Total AR"),
        "current": ReturnFieldSchema(type="number", description="Current (not due)"),
        "days_1_30": ReturnFieldSchema(type="number", description="1-30 days"),
        "days_31_60": ReturnFieldSchema(type="number", description="31-60 days"),
        "days_61_90": ReturnFieldSchema(type="number", description="61-90 days"),
        "days_over_90": ReturnFieldSchema(type="number", description="Over 90 days"),
        "customers": ReturnFieldSchema(
            type="array",
            description="Per-customer aging: {name, total, current, 30, 60, 90, over_90, invoices}",
        ),
        "as_of": ReturnFieldSchema(type="string", description="Report date"),
    },
    workflow=WorkflowHints(
        related_capabilities=["fci.ar", "fci.customer.lookup"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# AP Aging Report
# =============================================================================
FCI_AP_AGING = CapabilitySchema(
    capability_key="fci.report.ap_aging",
    service="fci",
    category="reports",
    description="Get detailed AP Aging report",
    description_detailed="""
    Pulls detailed AP Aging from connected accounting system.
    Returns vendor-level aging with bill details.
    More detailed than fci.ap primitive - includes per-vendor breakdown.
    Underlying: report.ap_aging (QuickBooks), xero.ap.aging, etc.
    """,
    parameters={
        "as_of_date": ParameterSchema(
            type="string",
            required=False,
            description="Report as-of date (YYYY-MM-DD), defaults to today",
        ),
        "aging_periods": ParameterSchema(
            type="string",
            required=False,
            description="Aging bucket configuration",
            enum=["standard", "weekly", "custom"],
            default="standard",
        ),
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Accounting system (auto-detected if not specified)",
            enum=["quickbooks", "xero", "netsuite", "sage_intacct", "billcom"],
        ),
    },
    returns={
        "total": ReturnFieldSchema(type="number", description="Total AP"),
        "current": ReturnFieldSchema(type="number", description="Current (not due)"),
        "days_1_30": ReturnFieldSchema(type="number", description="1-30 days"),
        "days_31_60": ReturnFieldSchema(type="number", description="31-60 days"),
        "days_61_90": ReturnFieldSchema(type="number", description="61-90 days"),
        "days_over_90": ReturnFieldSchema(type="number", description="Over 90 days"),
        "vendors": ReturnFieldSchema(
            type="array",
            description="Per-vendor aging: {name, total, current, 30, 60, 90, over_90, bills}",
        ),
        "as_of": ReturnFieldSchema(type="string", description="Report date"),
    },
    workflow=WorkflowHints(
        related_capabilities=["fci.ap", "fci.vendor.lookup"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# Cash Flow Report
# =============================================================================
FCI_CASHFLOW = CapabilitySchema(
    capability_key="fci.report.cashflow",
    service="fci",
    category="reports",
    description="Get Cash Flow statement",
    description_detailed="""
    Pulls Cash Flow statement from connected accounting system.
    Returns operating, investing, and financing activities.
    Underlying: report.cashflow (QuickBooks), sage_intacct.reports.cash_flow, etc.
    """,
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
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Accounting system (auto-detected if not specified)",
            enum=["quickbooks", "xero", "netsuite", "sage_intacct"],
        ),
    },
    returns={
        "operating_activities": ReturnFieldSchema(
            type="number",
            description="Net cash from operating activities",
        ),
        "investing_activities": ReturnFieldSchema(
            type="number",
            description="Net cash from investing activities",
        ),
        "financing_activities": ReturnFieldSchema(
            type="number",
            description="Net cash from financing activities",
        ),
        "net_change": ReturnFieldSchema(
            type="number",
            description="Net change in cash",
        ),
        "beginning_cash": ReturnFieldSchema(type="number", description="Starting cash balance"),
        "ending_cash": ReturnFieldSchema(type="number", description="Ending cash balance"),
        "details": ReturnFieldSchema(
            type="object",
            description="Detailed breakdown by category",
        ),
        "period": ReturnFieldSchema(type="object", description="Report period: {start, end}"),
    },
    workflow=WorkflowHints(
        related_capabilities=["fci.cash", "fci.burn"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# Registry of all FCI report schemas
# =============================================================================
FCI_REPORT_SCHEMAS = {
    "fci.report.profitloss": FCI_PROFITLOSS,
    "fci.report.balancesheet": FCI_BALANCESHEET,
    "fci.report.ar_aging": FCI_AR_AGING,
    "fci.report.ap_aging": FCI_AP_AGING,
    "fci.report.cashflow": FCI_CASHFLOW,
}
