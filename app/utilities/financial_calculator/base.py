"""
Base class for Financial Calculator utility.
"""

from typing import ClassVar

from app.utilities.base import BaseUtility


class FinancialCalculatorBase(BaseUtility):
    """
    Financial calculations utility base class.

    No external API required - pure Python calculations.
    Uses decimal for precision in monetary calculations.
    """

    SERVICE_NAME: ClassVar[str] = "financial_calculator"
    REQUIRED_ENV_VARS: ClassVar[list[str]] = []  # No external API needed

    def _initialize_client(self) -> None:
        """No client needed - pure Python calculations."""
        pass
