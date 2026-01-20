"""
Recurly Capability Registry
"""

from app.connectors.recurly import RecurlyConnector

# Initialize connector
recurly_connector = RecurlyConnector()

RECURLY_CAPABILITIES = {
    # ========== RECURLY ==========
    "recurly.account.create": {
        "handler": recurly_connector.create_account,
        "tool_name": "recurly.create_account",
        "description": "Create a customer account in Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.subscription.create": {
        "handler": recurly_connector.create_subscription,
        "tool_name": "recurly.create_subscription",
        "description": "Create a subscription in Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.subscription.cancel": {
        "handler": recurly_connector.cancel_subscription,
        "tool_name": "recurly.cancel_subscription",
        "description": "Cancel a subscription in Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.subscription.pause": {
        "handler": recurly_connector.pause_subscription,
        "tool_name": "recurly.pause_subscription",
        "description": "Pause a subscription in Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.subscription.resume": {
        "handler": recurly_connector.resume_subscription,
        "tool_name": "recurly.resume_subscription",
        "description": "Resume a paused subscription in Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.invoice.list": {
        "handler": recurly_connector.list_invoices,
        "tool_name": "recurly.list_invoices",
        "description": "List invoices in Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.invoice.get": {
        "handler": recurly_connector.get_invoice,
        "tool_name": "recurly.get_invoice",
        "description": "Get invoice details from Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.plan.create": {
        "handler": recurly_connector.create_plan,
        "tool_name": "recurly.create_plan",
        "description": "Create a subscription plan in Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.subscription.list": {
        "handler": recurly_connector.list_subscriptions,
        "tool_name": "recurly.list_subscriptions",
        "description": "List subscriptions in Recurly",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.payment.apply": {
        "handler": recurly_connector.apply_payment,
        "tool_name": "recurly.apply_payment",
        "description": "Apply external payment (check/wire) to invoice - for lockbox processing",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.invoice.collect": {
        "handler": recurly_connector.collect_invoice,
        "tool_name": "recurly.collect_invoice",
        "description": "Force collect invoice using stored billing info",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "recurly.invoice.search": {
        "handler": recurly_connector.search_invoices,
        "tool_name": "recurly.search_invoices",
        "description": "Search invoices by account/number - for lockbox matching",
        "requires_oauth": False,
        "service": "recurly",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}
