"""
Service constants for Stargate Lite
Defines OAuth requirements, enabled services, and display names for all services.
"""

import os

# =============================================================================
# ENABLED SERVICES — Controls what N3 shows on the integrations page.
#
# Set via the ENABLED_SERVICES env var (comma-separated service names):
#   ENABLED_SERVICES=quickbooks,xero,stripe,hubspot,slack
#
# If the env var is not set, falls back to the default set below.
# Only services listed here appear in /health/connectors and are available
# for customers to connect.
#
# ALL_SERVICES_OAUTH below is the full internal registry — it stays complete.
# ENABLED_SERVICES is the customer-facing gate.
# =============================================================================
_DEFAULT_ENABLED: set[str] = {
    "quickbooks",
}

_env_enabled = os.getenv("ENABLED_SERVICES", "").strip()
ENABLED_SERVICES: set[str] = (
    {s.strip() for s in _env_enabled.split(",") if s.strip()} if _env_enabled else _DEFAULT_ENABLED
)

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
    "xero": True,
    "ocr": False,
    "hyperbrowser": False,
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
    "xero": "Xero",
    "hyperbrowser": "Hyperbrowser",
}

# OAuth authorize paths — used to build connect_url in CREDENTIALS_MISSING errors.
# Only services with a standard OAuth authorize endpoint are listed here.
# Services using API keys (stripe, recurly, mercury), Link tokens (plaid),
# or session auth (billcom) are excluded — they require different onboarding.
OAUTH_AUTHORIZE_PATHS: dict[str, str] = {
    "quickbooks": "/oauth/quickbooks/authorize",
    "xero": "/oauth/xero/authorize",
    "hubspot": "/oauth/hubspot/authorize",
    "google": "/oauth/google/authorize",
    "slack": "/oauth/slack/authorize",
    "microsoft": "/oauth/microsoft/authorize",
    "powerbi": "/oauth/powerbi/authorize",
    "netsuite": "/oauth/netsuite/authorize",
    "stripe": "/oauth/stripe/authorize",
    "brex": "/oauth/brex/authorize",
    "ramp": "/oauth/ramp/authorize",
    "chase": "/oauth/chase/authorize",
    "schwab": "/oauth/schwab/authorize",
    "notion": "/oauth/notion/authorize",
    "asana": "/oauth/asana/authorize",
    "clickup": "/oauth/clickup/authorize",
    "monday": "/oauth/monday/authorize",
    "linear": "/oauth/linear/authorize",
    "airtable": "/oauth/airtable/authorize",
    "gusto": "/oauth/gusto/authorize",
    "shopify": "/oauth/shopify/authorize",
    "square": "/oauth/square/authorize",
    "docusign": "/oauth/docusign/authorize",
}


def build_connect_url(service: str, org_id: str, user_id: str) -> str | None:
    """Build the OAuth authorize URL for a service, or None if not OAuth-based."""
    path = OAUTH_AUTHORIZE_PATHS.get(service)
    if not path:
        return None
    return f"{path}?org_id={org_id}&user_id={user_id}&credential_type=customer"
