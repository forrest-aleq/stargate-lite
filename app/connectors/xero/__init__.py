"""
Xero Accounting API Connector - Full integration for Xero accounting software.

Reference: https://developer.xero.com/documentation/api/accounting/overview
API Version: api.xro/2.0 (January 2026)

Capabilities:
- Contacts: Customer and supplier management
- Invoices: Sales invoices (AR)
- Bills: Supplier bills (AP)
- Payments: Payment recording and batch payments
- Credit Notes: Customer and supplier credit notes
- Bank Transactions: Bank account transactions
- Bank Transfers: Inter-account transfers
- Reports: P&L, Balance Sheet, Trial Balance, Aging reports
- Manual Journals: Journal entries
- Chart of Accounts: GL account management

OAuth 2.0 with PKCE authentication.
Tokens expire after 30 minutes, refresh tokens valid for 60 days.
"""

from .reports import ReportsMixin


class XeroConnector(ReportsMixin):
    """
    Xero Accounting API connector with full accounting capabilities.

    Inherits from mixin chain:
    ReportsMixin -> BankMixin -> CreditNotesMixin -> PaymentsMixin ->
    BillsMixin -> InvoicesMixin -> ContactsMixin -> XeroBase

    Usage:
        connector = XeroConnector()
        result = connector.list_invoices(org_id, user_id, {"status": "AUTHORISED"})
    """

    pass


# Export singleton instance
xero_connector = XeroConnector()

# Export all capability handlers
__all__ = [
    "XeroConnector",
    "xero_connector",
]
