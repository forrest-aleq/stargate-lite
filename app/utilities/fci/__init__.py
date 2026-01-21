"""
FCI (Financial Command Interface) Utilities Package.

This package provides the aggregation layer that transforms raw connector data
into unified financial primitives. The FCI layer sits between the frontend and
the connectors, providing:

1. **Service Discovery**: Automatically detects which connectors are available
2. **Data Aggregation**: Combines data from multiple sources (e.g., cash from Plaid + Mercury)
3. **Unified Response Format**: Consistent shape for frontend consumption
4. **Change Tracking**: Calculates period-over-period changes
5. **Trend Data**: Provides sparkline data for visualization
6. **Insights**: Auto-generates basic insight strings

Primitives:
- fci.cash: Total cash across all banks
- fci.ar: Accounts receivable with aging
- fci.ap: Accounts payable with aging
- fci.revenue: Revenue from P&L + payment systems
- fci.expenses: Expenses from P&L
- fci.burn: Monthly burn rate (derived)
- fci.runway: Months of runway (derived)
- fci.payroll: Payroll summary from Gusto

Reports:
- fci.report.profitloss: P&L report
- fci.report.balancesheet: Balance sheet
- fci.report.ar_aging: Detailed AR aging
- fci.report.ap_aging: Detailed AP aging
- fci.report.cashflow: Cash flow statement

Entity Lookups:
- fci.customer.lookup: Cross-service customer search
- fci.vendor.lookup: Cross-service vendor search
- fci.invoice.lookup: Cross-service invoice search

Usage:
    from app.utilities.fci import get_fci_utility

    fci = get_fci_utility()
    cash = fci.get_cash(org_id, user_id, {})
    ar = fci.get_ar(org_id, user_id, {"as_of_date": "2026-01-15"})
"""

from app.utilities.fci.ap import APMixin
from app.utilities.fci.ar import ARMixin
from app.utilities.fci.base import FCIBase
from app.utilities.fci.burn import BurnMixin
from app.utilities.fci.cash import CashMixin
from app.utilities.fci.entities import EntityMixin
from app.utilities.fci.expenses import ExpensesMixin
from app.utilities.fci.payroll import PayrollMixin
from app.utilities.fci.reports import ReportsMixin
from app.utilities.fci.revenue import RevenueMixin
from app.utilities.fci.runway import RunwayMixin


class FCIUtility(
    # Entity lookups (highest precedence for method resolution)
    EntityMixin,
    # Reports
    ReportsMixin,
    # Derived primitives
    RunwayMixin,
    BurnMixin,
    # Core primitives
    PayrollMixin,
    ExpensesMixin,
    RevenueMixin,
    APMixin,
    ARMixin,
    CashMixin,
    # Base class (provides _aggregate_from_services, _format_response, etc.)
    FCIBase,
):
    """
    FCI Utility - Financial Command Interface aggregation layer.

    Combines all FCI mixins to provide a unified interface for financial
    data aggregation across connected services.

    This class uses multiple inheritance with mixins in a specific order.
    Each mixin provides methods for a specific FCI capability area.
    The FCIBase class provides shared helper methods.

    Example:
        fci = FCIUtility()

        # Get cash position
        cash = fci.get_cash("org_123", "user_456", {})

        # Get AR aging with specific date
        ar = fci.get_ar("org_123", "user_456", {"as_of_date": "2026-01-15"})

        # Get P&L report
        pl = fci.get_profit_loss("org_123", "user_456", {
            "start_date": "2026-01-01",
            "end_date": "2026-01-31"
        })
    """

    pass


# Singleton instance
_fci_utility_instance: FCIUtility | None = None


def get_fci_utility() -> FCIUtility:
    """
    Get the singleton FCI utility instance.

    Returns:
        FCIUtility instance ready for use
    """
    global _fci_utility_instance

    if _fci_utility_instance is None:
        _fci_utility_instance = FCIUtility()

    return _fci_utility_instance


# Export public interface
__all__ = [
    "FCIUtility",
    "get_fci_utility",
]
