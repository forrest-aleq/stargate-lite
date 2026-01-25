"""Sage Intacct Reports Schemas."""

from app.schemas.base import CapabilitySchema, ParameterSchema, ReturnFieldSchema

SAGE_TRIAL_BALANCE = CapabilitySchema(
    capability_key="sage_intacct.reports.trial_balance",
    service="sage_intacct",
    category="reports",
    description="Get trial balance report from Sage Intacct",
    parameters={
        "as_of_date": ParameterSchema(
            type="string", required=False, description="Report as-of date (YYYY-MM-DD)"
        ),
        "reporting_period": ParameterSchema(
            type="string", required=False, description="Reporting period key"
        ),
    },
    returns={
        "accounts": ReturnFieldSchema(
            type="array", description="Accounts with debit/credit balances"
        ),
        "total_debits": ReturnFieldSchema(type="number", description="Total debits"),
        "total_credits": ReturnFieldSchema(type="number", description="Total credits"),
    },
    idempotent=True,
    has_side_effects=False,
)

SAGE_AP_AGING = CapabilitySchema(
    capability_key="sage_intacct.reports.ap_aging",
    service="sage_intacct",
    category="reports",
    description="Get AP aging report from Sage Intacct",
    parameters={
        "as_of_date": ParameterSchema(
            type="string", required=False, description="Report as-of date (YYYY-MM-DD)"
        ),
        "vendor_id": ParameterSchema(
            type="string", required=False, description="Filter by vendor ID"
        ),
    },
    returns={
        "aging": ReturnFieldSchema(
            type="object",
            description="Aging buckets (current, 1-30, 31-60, 61-90, over 90)",
        ),
        "total": ReturnFieldSchema(type="number", description="Total AP balance"),
    },
    idempotent=True,
    has_side_effects=False,
)

SAGE_AR_AGING = CapabilitySchema(
    capability_key="sage_intacct.reports.ar_aging",
    service="sage_intacct",
    category="reports",
    description="Get AR aging report from Sage Intacct",
    parameters={
        "as_of_date": ParameterSchema(
            type="string", required=False, description="Report as-of date (YYYY-MM-DD)"
        ),
        "customer_id": ParameterSchema(
            type="string", required=False, description="Filter by customer ID"
        ),
    },
    returns={
        "aging": ReturnFieldSchema(
            type="object",
            description="Aging buckets (current, 1-30, 31-60, 61-90, over 90)",
        ),
        "total": ReturnFieldSchema(type="number", description="Total AR balance"),
    },
    idempotent=True,
    has_side_effects=False,
)

SAGE_CASH_FLOW = CapabilitySchema(
    capability_key="sage_intacct.reports.cash_flow",
    service="sage_intacct",
    category="reports",
    description="Get cash flow statement from Sage Intacct",
    parameters={
        "start_date": ParameterSchema(
            type="string", required=True, description="Period start date (YYYY-MM-DD)"
        ),
        "end_date": ParameterSchema(
            type="string", required=True, description="Period end date (YYYY-MM-DD)"
        ),
    },
    returns={
        "operating": ReturnFieldSchema(type="object", description="Operating activities"),
        "investing": ReturnFieldSchema(type="object", description="Investing activities"),
        "financing": ReturnFieldSchema(type="object", description="Financing activities"),
        "net_change": ReturnFieldSchema(type="number", description="Net cash change"),
    },
    idempotent=True,
    has_side_effects=False,
)

REPORT_SCHEMAS = {
    "sage_intacct.reports.trial_balance": SAGE_TRIAL_BALANCE,
    "sage_intacct.reports.ap_aging": SAGE_AP_AGING,
    "sage_intacct.reports.ar_aging": SAGE_AR_AGING,
    "sage_intacct.reports.cash_flow": SAGE_CASH_FLOW,
}
