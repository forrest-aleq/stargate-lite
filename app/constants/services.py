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

# Customer-facing connector visibility is controlled by ENABLED_SERVICES.
# Provider readiness is evaluated separately so Aleq can surface the full
# environment roadmap without hiding partially configured systems.
CUSTOMER_CONNECT_ENV_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "quickbooks": (
        "QUICKBOOKS_CLIENT_ID",
        "QUICKBOOKS_CLIENT_SECRET",
        "QUICKBOOKS_REDIRECT_URI",
    ),
    "xero": (
        "XERO_CLIENT_ID",
        "XERO_CLIENT_SECRET",
        "XERO_REDIRECT_URI",
    ),
    "zoho_books": (
        "ZOHO_BOOKS_CLIENT_ID",
        "ZOHO_BOOKS_CLIENT_SECRET",
        "ZOHO_BOOKS_REDIRECT_URI",
    ),
    "stripe": (
        "STRIPE_SECRET_KEY",
        "STRIPE_CLIENT_ID",
        "STRIPE_REDIRECT_URI",
    ),
    "hubspot": (
        "HUBSPOT_CLIENT_ID",
        "HUBSPOT_CLIENT_SECRET",
        "HUBSPOT_REDIRECT_URI",
    ),
    "slack": (
        "SLACK_CLIENT_ID",
        "SLACK_CLIENT_SECRET",
        "SLACK_REDIRECT_URI",
    ),
    "google": (
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
    ),
    "microsoft": (
        "MICROSOFT_CLIENT_ID",
        "MICROSOFT_CLIENT_SECRET",
        "MICROSOFT_REDIRECT_URI",
    ),
    "powerbi": (
        "MICROSOFT_CLIENT_ID",
        "MICROSOFT_CLIENT_SECRET",
        "MICROSOFT_REDIRECT_URI",
    ),
    "plaid": (
        "PLAID_CLIENT_ID",
        "PLAID_SECRET",
        "PLAID_ENVIRONMENT",
    ),
    "netsuite": (
        "NETSUITE_ACCOUNT_ID",
        "NETSUITE_CONSUMER_KEY",
        "NETSUITE_CONSUMER_SECRET",
        "NETSUITE_REDIRECT_URI",
    ),
    "ramp": (
        "RAMP_CLIENT_ID",
        "RAMP_CLIENT_SECRET",
        "RAMP_REDIRECT_URI",
    ),
    "brex": (
        "BREX_CLIENT_ID",
        "BREX_CLIENT_SECRET",
        "BREX_REDIRECT_URI",
    ),
    "chase": (
        "CHASE_CLIENT_ID",
        "CHASE_CLIENT_SECRET",
        "CHASE_REDIRECT_URI",
    ),
    "schwab": (
        "SCHWAB_CLIENT_ID",
        "SCHWAB_CLIENT_SECRET",
        "SCHWAB_REDIRECT_URI",
    ),
    "notion": (
        "NOTION_CLIENT_ID",
        "NOTION_CLIENT_SECRET",
        "NOTION_REDIRECT_URI",
    ),
    "asana": (
        "ASANA_CLIENT_ID",
        "ASANA_CLIENT_SECRET",
        "ASANA_REDIRECT_URI",
    ),
    "clickup": (
        "CLICKUP_CLIENT_ID",
        "CLICKUP_CLIENT_SECRET",
        "CLICKUP_REDIRECT_URI",
    ),
    "monday": (
        "MONDAY_CLIENT_ID",
        "MONDAY_CLIENT_SECRET",
        "MONDAY_REDIRECT_URI",
    ),
    "linear": (
        "LINEAR_CLIENT_ID",
        "LINEAR_CLIENT_SECRET",
        "LINEAR_REDIRECT_URI",
    ),
    "airtable": (
        "AIRTABLE_CLIENT_ID",
        "AIRTABLE_CLIENT_SECRET",
        "AIRTABLE_REDIRECT_URI",
    ),
    "gusto": (
        "GUSTO_CLIENT_ID",
        "GUSTO_CLIENT_SECRET",
        "GUSTO_REDIRECT_URI",
    ),
    "shopify": (
        "SHOPIFY_CLIENT_ID",
        "SHOPIFY_CLIENT_SECRET",
        "SHOPIFY_REDIRECT_URI",
    ),
    "square": (
        "SQUARE_APPLICATION_ID",
        "SQUARE_APPLICATION_SECRET",
        "SQUARE_REDIRECT_URI",
    ),
    "docusign": (
        "DOCUSIGN_INTEGRATION_KEY",
        "DOCUSIGN_SECRET_KEY",
        "DOCUSIGN_REDIRECT_URI",
    ),
}

