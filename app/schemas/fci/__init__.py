"""
FCI (Financial Command Interface) Schemas.

This module defines schemas for FCI primitives that can be called directly
by the frontend, bypassing Baby Mars orchestration for pure data pulls.

Architecture:
- Layer 1 (Direct): Pure reads - frontend calls Stargate directly
- Layer 2 (Orchestrated): Logic required - frontend → Baby Mars → Stargate

Layer 1 capabilities are deterministic and don't need AI reasoning:
- @cash: Aggregate bank balances
- @ar: AR aging totals
- @ap: AP aging totals
- @revenue: P&L revenue section
- @expenses: P&L expense section
- @payroll: Gusto payroll summary

Layer 2 capabilities require orchestration:
- Bank reconciliation (matching logic)
- Three-way match (PO + Receipt + Invoice)
- Covenant calculations (DSCR, LTV)
- Waterfall distributions
- Fuzzy entity matching
"""

from app.schemas.fci.entities import (
    FCI_CUSTOMER_LOOKUP,
    FCI_ENTITY_SCHEMAS,
    FCI_INVOICE_LOOKUP,
    FCI_VENDOR_LOOKUP,
)
from app.schemas.fci.primitives import (
    FCI_AP,
    FCI_AR,
    FCI_BURN,
    FCI_CASH,
    FCI_EXPENSES,
    FCI_PAYROLL,
    FCI_PRIMITIVE_SCHEMAS,
    FCI_REVENUE,
    FCI_RUNWAY,
)
from app.schemas.fci.reports import (
    FCI_AP_AGING,
    FCI_AR_AGING,
    FCI_BALANCESHEET,
    FCI_CASHFLOW,
    FCI_PROFITLOSS,
    FCI_REPORT_SCHEMAS,
)

# All FCI schemas combined
FCI_SCHEMAS = {
    **FCI_PRIMITIVE_SCHEMAS,
    **FCI_ENTITY_SCHEMAS,
    **FCI_REPORT_SCHEMAS,
}

__all__ = [
    "FCI_AP",
    "FCI_AP_AGING",
    "FCI_AR",
    "FCI_AR_AGING",
    "FCI_BALANCESHEET",
    "FCI_BURN",
    "FCI_CASH",
    "FCI_CASHFLOW",
    "FCI_CUSTOMER_LOOKUP",
    "FCI_ENTITY_SCHEMAS",
    "FCI_EXPENSES",
    "FCI_INVOICE_LOOKUP",
    "FCI_PAYROLL",
    "FCI_PRIMITIVE_SCHEMAS",
    "FCI_PROFITLOSS",
    "FCI_REPORT_SCHEMAS",
    "FCI_REVENUE",
    "FCI_RUNWAY",
    "FCI_SCHEMAS",
    "FCI_VENDOR_LOOKUP",
]
