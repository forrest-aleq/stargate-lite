"""
Bill.com Capability Registry
"""

from app.connectors.bill_com import BillComConnector

# Initialize connector
billcom_connector = BillComConnector()

BILLCOM_CAPABILITIES = {
    # ========== BILL.COM ==========
    "billcom.vendor.create": {
        "handler": billcom_connector.create_vendor,
        "tool_name": "billcom.create_vendor",
        "description": "Create a vendor in Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "billcom.bill.create": {
        "handler": billcom_connector.create_bill,
        "tool_name": "billcom.create_bill",
        "description": "Create a bill in Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "billcom.payment.create": {
        "handler": billcom_connector.create_payment,
        "tool_name": "billcom.create_payment",
        "description": "Create a payment in Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "billcom.payment.bulk": {
        "handler": billcom_connector.create_bulk_payment,
        "tool_name": "billcom.create_bulk_payment",
        "description": "Create bulk payments in Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "billcom.bill.list": {
        "handler": billcom_connector.list_bills,
        "tool_name": "billcom.list_bills",
        "description": "List bills from Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "billcom.vendor.list": {
        "handler": billcom_connector.list_vendors,
        "tool_name": "billcom.list_vendors",
        "description": "List vendors from Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "billcom.payment.status": {
        "handler": billcom_connector.get_payment_status,
        "tool_name": "billcom.get_payment_status",
        "description": "Get payment status from Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "billcom.vendorcredit.create": {
        "handler": billcom_connector.create_vendor_credit,
        "tool_name": "billcom.create_vendor_credit",
        "description": "Create a vendor credit in Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "billcom.bill.approve": {
        "handler": billcom_connector.approve_bill,
        "tool_name": "billcom.approve_bill",
        "description": "Approve a bill in Bill.com",
        "requires_oauth": True,
        "service": "billcom",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}
