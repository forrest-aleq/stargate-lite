"""
Base class for Financial Operations utility.

Financial operations for accounting workflows including:
- Bank reconciliation
- Fuzzy matching for vendors/customers
- Covenant calculations
- Investor waterfall distributions
- Tiered fee calculations
- Cash flow forecasting
"""

from typing import ClassVar

from app.utilities.base import BaseUtility


class FinancialOpsBase(BaseUtility):
    """
    Financial operations utility base class.

    No external API required - pure Python calculations.
    Uses decimal for precision in monetary calculations.
    """

    SERVICE_NAME: ClassVar[str] = "financial_ops"
    REQUIRED_ENV_VARS: ClassVar[list[str]] = []  # No external API needed

    def _initialize_client(self) -> None:
        """No client needed - pure Python calculations."""
        pass
