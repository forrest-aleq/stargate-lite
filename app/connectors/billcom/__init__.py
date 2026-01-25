"""
Bill.com connector for Stargate Lite.

Handles vendor payments and AP automation using Bill.com v3 API.
Uses session-based authentication (NOT OAuth 2.0).

API Reference: https://developer.bill.com/reference/api-reference-overview
"""

from app.connectors.billcom.bills import BillComBillsMixin
from app.connectors.billcom.payments import BillComPaymentsMixin
from app.connectors.billcom.vendors import BillComVendorsMixin


class BillComConnector(BillComVendorsMixin, BillComBillsMixin, BillComPaymentsMixin):
    """
    Bill.com v3 API connector for AP automation.

    Combines all Bill.com operations:
    - Vendors: create, get, list, update, archive, credits
    - Bills: create, get, list, update, approve, archive, record payment
    - Payments: create, get, list, cancel, void, bulk payments, bank accounts

    Authentication:
    - Session-based (NOT OAuth 2.0)
    - Login with credentials to get sessionId
    - Session expires after 35 minutes of inactivity

    Environment variables:
    - BILLCOM_DEV_KEY: Developer key from Bill.com
    - BILLCOM_ENVIRONMENT: 'sandbox' or 'production' (default: sandbox)

    Credential storage (via CredentialManager):
    - access_token: Bill.com username or sync token name
    - refresh_token: Bill.com password or sync token value
    - realm_id: Bill.com organization ID
    """

    pass


__all__ = ["BillComConnector"]