# All services in the registry with OAuth requirements (internal — not all are customer-facing)
ALL_SERVICES_OAUTH: dict[str, bool] = {
    "quickbooks": True,  # requires_oauth
    "stripe": False,
    "billcom": True,
    "netsuite": True,
    "recurly": False,
    "plaid": False,
    "sms": False,
    "voice": False,
    "ramp": True,
    "mercury": False,
    "brex": True,
    "chase": True,
    "hubspot": True,
    "gmail": True,
    "google": True,
    "slack": True,
    "notion": True,
    "asana": True,
    "clickup": True,
    "linear": True,
    "monday": True,
    "airtable": True,
    "dropbox": True,
    "powerbi": True,
    "docusign": True,
    "gusto": True,
    "shopify": True,
    "square": True,
    "sage_intacct": True,
    "blandai": False,
    "twilio": False,
    "ibkr": False,
    "schwab": True,
    "microsoft": True,
    "xero": True,
    "zoho_books": True,
    "ocr": False,
    "hyperbrowser": False,
}

# Extended OAuth requirements (includes gmail and vision for workflow checks)
WORKFLOW_OAUTH_REQUIREMENTS: dict[str, bool] = {
    **ALL_SERVICES_OAUTH,
    "vision": True,  # Vision API (Claude)
}

# Display name mappings for services
SERVICE_DISPLAY_NAMES: dict[str, str] = {
    "quickbooks": "QuickBooks",
    "xero": "Xero",
    "zoho_books": "Zoho Books",
    "netsuite": "NetSuite",
    "gmail": "Gmail",
    "google": "Google",
    "slack": "Slack",
    "hubspot": "HubSpot",
    "stripe": "Stripe",
    "plaid": "Plaid",
    "mercury": "Mercury",
    "brex": "Brex",
    "chase": "Chase",
    "billcom": "Bill.com",
    "recurly": "Recurly",
    "sms": "SMS",
    "voice": "Voice",
    "linear": "Linear",
    "clickup": "ClickUp",
    "monday": "Monday.com",
    "airtable": "Airtable",
    "dropbox": "Dropbox",
    "notion": "Notion",
    "asana": "Asana",
    "docusign": "DocuSign",
    "gusto": "Gusto",
    "shopify": "Shopify",
    "square": "Square",
    "sage_intacct": "Sage Intacct",
    "ramp": "Ramp",
    "powerbi": "Power BI",
    "microsoft": "Microsoft",
    "vision": "Vision API",
    "hyperbrowser": "Hyperbrowser",
}

# OAuth authorize paths — used to build connect_url in CREDENTIALS_MISSING errors.
# Only services with a standard OAuth authorize endpoint are listed here.
# Services using API keys (stripe, recurly, mercury), Link tokens (plaid),
# or session auth (billcom) are excluded — they require different onboarding.
OAUTH_AUTHORIZE_PATHS: dict[str, str] = {
    "quickbooks": "/oauth/quickbooks/authorize",
    "xero": "/oauth/xero/authorize",
    "zoho_books": "/oauth/zoho_books/authorize",
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


def service_is_customer_connectable(service: str) -> bool:
    """Return whether a customer-facing service is fully configured for connection."""
    required = CUSTOMER_CONNECT_ENV_REQUIREMENTS.get(service)
    if not required:
        return False
    return all(os.getenv(env_var, "").strip() for env_var in required)


def get_customer_facing_enabled_services() -> dict[str, bool]:
    """Return every explicitly enabled customer-facing service.

    Connectability is evaluated separately at connect time. Hiding enabled services
    made staging look artificially narrow and prevented Aleq from surfacing the
    actual integration roadmap of the environment.
    """
    return {
        service: ALL_SERVICES_OAUTH.get(service, False)
        for service in ENABLED_SERVICES
    }
