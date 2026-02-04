"""
Brex Capability Registry
"""

from app.connectors.brex import BrexConnector

brex_connector = BrexConnector()

BREX_CAPABILITIES = {
    "brex.transaction.list": {
        "handler": brex_connector.list_transactions,
        "tool_name": "brex.list_transactions",
        "description": "List card transactions in Brex",
        "requires_oauth": True,
        "service": "brex",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "brex.expense.list": {
        "handler": brex_connector.list_expenses,
        "tool_name": "brex.list_expenses",
        "description": "List expenses with categories in Brex",
        "requires_oauth": True,
        "service": "brex",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "brex.card.virtual.create": {
        "handler": brex_connector.create_virtual_card,
        "tool_name": "brex.create_virtual_card",
        "description": "Create virtual card with spending limits",
        "requires_oauth": True,
        "service": "brex",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "brex.card.lock": {
        "handler": brex_connector.lock_card,
        "tool_name": "brex.lock_card",
        "description": "Lock a card in Brex",
        "requires_oauth": True,
        "service": "brex",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "brex.card.unlock": {
        "handler": brex_connector.unlock_card,
        "tool_name": "brex.unlock_card",
        "description": "Unlock a card in Brex",
        "requires_oauth": True,
        "service": "brex",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "brex.card.limit.update": {
        "handler": brex_connector.update_card_limit,
        "tool_name": "brex.update_card_limit",
        "description": "Update card spending limit",
        "requires_oauth": True,
        "service": "brex",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "brex.payment.create": {
        "handler": brex_connector.create_payment,
        "tool_name": "brex.create_payment",
        "description": "Create vendor payment in Brex",
        "requires_oauth": True,
        "service": "brex",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "brex.balance.get": {
        "handler": brex_connector.get_account_balance,
        "tool_name": "brex.get_account_balance",
        "description": "Get cash account balance",
        "requires_oauth": True,
        "service": "brex",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}
