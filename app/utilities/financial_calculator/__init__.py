"""
Financial Calculator utility for Stargate Lite.

Provides financial calculations without external API dependencies.
Uses numpy for numerical computations.

Capability keys:
- calc.npv: Net Present Value calculation
- calc.irr: Internal Rate of Return
- calc.amortization: Loan amortization schedule
- calc.depreciation: Asset depreciation schedules
- calc.compound_interest: Compound interest calculations
- calc.payback_period: Investment payback period
"""

from .compound import CompoundMixin


class FinancialCalculatorUtility(CompoundMixin):
    """
    Financial calculations utility.

    Inherits from CompoundMixin which inherits from DepreciationMixin
    which inherits from AmortizationMixin which inherits from NpvIrrMixin
    which inherits from FinancialCalculatorBase.

    No external API required - pure Python calculations.
    Uses decimal for precision in monetary calculations.
    """

    pass


# Singleton instance for registry
_financial_calculator_utility: FinancialCalculatorUtility | None = None


def get_financial_calculator_utility() -> FinancialCalculatorUtility:
    """Get or create singleton FinancialCalculatorUtility instance."""
    global _financial_calculator_utility
    if _financial_calculator_utility is None:
        _financial_calculator_utility = FinancialCalculatorUtility()
    return _financial_calculator_utility


__all__ = ["FinancialCalculatorUtility", "get_financial_calculator_utility"]
