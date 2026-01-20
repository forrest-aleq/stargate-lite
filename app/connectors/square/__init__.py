"""
Square connector package

This package provides a modular Square API connector split across multiple files
to maintain code under the 500-line limit per file.

Modules:
- base: Authentication and token refresh
- locations: Location operations
- payments: Payment operations
- orders: Order operations
- customers: Customer operations
- invoices: Invoice operations
- payouts: Payout operations
"""

from app.connectors.square.base import SquareBase
from app.connectors.square.customers import SquareCustomersMixin
from app.connectors.square.invoices import SquareInvoicesMixin
from app.connectors.square.locations import SquareLocationsMixin
from app.connectors.square.orders import SquareOrdersMixin
from app.connectors.square.payments import SquarePaymentsMixin
from app.connectors.square.payouts import SquarePayoutsMixin


class SquareConnector(
    SquareBase,
    SquareLocationsMixin,
    SquarePaymentsMixin,
    SquareOrdersMixin,
    SquareCustomersMixin,
    SquareInvoicesMixin,
    SquarePayoutsMixin,
):
    """
    Square API connector.

    This class combines all Square operations through mixin classes:
    - Authentication and token management (from SquareBase)
    - Location operations (from SquareLocationsMixin)
    - Payment operations (from SquarePaymentsMixin)
    - Order operations (from SquareOrdersMixin)
    - Customer operations (from SquareCustomersMixin)
    - Invoice operations (from SquareInvoicesMixin)
    - Payout operations (from SquarePayoutsMixin)
    """

    pass


# Singleton instance
square_connector = SquareConnector()

__all__ = ["SquareConnector", "square_connector"]
