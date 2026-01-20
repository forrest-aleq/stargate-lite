"""
FCI Data Primitive Schemas.

These are the core FCI primitives that map to financial metrics:
- @cash: Total cash across all connected bank accounts
- @ar: Accounts receivable totals and aging buckets
- @ap: Accounts payable totals and aging buckets
- @burn: Monthly burn rate from P&L expenses
- @runway: Cash / Burn = months of runway
- @revenue: Revenue totals from P&L
- @expenses: Expense totals from P&L
- @payroll: Payroll summary from Gusto

These can be called DIRECTLY by the frontend without Baby Mars orchestration
because they're pure data aggregations with no AI reasoning required.
"""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# =============================================================================
# @cash - Aggregate cash position across all banks
# =============================================================================
FCI_CASH = CapabilitySchema(
    capability_key="fci.cash",
    service="fci",
    category="primitives",
    description="Get total cash position across all connected bank accounts",
    description_detailed="""
    Aggregates balances from all connected banking sources:
    - Plaid-linked accounts
    - Mercury
    - Brex
    - Chase
    - Ramp

    Returns total cash, breakdown by account, and trend data.
    Maps to FCI primitive: @cash
    """,
    parameters={
        "include_pending": ParameterSchema(
            type="boolean",
            required=False,
            description="Include pending transactions in balance",
            default=False,
        ),
        "currency": ParameterSchema(
            type="string",
            required=False,
            description="Currency for aggregation (default: USD)",
            default="USD",
        ),
    },
    returns={
        "total": ReturnFieldSchema(
            type="number",
            description="Total cash balance across all accounts",
            example=1247000.00,
        ),
        "currency": ReturnFieldSchema(type="string", description="Currency code"),
        "accounts": ReturnFieldSchema(
            type="array",
            description="Breakdown by account: {name, bank, balance, type}",
        ),
        "as_of": ReturnFieldSchema(type="string", description="Timestamp of balances"),
    },
    workflow=WorkflowHints(
        related_capabilities=["fci.burn", "fci.runway"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @ar - Accounts Receivable totals and aging
# =============================================================================
FCI_AR = CapabilitySchema(
    capability_key="fci.ar",
    service="fci",
    category="primitives",
    description="Get accounts receivable totals with aging buckets",
    description_detailed="""
    Pulls AR aging data from accounting system (QuickBooks, Xero, NetSuite, Sage).
    Returns total outstanding AR plus aging buckets (current, 30, 60, 90, 90+).
    Maps to FCI primitive: @ar
    """,
    parameters={
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Accounting system to query (auto-detected if not specified)",
            enum=["quickbooks", "xero", "netsuite", "sage_intacct"],
        ),
        "as_of_date": ParameterSchema(
            type="string",
            required=False,
            description="Report as-of date (YYYY-MM-DD), defaults to today",
        ),
    },
    returns={
        "total": ReturnFieldSchema(
            type="number",
            description="Total outstanding AR",
            example=342000.00,
        ),
        "current": ReturnFieldSchema(type="number", description="Current (not yet due)"),
        "days_30": ReturnFieldSchema(type="number", description="1-30 days past due"),
        "days_60": ReturnFieldSchema(type="number", description="31-60 days past due"),
        "days_90": ReturnFieldSchema(type="number", description="61-90 days past due"),
        "over_90": ReturnFieldSchema(type="number", description="Over 90 days past due"),
        "count": ReturnFieldSchema(type="integer", description="Number of open invoices"),
        "as_of": ReturnFieldSchema(type="string", description="Report date"),
    },
    workflow=WorkflowHints(
        related_capabilities=["fci.cash", "fci.revenue"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @ap - Accounts Payable totals and aging
# =============================================================================
FCI_AP = CapabilitySchema(
    capability_key="fci.ap",
    service="fci",
    category="primitives",
    description="Get accounts payable totals with aging buckets",
    description_detailed="""
    Pulls AP aging data from accounting system (QuickBooks, Xero, NetSuite, Sage)
    and Bill.com if connected. Returns total outstanding AP plus aging buckets.
    Maps to FCI primitive: @ap
    """,
    parameters={
        "source": ParameterSchema(
            type="string",
            required=False,
            description="Accounting system to query (auto-detected if not specified)",
            enum=["quickbooks", "xero", "netsuite", "sage_intacct", "billcom"],
        ),
        "as_of_date": ParameterSchema(
            type="string",
            required=False,
            description="Report as-of date (YYYY-MM-DD), defaults to today",
        ),
    },
    returns={
        "total": ReturnFieldSchema(
            type="number",
            description="Total outstanding AP",
            example=156000.00,
        ),
        "current": ReturnFieldSchema(type="number", description="Current (not yet due)"),
        "days_30": ReturnFieldSchema(type="number", description="1-30 days past due"),
        "days_60": ReturnFieldSchema(type="number", description="31-60 days past due"),
        "days_90": ReturnFieldSchema(type="number", description="61-90 days past due"),
        "over_90": ReturnFieldSchema(type="number", description="Over 90 days past due"),
        "count": ReturnFieldSchema(type="integer", description="Number of open bills"),
        "as_of": ReturnFieldSchema(type="string", description="Report date"),
    },
    workflow=WorkflowHints(
        related_capabilities=["fci.cash", "fci.expenses"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @burn - Monthly burn rate
# =============================================================================
FCI_BURN = CapabilitySchema(
    capability_key="fci.burn",
    service="fci",
    category="primitives",
    description="Get monthly burn rate from P&L expenses",
    description_detailed="""
    Calculates burn rate from P&L expense data over the last 3-6 months.
    Returns monthly average, last month's burn, and trend direction.
    Maps to FCI primitive: @burn
    """,
    parameters={
        "months": ParameterSchema(
            type="integer",
            required=False,
            description="Number of months to average (default: 3)",
            default=3,
        ),
        "exclude_categories": ParameterSchema(
            type="array",
            required=False,
            description="Expense categories to exclude (e.g., one-time costs)",
        ),
    },
    returns={
        "monthly_avg": ReturnFieldSchema(
            type="number",
            description="Average monthly burn",
            example=87500.00,
        ),
        "last_month": ReturnFieldSchema(type="number", description="Last month's burn"),
        "trend": ReturnFieldSchema(
            type="string",
            description="Trend direction: increasing, decreasing, stable",
        ),
        "trend_pct": ReturnFieldSchema(
            type="number",
            description="Month-over-month change percentage",
        ),
        "by_category": ReturnFieldSchema(
            type="array",
            description="Burn breakdown by expense category",
        ),
    },
    workflow=WorkflowHints(
        typically_followed_by=["fci.runway"],
        related_capabilities=["fci.cash", "fci.expenses"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @runway - Cash / Burn = months of runway
# =============================================================================
FCI_RUNWAY = CapabilitySchema(
    capability_key="fci.runway",
    service="fci",
    category="primitives",
    description="Calculate runway in months (cash / burn)",
    description_detailed="""
    Divides current cash position by monthly burn rate to get runway.
    Also projects cash-out date assuming linear burn.
    Maps to FCI primitive: @runway
    """,
    parameters={
        "burn_months": ParameterSchema(
            type="integer",
            required=False,
            description="Months to average for burn calculation (default: 3)",
            default=3,
        ),
    },
    returns={
        "months": ReturnFieldSchema(
            type="number",
            description="Runway in months",
            example=14.2,
        ),
        "cash": ReturnFieldSchema(type="number", description="Current cash position"),
        "burn": ReturnFieldSchema(type="number", description="Monthly burn used"),
        "cash_out_date": ReturnFieldSchema(
            type="string",
            description="Projected cash-out date (YYYY-MM)",
        ),
        "confidence": ReturnFieldSchema(
            type="string",
            description="Confidence level: high, medium, low",
        ),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["fci.cash", "fci.burn"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @revenue - Revenue totals from P&L
# =============================================================================
FCI_REVENUE = CapabilitySchema(
    capability_key="fci.revenue",
    service="fci",
    category="primitives",
    description="Get revenue totals from P&L income section",
    description_detailed="""
    Extracts revenue data from P&L report. Returns MTD, YTD, and last month
    with trend information. For subscription businesses, includes MRR if
    Stripe/Recurly data is available.
    Maps to FCI primitive: @revenue
    """,
    parameters={
        "period": ParameterSchema(
            type="string",
            required=False,
            description="Period to report: mtd, ytd, last_month, trailing_12m",
            default="mtd",
            enum=["mtd", "ytd", "last_month", "trailing_12m"],
        ),
    },
    returns={
        "total": ReturnFieldSchema(
            type="number",
            description="Revenue for the period",
            example=425000.00,
        ),
        "mtd": ReturnFieldSchema(type="number", description="Month-to-date revenue"),
        "ytd": ReturnFieldSchema(type="number", description="Year-to-date revenue"),
        "last_month": ReturnFieldSchema(type="number", description="Last month revenue"),
        "trend": ReturnFieldSchema(
            type="string",
            description="Trend: increasing, decreasing, stable",
        ),
        "mrr": ReturnFieldSchema(
            type="number",
            description="Monthly recurring revenue (if subscription business)",
        ),
        "by_category": ReturnFieldSchema(
            type="array",
            description="Revenue breakdown by category/product",
        ),
    },
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @expenses - Expense totals from P&L
# =============================================================================
FCI_EXPENSES = CapabilitySchema(
    capability_key="fci.expenses",
    service="fci",
    category="primitives",
    description="Get expense totals from P&L expense section",
    description_detailed="""
    Extracts expense data from P&L report. Returns MTD, YTD, and last month
    with breakdown by category.
    Maps to FCI primitive: @expenses
    """,
    parameters={
        "period": ParameterSchema(
            type="string",
            required=False,
            description="Period to report: mtd, ytd, last_month, trailing_12m",
            default="mtd",
            enum=["mtd", "ytd", "last_month", "trailing_12m"],
        ),
        "by_category": ParameterSchema(
            type="boolean",
            required=False,
            description="Include category breakdown",
            default=True,
        ),
    },
    returns={
        "total": ReturnFieldSchema(
            type="number",
            description="Total expenses for the period",
            example=312000.00,
        ),
        "mtd": ReturnFieldSchema(type="number", description="Month-to-date expenses"),
        "ytd": ReturnFieldSchema(type="number", description="Year-to-date expenses"),
        "last_month": ReturnFieldSchema(type="number", description="Last month expenses"),
        "trend": ReturnFieldSchema(
            type="string",
            description="Trend: increasing, decreasing, stable",
        ),
        "by_category": ReturnFieldSchema(
            type="array",
            description="Expense breakdown by category",
        ),
    },
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @payroll - Payroll summary from Gusto
# =============================================================================
FCI_PAYROLL = CapabilitySchema(
    capability_key="fci.payroll",
    service="fci",
    category="primitives",
    description="Get payroll summary from Gusto",
    description_detailed="""
    Pulls payroll data from Gusto. Returns last payroll run details,
    monthly total, headcount, and next run date.
    Maps to FCI primitive: @payroll
    """,
    parameters={
        "company_id": ParameterSchema(
            type="string",
            required=False,
            description="Gusto company ID (auto-detected if only one)",
        ),
    },
    returns={
        "last_run": ReturnFieldSchema(
            type="object",
            description="Last payroll: {date, gross, net, taxes}",
        ),
        "next_run": ReturnFieldSchema(
            type="string",
            description="Next scheduled payroll date",
        ),
        "monthly_total": ReturnFieldSchema(
            type="number",
            description="Monthly payroll total (employer cost)",
            example=156000.00,
        ),
        "headcount": ReturnFieldSchema(
            type="integer",
            description="Number of employees on payroll",
        ),
        "contractor_count": ReturnFieldSchema(
            type="integer",
            description="Number of active contractors",
        ),
    },
    workflow=WorkflowHints(
        related_capabilities=["fci.burn", "fci.expenses"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# Registry of all FCI primitive schemas
# =============================================================================
FCI_PRIMITIVE_SCHEMAS = {
    "fci.cash": FCI_CASH,
    "fci.ar": FCI_AR,
    "fci.ap": FCI_AP,
    "fci.burn": FCI_BURN,
    "fci.runway": FCI_RUNWAY,
    "fci.revenue": FCI_REVENUE,
    "fci.expenses": FCI_EXPENSES,
    "fci.payroll": FCI_PAYROLL,
}
