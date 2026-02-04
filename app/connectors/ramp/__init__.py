"""
Ramp connector for Stargate Lite.

Handles OAuth 2.0, corporate cards, expenses, reimbursements,
vendors, bills, treasury, and organizational management.
"""

from .hr import HRMixin


class RampConnector(HRMixin):
    """Ramp API connector with full capability coverage."""

    pass


__all__ = ["RampConnector"]
