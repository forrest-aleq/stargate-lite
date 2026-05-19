"""
Chase/J.P. Morgan Capability Registry
"""

from app.connectors.chase import ChaseConnector

chase_connector = ChaseConnector()

CHASE_CAPABILITIES = {
    "chase.account.list": {
        "handler": chase_connector.list_accounts,
        "tool_name": "chase.list_accounts",
        "description": "List business banking accounts",
        "requires_oauth": True,
        "service": "chase",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "chase.balance.get": {
        "handler": chase_connector.get_account_balance,
        "tool_name": "chase.get_account_balance",
        "description": "Get account balance",
        "requires_oauth": True,
        "service": "chase",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "chase.transaction.get": {
        "handler": chase_connector.get_transactions,
        "tool_name": "chase.get_transactions",
        "description": "Get account transactions",
        "requires_oauth": True,
        "service": "chase",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "chase.ach.create": {
        "handler": chase_connector.create_ach_payment,
        "tool_name": "chase.create_ach_payment",
        "description": "Create ACH payment (free for business)",
        "requires_oauth": True,
        "service": "chase",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "chase.wire.create": {
        "handler": chase_connector.create_wire_payment,
        "tool_name": "chase.create_wire_payment",
        "description": "Create wire transfer (domestic/international)",
        "requires_oauth": True,
        "service": "chase",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "chase.payment.status": {
        "handler": chase_connector.get_payment_status,
        "tool_name": "chase.get_payment_status",
        "description": "Get payment status",
        "requires_oauth": True,
        "service": "chase",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "chase.payment.list": {
        "handler": chase_connector.list_payments,
        "tool_name": "chase.list_payments",
        "description": "List payment history",
        "requires_oauth": True,
        "service": "chase",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "chase.recipient.create": {
        "handler": chase_connector.create_recipient,
        "tool_name": "chase.create_recipient",
        "description": "Create payment recipient/beneficiary",
        "requires_oauth": True,
        "service": "chase",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}
