"""
FCI Service Mappings.

Maps services to their connector classes and defines which services
support each FCI primitive. This allows the FCI layer to dynamically
discover available data sources based on connected services.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


def _get_connector_classes() -> dict[str, Any]:
    """
    Lazy-load connector classes to avoid circular imports.
    Returns a dict mapping service name to connector class.
    """
    from app.connectors.billcom import BillComConnector
    from app.connectors.brex import BrexConnector
    from app.connectors.chase import ChaseConnector
    from app.connectors.gusto import GustoConnector
    from app.connectors.hubspot import HubSpotConnector
    from app.connectors.mercury import MercuryConnector
    from app.connectors.netsuite import NetSuiteConnector
    from app.connectors.plaid import PlaidConnector
    from app.connectors.quickbooks import QuickBooksConnector
    from app.connectors.ramp import RampConnector
    from app.connectors.recurly import RecurlyConnector
    from app.connectors.sage_intacct import SageIntacctConnector
    from app.connectors.shopify import ShopifyConnector
    from app.connectors.square import SquareConnector
    from app.connectors.stripe import StripeConnector
    from app.connectors.xero import XeroConnector

    return {
        "quickbooks": QuickBooksConnector,
        "xero": XeroConnector,
        "sage_intacct": SageIntacctConnector,
        "netsuite": NetSuiteConnector,
        "plaid": PlaidConnector,
        "mercury": MercuryConnector,
        "brex": BrexConnector,
        "chase": ChaseConnector,
        "ramp": RampConnector,
        "gusto": GustoConnector,
        "billcom": BillComConnector,
        "stripe": StripeConnector,
        "shopify": ShopifyConnector,
        "square": SquareConnector,
        "recurly": RecurlyConnector,
        "hubspot": HubSpotConnector,
    }


# Connector instance cache (lazy-loaded singletons)
_connector_instances: dict[str, Any] = {}


def get_connector(service: str) -> Any:
    """
    Get or create a connector instance for the given service.
    Connectors are cached as singletons.
    """
    if service not in _connector_instances:
        classes = _get_connector_classes()
        if service not in classes:
            raise ValueError(f"Unknown service: {service}")
        _connector_instances[service] = classes[service]()
    return _connector_instances[service]


# =============================================================================
# Cash Services - Bank accounts and balances
# =============================================================================
CASH_SERVICES: dict[str, str] = {
    "plaid": "get_balance",
    "mercury": "list_accounts",
    "brex": "get_account_balance",
    "chase": "get_account_balance",
    "ramp": "list_transactions",  # Ramp provides balance in transaction list
    "stripe": "get_balance",
    "sage_intacct": "get_checking_accounts",
}


# =============================================================================
# AR Services - Accounts Receivable
# =============================================================================
AR_SERVICES: dict[str, str] = {
    "quickbooks": "get_ar_aging",
    "xero": "get_ar_aging_report",
    "sage_intacct": "get_ar_aging",
    "netsuite": "get_ar_aging",
}


# =============================================================================
# AP Services - Accounts Payable
# =============================================================================
AP_SERVICES: dict[str, str] = {
    "quickbooks": "get_ap_aging",
    "xero": "get_ap_aging_report",
    "sage_intacct": "get_ap_aging",
    "netsuite": "get_ap_aging",
    "billcom": "list_bills",
}


# =============================================================================
# Revenue Services - Income/Revenue data
# =============================================================================
REVENUE_SERVICES: dict[str, str] = {
    "quickbooks": "get_profit_loss_report",
    "xero": "get_profit_loss_report",
    "sage_intacct": "get_profit_loss_report",
    "stripe": "list_charges",
    "recurly": "list_invoices",
    "shopify": "list_orders",
    "square": "list_payments",
}


# =============================================================================
# Expense Services - Expense data
# =============================================================================
EXPENSE_SERVICES: dict[str, str] = {
    "quickbooks": "get_profit_loss_report",
    "xero": "get_profit_loss_report",
    "sage_intacct": "get_profit_loss_report",
    "brex": "list_expenses",
    "ramp": "list_transactions",
}


# =============================================================================
# Payroll Services
# =============================================================================
PAYROLL_SERVICES: dict[str, str] = {
    "gusto": "list_payrolls",
}


# =============================================================================
# P&L Report Services
# =============================================================================
PL_REPORT_SERVICES: dict[str, str] = {
    "quickbooks": "get_profit_loss_report",
    "xero": "get_profit_loss_report",
    "sage_intacct": "get_profit_loss_report",
    "netsuite": "get_profit_loss_report",
}


# =============================================================================
# Balance Sheet Services
# =============================================================================
BALANCE_SHEET_SERVICES: dict[str, str] = {
    "quickbooks": "get_balance_sheet",
    "xero": "get_balance_sheet_report",
    "sage_intacct": "get_balance_sheet",
    "netsuite": "get_balance_sheet",
}


# =============================================================================
# Cash Flow Services
# =============================================================================
CASHFLOW_SERVICES: dict[str, str] = {
    "quickbooks": "get_cashflow_report",
    "xero": "get_cash_flow_report",
    "sage_intacct": "get_cash_flow_report",
}


# =============================================================================
# Customer Lookup Services
# =============================================================================
CUSTOMER_SERVICES: dict[str, str] = {
    "quickbooks": "get_customer",
    "xero": "get_contact",
    "stripe": "get_customer",
    "shopify": "get_customer",
    "hubspot": "get_contact",
    "recurly": "get_account",
    "square": "get_customer",
}


# =============================================================================
# Vendor Lookup Services
# =============================================================================
VENDOR_SERVICES: dict[str, str] = {
    "quickbooks": "get_vendor",
    "xero": "get_contact",
    "billcom": "get_vendor",
    "netsuite": "get_vendor",
    "sage_intacct": "get_vendor",
}


# =============================================================================
# Invoice Lookup Services
# =============================================================================
INVOICE_SERVICES: dict[str, str] = {
    "quickbooks": "get_invoice",
    "xero": "get_invoice",
    "stripe": "get_invoice",
    "recurly": "get_invoice",
    "square": "get_invoice",
}


# =============================================================================
# Priority order for accounting systems (prefer full-featured over partial)
# =============================================================================
ACCOUNTING_PRIORITY = [
    "quickbooks",
    "xero",
    "sage_intacct",
    "netsuite",
]

BANKING_PRIORITY = [
    "plaid",  # Aggregator - often has multiple banks
    "mercury",
    "chase",
    "brex",
    "ramp",
    "stripe",
]


# =============================================================================
# Cache TTLs (seconds) - for future caching implementation
# =============================================================================
CACHE_TTL = {
    "fci.cash": 60,  # 1 min - balances change frequently
    "fci.ar": 300,  # 5 min - AR aging updates less frequently
    "fci.ap": 300,  # 5 min - AP aging updates less frequently
    "fci.revenue": 300,  # 5 min
    "fci.expenses": 300,  # 5 min
    "fci.burn": 3600,  # 1 hour - computed metric
    "fci.runway": 3600,  # 1 hour - derived from burn
    "fci.payroll": 3600,  # 1 hour - payroll rarely changes mid-day
    "fci.report.profitloss": 600,  # 10 min
    "fci.report.balancesheet": 600,  # 10 min
    "fci.report.ar_aging": 300,  # 5 min
    "fci.report.ap_aging": 300,  # 5 min
    "fci.report.cashflow": 600,  # 10 min
}
