"""
NetSuite connector for Stargate Lite
Handles ERP operations via NetSuite REST API
Uses NetSuite REST API (October 2025)
"""

from .payments import PaymentsMixin


class NetSuiteConnector(PaymentsMixin):
    """
    NetSuite REST API connector.

    Inherits from PaymentsMixin which inherits from VendorsMixin
    which inherits from JournalEntriesMixin which inherits from NetSuiteBase.
    """

    pass


__all__ = ["NetSuiteConnector"]
