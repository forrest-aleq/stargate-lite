"""
QuickBooks Capability Schemas.

Aggregates all QuickBooks capability schemas into a single registry.
Complete coverage of all 71+ QuickBooks capabilities.
"""

from app.schemas.base import CapabilitySchema
from app.schemas.quickbooks.accounting import ACCOUNTING_SCHEMAS
from app.schemas.quickbooks.billpayments import BILLPAYMENT_SCHEMAS
from app.schemas.quickbooks.bills import BILL_SCHEMAS
from app.schemas.quickbooks.customers import CUSTOMER_SCHEMAS
from app.schemas.quickbooks.invoices import INVOICE_SCHEMAS
from app.schemas.quickbooks.items import ITEM_SCHEMAS
from app.schemas.quickbooks.organization import ORGANIZATION_SCHEMAS
from app.schemas.quickbooks.payments import PAYMENT_SCHEMAS
from app.schemas.quickbooks.reports import REPORT_SCHEMAS
from app.schemas.quickbooks.sales import SALES_SCHEMAS
from app.schemas.quickbooks.transactions import TRANSACTION_SCHEMAS
from app.schemas.quickbooks.vendors import VENDOR_SCHEMAS

# All QuickBooks schemas - complete coverage
QUICKBOOKS_SCHEMAS: dict[str, CapabilitySchema] = {
    **VENDOR_SCHEMAS,  # 5 capabilities
    **BILL_SCHEMAS,  # 3 capabilities
    **BILLPAYMENT_SCHEMAS,  # 2 capabilities
    **CUSTOMER_SCHEMAS,  # 9 capabilities (5 + 4 aliases)
    **INVOICE_SCHEMAS,  # 11 capabilities (6 + 5 aliases)
    **ITEM_SCHEMAS,  # 3 capabilities
    **PAYMENT_SCHEMAS,  # 4 capabilities
    **SALES_SCHEMAS,  # 6 capabilities
    **ACCOUNTING_SCHEMAS,  # 5 capabilities (journal, query, accounts)
    **TRANSACTION_SCHEMAS,  # 5 capabilities (PO, expense, deposit, transfer, txn list)
    **REPORT_SCHEMAS,  # 9 capabilities
    **ORGANIZATION_SCHEMAS,  # 9 capabilities
}

__all__ = ["QUICKBOOKS_SCHEMAS"]
