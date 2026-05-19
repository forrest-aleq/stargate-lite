"""
Tool Registry for Stargate Lite
Maps capability keys to actual tool implementations
Updated February 2026 - Includes dynamic Zoho Books parity registry
+ Cognitive Utilities Phase 1: web_search, summarizer, financial_calculator
+ Financial Operations: reconciliation, matching, covenants, waterfall, tiered_fees, forecasting
+ Recent additions: Google Workspace, Microsoft 365, Dropbox, DocuSign, Power BI expansions

This module combines all sub-registries into a unified CAPABILITY_REGISTRY.

PRODUCTION SAFETY: Certain high-risk services are explicitly disabled.
"""

import os
from typing import Any

from app.logging_config import get_logger
from app.registry.banking import BANKING_CAPABILITIES
from app.registry.communication import COMMUNICATION_CAPABILITIES
from app.registry.fci import FCI_CAPABILITIES
from app.registry.financial import FINANCIAL_CAPABILITIES
from app.registry.financial_ops import FINANCIAL_OPS_CAPABILITIES
from app.registry.google_microsoft import GOOGLE_MICROSOFT_CAPABILITIES
from app.registry.productivity import PRODUCTIVITY_CAPABILITIES
from app.registry.trading import TRADING_CAPABILITIES
from app.registry.utilities import UTILITIES_CAPABILITIES
from app.registry.vault import VAULT_CAPABILITIES
from app.schemas import has_schema

logger = get_logger(__name__)

# =============================================================================
# PRODUCTION SAFETY: DISABLED SERVICES
# =============================================================================
# Always disabled — trading operations are HIGH RISK
_ALWAYS_DISABLED = {"ibkr", "schwab"}

# Key-gated services — auto-enable when the env var is set.
# If the env var is missing, ALL capabilities for that service are hidden.
# This covers API-key services AND OAuth services (need app credentials to function).
_KEY_GATED_SERVICES: dict[str, str] = {
    # API-key services
    "blandai": "BLANDAI_API_KEY",
    "twilio": "TWILIO_ACCOUNT_SID",
    "hyperbrowser": "HYPERBROWSER_API_KEY",
    "e2b": "E2B_API_KEY",
    "bitwarden": "BWS_ACCESS_TOKEN",
    # OAuth services — need app credentials to even start the flow
    "quickbooks": "QUICKBOOKS_CLIENT_ID",
    "hubspot": "HUBSPOT_CLIENT_ID",
    "google": "GOOGLE_CLIENT_ID",
    "gmail": "GOOGLE_CLIENT_ID",
    "google_drive": "GOOGLE_CLIENT_ID",
    "google_sheets": "GOOGLE_CLIENT_ID",
    "google_calendar": "GOOGLE_CLIENT_ID",
    "slack": "SLACK_CLIENT_ID",
    "stripe": "STRIPE_SECRET_KEY",
    "xero": "XERO_CLIENT_ID",
    "zoho_books": "ZOHO_BOOKS_CLIENT_ID",
    "billcom": "BILLCOM_CLIENT_ID",
    "netsuite": "NETSUITE_ACCOUNT_ID",
    "sage_intacct": "SAGE_INTACCT_CLIENT_ID",
    "gusto": "GUSTO_CLIENT_ID",
    "shopify": "SHOPIFY_CLIENT_ID",
    "square": "SQUARE_APPLICATION_ID",
    "docusign": "DOCUSIGN_INTEGRATION_KEY",
    "airtable": "AIRTABLE_CLIENT_ID",
    "microsoft": "MICROSOFT_CLIENT_ID",
    "microsoft_excel": "MICROSOFT_CLIENT_ID",
    "microsoft_onedrive": "MICROSOFT_CLIENT_ID",
    "microsoft_outlook_calendar": "MICROSOFT_CLIENT_ID",
    "powerbi": "MICROSOFT_CLIENT_ID",
    "notion": "NOTION_CLIENT_ID",
    "linear": "LINEAR_CLIENT_ID",
    "asana": "ASANA_CLIENT_ID",
    "clickup": "CLICKUP_CLIENT_ID",
    "monday": "MONDAY_CLIENT_ID",
    "dropbox": "DROPBOX_CLIENT_ID",
    "brex": "BREX_CLIENT_ID",
    "ramp": "RAMP_CLIENT_ID",
    "chase": "CHASE_CLIENT_ID",
    "mercury": "MERCURY_API_KEY",
    "recurly": "RECURLY_API_KEY",
    "plaid": "PLAID_CLIENT_ID",
}


def _build_disabled_services() -> set[str]:
    """Build disabled set: always-disabled + key-gated services missing their key."""
    disabled = set(_ALWAYS_DISABLED)
    for service, env_var in _KEY_GATED_SERVICES.items():
        if not os.getenv(env_var):
            disabled.add(service)
            logger.debug(
                f"Service '{service}' disabled (set {env_var} to enable)",
                service=service,
                env_var=env_var,
                log_event="service_disabled_no_key",
            )
    enabled_gated = [s for s in _KEY_GATED_SERVICES if s not in disabled]
    if enabled_gated:
        logger.info(
            f"Key-gated services enabled: {', '.join(sorted(enabled_gated))}",
            count=len(enabled_gated),
            log_event="key_gated_services_enabled",
        )
    logger.info(
        f"Services disabled: {len(disabled)} (always: {len(_ALWAYS_DISABLED)}, "
        f"missing keys: {len(disabled) - len(_ALWAYS_DISABLED)})",
        disabled_count=len(disabled),
        log_event="services_disabled_summary",
    )
    return disabled


DISABLED_SERVICES = _build_disabled_services()


def _filter_capabilities(capabilities: dict[str, Any]) -> dict[str, Any]:
    """Filter out capabilities from disabled services."""
    return {
        key: config
        for key, config in capabilities.items()
        if config.get("service") not in DISABLED_SERVICES
    }


# CAPABILITY REGISTRY
# This maps abstract capability keys to concrete tool implementations
# The Brain (MARS/Aletheia) sends capability_key, Stargate maps it to the right tool

ALL_CAPABILITIES = {
    **FINANCIAL_CAPABILITIES,
    **FINANCIAL_OPS_CAPABILITIES,
    **FCI_CAPABILITIES,
    **BANKING_CAPABILITIES,
    **PRODUCTIVITY_CAPABILITIES,
    **COMMUNICATION_CAPABILITIES,
    **TRADING_CAPABILITIES,
    **GOOGLE_MICROSOFT_CAPABILITIES,
    **UTILITIES_CAPABILITIES,
    **VAULT_CAPABILITIES,
}

# Apply production safety filter
CAPABILITY_REGISTRY = _filter_capabilities(ALL_CAPABILITIES)


def get_capability(capability_key: str) -> dict[str, Any] | None:
    """Get capability configuration by key"""
    return CAPABILITY_REGISTRY.get(capability_key)


def list_capabilities() -> dict[str, dict[str, Any]]:
    """List all available capabilities with schema availability indicator"""
    return {
        key: {
            "tool_name": config["tool_name"],
            "description": config["description"],
            "service": config["service"],
            "credential_type": config.get("credential_type", "customer"),
            "supports_delegation": config.get("supports_delegation", False),
            "requires_oauth": config["requires_oauth"],
            "schema_available": has_schema(key),
        }
        for key, config in CAPABILITY_REGISTRY.items()
    }


def get_capabilities_by_service(service: str) -> dict[str, dict[str, Any]]:
    """Get all capabilities for a specific service"""
    return {
        key: config for key, config in CAPABILITY_REGISTRY.items() if config["service"] == service
    }
