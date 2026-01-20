"""
QuickBooks Online connector package

This package provides a modular QuickBooks API connector split across multiple files
to maintain code under the 500-line limit per file.

Modules:
- base: Authentication and token refresh
- vendors: Vendor operations
- customers: Customer operations
- bills: Bills and payables
- invoices: Invoice operations
- payments: Payment operations
- items: Items and document operations
- reports: Reports and queries
- accounting: Journal entries, chart of accounts, employees, etc.
"""

from app.connectors.quickbooks.accounting import QuickBooksAccountingMixin
from app.connectors.quickbooks.base import QuickBooksBase
from app.connectors.quickbooks.bills import QuickBooksBillsMixin
from app.connectors.quickbooks.customers import QuickBooksCustomersMixin
from app.connectors.quickbooks.invoices import QuickBooksInvoicesMixin
from app.connectors.quickbooks.items import QuickBooksItemsMixin
from app.connectors.quickbooks.payments import QuickBooksPaymentsMixin
from app.connectors.quickbooks.reports import QuickBooksReportsMixin
from app.connectors.quickbooks.vendors import QuickBooksVendorsMixin


class QuickBooksConnector(
    QuickBooksBase,
    QuickBooksVendorsMixin,
    QuickBooksCustomersMixin,
    QuickBooksBillsMixin,
    QuickBooksInvoicesMixin,
    QuickBooksPaymentsMixin,
    QuickBooksItemsMixin,
    QuickBooksReportsMixin,
    QuickBooksAccountingMixin,
):
    """
    QuickBooks Online API connector.

    This class combines all QuickBooks operations through mixin classes:
    - Authentication and token management (from QuickBooksBase)
    - Vendor operations (from QuickBooksVendorsMixin)
    - Customer operations (from QuickBooksCustomersMixin)
    - Bill and payables (from QuickBooksBillsMixin)
    - Invoice operations (from QuickBooksInvoicesMixin)
    - Payment operations (from QuickBooksPaymentsMixin)
    - Items and documents (from QuickBooksItemsMixin)
    - Reports and queries (from QuickBooksReportsMixin)
    - Accounting operations (from QuickBooksAccountingMixin)
    """

    pass


__all__ = ["QuickBooksConnector"]
