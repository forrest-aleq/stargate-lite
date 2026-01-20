"""
Financial Operations Capability Registry

Bank reconciliation, fuzzy matching, covenants, waterfalls, tiered fees, forecasting.
"""

import threading
from collections.abc import Callable
from typing import Any

from app.utilities.financial_ops import get_financial_ops_utility

# Thread-safe lazy initialization
_utilities_lock = threading.Lock()
_financial_ops_utility = None


def _lazy_financial_ops(
    method_name: str,
) -> Callable[[str, str, dict[str, Any]], dict[str, Any]]:
    """Create lazy handler for financial ops utility methods."""

    def handler(org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        global _financial_ops_utility
        if _financial_ops_utility is None:
            with _utilities_lock:
                if _financial_ops_utility is None:
                    _financial_ops_utility = get_financial_ops_utility()
        result: dict[str, Any] = getattr(_financial_ops_utility, method_name)(org_id, user_id, args)
        return result

    return handler


FINANCIAL_OPS_CAPABILITIES = {
    # ========== BANK RECONCILIATION ==========
    "calc.reconcile": {
        "handler": _lazy_financial_ops("reconcile_transactions"),
        "tool_name": "financial_ops.reconcile_transactions",
        "description": (
            "Reconcile GL transactions against bank transactions - "
            "identifies matches, timing items, and variances"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== FUZZY MATCHING ==========
    "match.fuzzy": {
        "handler": _lazy_financial_ops("fuzzy_match_entity"),
        "tool_name": "financial_ops.fuzzy_match_entity",
        "description": (
            "Fuzzy match entity names (customers/vendors) with confidence scoring - "
            "handles LLC/Inc variations and DBA names"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    "match.transactions": {
        "handler": _lazy_financial_ops("match_transactions_by_entity"),
        "tool_name": "financial_ops.match_transactions_by_entity",
        "description": (
            "Match transactions to entities using fuzzy name matching - "
            "useful for lockbox payment processing"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== COVENANT CALCULATIONS ==========
    "calc.covenant.dscr": {
        "handler": _lazy_financial_ops("calculate_dscr"),
        "tool_name": "financial_ops.calculate_dscr",
        "description": (
            "Calculate Debt Service Coverage Ratio (DSCR) with compliance check - "
            "NOI / Debt Service"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.covenant.ltv": {
        "handler": _lazy_financial_ops("calculate_ltv"),
        "tool_name": "financial_ops.calculate_ltv",
        "description": (
            "Calculate Loan-to-Value Ratio (LTV) with compliance check - "
            "Loan Balance / Property Value"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.covenant.check": {
        "handler": _lazy_financial_ops("check_covenant_compliance"),
        "tool_name": "financial_ops.check_covenant_compliance",
        "description": (
            "Check compliance against custom covenant threshold - "
            "supports various comparison operators"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.covenant.summary": {
        "handler": _lazy_financial_ops("covenant_summary"),
        "tool_name": "financial_ops.covenant_summary",
        "description": (
            "Generate summary of multiple covenant checks - "
            "identifies all violations and compliance rate"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== WATERFALL DISTRIBUTION ==========
    "calc.waterfall": {
        "handler": _lazy_financial_ops("calculate_waterfall"),
        "tool_name": "financial_ops.calculate_waterfall",
        "description": (
            "Calculate investor distribution waterfall - "
            "return of capital, preferred return, GP catch-up, carried interest"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== TIERED FEES ==========
    "calc.tiered_fee": {
        "handler": _lazy_financial_ops("calculate_tiered_fee"),
        "tool_name": "financial_ops.calculate_tiered_fee",
        "description": (
            "Calculate management fee using tiered AUM structure - "
            "supports multiple tiers, proration, minimum fees"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.client_fees": {
        "handler": _lazy_financial_ops("calculate_client_fees"),
        "tool_name": "financial_ops.calculate_client_fees",
        "description": (
            "Calculate fees for multiple clients with proration - "
            "batch fee calculation for client portfolios"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== CASH FLOW FORECASTING ==========
    "forecast.cashflow": {
        "handler": _lazy_financial_ops("forecast_cashflow"),
        "tool_name": "financial_ops.forecast_cashflow",
        "description": (
            "Generate 13-week rolling cash flow forecast - "
            "includes seasonal adjustment and confidence intervals"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== BANK AGGREGATION ==========
    "bank.aggregate": {
        "handler": _lazy_financial_ops("aggregate_bank_balances"),
        "tool_name": "financial_ops.aggregate_bank_balances",
        "description": (
            "Aggregate balances across multiple bank accounts - "
            "treasury management for multi-account portfolios"
        ),
        "requires_oauth": False,
        "service": "financial_ops",
        "credential_type": None,
        "supports_delegation": False,
    },
}
