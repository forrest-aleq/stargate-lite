"""
Sage Intacct REST API connector.

Reference: https://developer.sage.com/intacct/docs/

Provides comprehensive access to Sage Intacct functionality:
- General Ledger (chart of accounts, journal entries, trial balance)
- Accounts Payable (vendors, bills, bill payments, AP aging)
- Accounts Receivable (customers, invoices, payments, AR aging)
- Cash Management (bank accounts, deposits, transfers, reconciliation)

Authentication: OAuth 2.0 with authorization code flow.
Requires a Web Services developer license and Sage App Registry application.
"""

from .cash import CashManagementMixin


class SageIntacctConnector(CashManagementMixin):
    """Complete Sage Intacct connector with all capabilities.

    Inheritance chain:
    SageIntacctBase -> GLMixin -> APMixin -> ARMixin -> CashManagementMixin -> SageIntacctConnector

    This provides:
    - Base: OAuth 2.0 auth, token refresh, API calls, pagination
    - GL: Chart of accounts, journal entries, trial balance
    - AP: Vendors, bills, bill payments, AP aging
    - AR: Customers, invoices, AR payments, AR aging
    - Cash: Bank accounts, deposits, transfers, reconciliation
    """

    pass


# Export the connector
__all__ = ["SageIntacctConnector"]
