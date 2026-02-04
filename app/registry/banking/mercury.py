"""
Mercury Capability Registry
"""

from app.connectors.mercury import MercuryConnector

mercury_connector = MercuryConnector()

MERCURY_CAPABILITIES = {
    "mercury.account.list": {
        "handler": mercury_connector.list_accounts,
        "tool_name": "mercury.list_accounts",
        "description": "List Mercury banking accounts",
        "requires_oauth": False,
        "service": "mercury",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "mercury.transaction.get": {
        "handler": mercury_connector.get_transactions,
        "tool_name": "mercury.get_transactions",
        "description": "Get transactions from Mercury",
        "requires_oauth": False,
        "service": "mercury",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "mercury.payment.create": {
        "handler": mercury_connector.create_payment,
        "tool_name": "mercury.create_payment",
        "description": "Create ACH payment (100 free/month)",
        "requires_oauth": False,
        "service": "mercury",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "mercury.recipient.create": {
        "handler": mercury_connector.create_recipient,
        "tool_name": "mercury.create_recipient",
        "description": "Create payment recipient",
        "requires_oauth": False,
        "service": "mercury",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "mercury.recipient.list": {
        "handler": mercury_connector.list_recipients,
        "tool_name": "mercury.list_recipients",
        "description": "List payment recipients",
        "requires_oauth": False,
        "service": "mercury",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "mercury.wire.create": {
        "handler": mercury_connector.create_wire,
        "tool_name": "mercury.create_wire",
        "description": "Create wire transfer (domestic/international)",
        "requires_oauth": False,
        "service": "mercury",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}
