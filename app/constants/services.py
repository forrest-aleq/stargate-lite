"""
Service constants for Stargate Lite
Defines OAuth requirements, enabled services, and display names for all services.
"""

# =============================================================================
# ENABLED SERVICES — Controls what N3 shows on the integrations page.
#
# Only services listed here appear in /health/connectors and are available
# for customers to connect. Add a service here AFTER:
#   1. Developer/sandbox credentials are configured in Railway
#   2. OAuth flow is tested end-to-end on staging
#   3. At least one capability is verified working
#
# ALL_SERVICES_OAUTH below is the full internal registry — it stays complete.
# ENABLED_SERVICES is the customer-facing gate.
# =============================================================================
ENABLED_SERVICES: set[str] = {
    "quickbooks",
}

# All services in the registry with OAuth requirements (internal — not all are customer-facing)
ALL_SERVICES_OAUTH: dict[str, bool] = {
    "quickbooks": True,  # requires_oauth
    "stripe": False,
    "billcom": True,
    "netsuite": True,
    "recurly": False,
    "plaid": False,
    "ramp": True,
    "mercury": False,
    "brex": True,
    "chase": True,
    "hubspot": True,
    "notion": True,
    "asana": True,
    "powerbi": True,
    "google": True,
    "slack": True,
    "blandai": False,
    "twilio": False,
    "ibkr": False,
    "schwab": True,
    "microsoft": True,
    "ocr": False,
}

# Extended OAuth requirements (includes gmail and vision for workflow checks)
WORKFLOW_OAUTH_REQUIREMENTS: dict[str, bool] = {
    **ALL_SERVICES_OAUTH,
    "gmail": True,  # Gmail uses Google OAuth
    "vision": True,  # Vision API (Claude)
}

# Display name mappings for services
SERVICE_DISPLAY_NAMES: dict[str, str] = {
    "quickbooks": "QuickBooks",
    "gmail": "Gmail",
    "google": "Google",
    "vision": "Vision API",
    "slack": "Slack",
    "hubspot": "HubSpot",
    "stripe": "Stripe",
    "notion": "Notion",
    "asana": "Asana",
    "powerbi": "Power BI",
    "microsoft": "Microsoft",
}
