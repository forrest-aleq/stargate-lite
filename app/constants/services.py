"""
Service constants for Stargate Lite
Defines OAuth requirements and display names for all services.
"""

# All services in the registry with OAuth requirements
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
