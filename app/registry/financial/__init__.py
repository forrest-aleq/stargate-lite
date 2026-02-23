"""
Financial/Accounting Capability Registry Package

Aggregates capabilities from:
- QuickBooks (split into core, invoices, reports)
- Stripe (split into core, billing)
- Bill.com
- NetSuite
- Recurly
- Xero
- Zoho Books
- Sage Intacct
- Gusto (payroll/HR)
- Shopify (e-commerce)
- Square (payments/POS)
"""

from app.registry.financial.billcom import BILLCOM_CAPABILITIES
from app.registry.financial.gusto import GUSTO_CAPABILITIES
from app.registry.financial.netsuite import NETSUITE_CAPABILITIES
from app.registry.financial.quickbooks_core import QUICKBOOKS_CORE_CAPABILITIES
from app.registry.financial.quickbooks_invoices import QUICKBOOKS_INVOICE_CAPABILITIES
from app.registry.financial.quickbooks_reports import QUICKBOOKS_REPORT_CAPABILITIES
from app.registry.financial.recurly import RECURLY_CAPABILITIES
from app.registry.financial.sage_intacct import SAGE_INTACCT_CAPABILITIES
from app.registry.financial.shopify import SHOPIFY_CAPABILITIES
from app.registry.financial.square import SQUARE_CAPABILITIES
from app.registry.financial.stripe_billing import STRIPE_BILLING_CAPABILITIES
from app.registry.financial.stripe_core import STRIPE_CORE_CAPABILITIES
from app.registry.financial.xero import XERO_CAPABILITIES
from app.registry.financial.zoho_books import ZOHO_BOOKS_CAPABILITIES

# Aggregate all financial capabilities
FINANCIAL_CAPABILITIES = {
    **QUICKBOOKS_CORE_CAPABILITIES,
    **QUICKBOOKS_INVOICE_CAPABILITIES,
    **QUICKBOOKS_REPORT_CAPABILITIES,
    **STRIPE_CORE_CAPABILITIES,
    **STRIPE_BILLING_CAPABILITIES,
    **BILLCOM_CAPABILITIES,
    **NETSUITE_CAPABILITIES,
    **RECURLY_CAPABILITIES,
    **XERO_CAPABILITIES,
    **SAGE_INTACCT_CAPABILITIES,
    **GUSTO_CAPABILITIES,
    **SHOPIFY_CAPABILITIES,
    **SQUARE_CAPABILITIES,
    **ZOHO_BOOKS_CAPABILITIES,
}

__all__ = ["FINANCIAL_CAPABILITIES"]
