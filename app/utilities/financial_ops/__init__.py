"""
Financial Operations utility for Stargate Lite.

Provides financial operations for accounting workflows:
- Bank reconciliation (matching GL vs bank transactions)
- Fuzzy entity matching (customer/vendor name matching)
- Covenant calculations (DSCR, LTV, compliance)
- Investor waterfall distributions
- Tiered AUM fee calculations
- Cash flow forecasting

Capability keys:
- calc.reconcile: Bank reconciliation engine
- match.fuzzy: Fuzzy entity matching
- match.transactions: Match transactions to entities
- calc.covenant.dscr: Debt Service Coverage Ratio
- calc.covenant.ltv: Loan-to-Value ratio
- calc.covenant.check: Custom covenant compliance check
- calc.covenant.summary: Multi-covenant summary
- calc.waterfall: Investor distribution waterfall
- calc.tiered_fee: Tiered AUM fee calculation
- calc.client_fees: Multi-client fee calculation
- forecast.cashflow: 13-week cash flow forecast
- bank.aggregate: Multi-bank balance aggregation
"""

import threading

from .forecasting import ForecastingMixin


class FinancialOpsUtility(ForecastingMixin):
    """
    Financial operations utility.

    Inherits from ForecastingMixin which inherits from TieredFeesMixin
    which inherits from WaterfallMixin which inherits from CovenantsMixin
    which inherits from MatchingMixin which inherits from ReconciliationMixin
    which inherits from FinancialOpsBase.

    No external API required - pure Python calculations.
    Uses decimal for precision in monetary calculations.
    """

    pass


# Thread-safe singleton instance for registry
_financial_ops_lock = threading.Lock()
_financial_ops_utility: FinancialOpsUtility | None = None


def get_financial_ops_utility() -> FinancialOpsUtility:
    """Get or create singleton FinancialOpsUtility instance."""
    global _financial_ops_utility
    if _financial_ops_utility is None:
        with _financial_ops_lock:
            if _financial_ops_utility is None:
                _financial_ops_utility = FinancialOpsUtility()
    return _financial_ops_utility


__all__ = ["FinancialOpsUtility", "get_financial_ops_utility"]
