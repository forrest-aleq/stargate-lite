"""
Tool Registry for Stargate Lite
Maps capability keys to actual tool implementations
Updated February 2026 - 34 SERVICES + Cognitive Utilities + Financial Ops - 711 CAPABILITIES
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
from app.schemas import has_schema

logger = get_logger(__name__)

# =============================================================================
# PRODUCTION SAFETY: DISABLED SERVICES
# =============================================================================
# Always disabled — trading operations are HIGH RISK
_ALWAYS_DISABLED = {"ibkr", "schwab"}

# Key-gated services — auto-enable when the env var is set
_KEY_GATED_SERVICES: dict[str, str] = {
    "blandai": "BLANDAI_API_KEY",
    "twilio": "TWILIO_ACCOUNT_SID",
    "hyperbrowser": "HYPERBROWSER_API_KEY",
}


def _build_disabled_services() -> set[str]:
    """Build disabled set: always-disabled + key-gated services missing their key."""
    disabled = set(_ALWAYS_DISABLED)
    for service, env_var in _KEY_GATED_SERVICES.items():
        if not os.getenv(env_var):
            disabled.add(service)
            logger.info(
                f"Service '{service}' disabled (set {env_var} to enable)",
                service=service,
                env_var=env_var,
                log_event="service_disabled_no_key",
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

_ALL_CAPABILITIES = {
    **FINANCIAL_CAPABILITIES,
    **FINANCIAL_OPS_CAPABILITIES,
    **FCI_CAPABILITIES,
    **BANKING_CAPABILITIES,
    **PRODUCTIVITY_CAPABILITIES,
    **COMMUNICATION_CAPABILITIES,
    **TRADING_CAPABILITIES,
    **GOOGLE_MICROSOFT_CAPABILITIES,
    **UTILITIES_CAPABILITIES,
}

# Apply production safety filter
CAPABILITY_REGISTRY = _filter_capabilities(_ALL_CAPABILITIES)


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
