"""
Schema Registry for Enhanced Capability Metadata.

Provides a central registry for capability schemas and functions to query them.
"""

from typing import Any

# Import service-specific schemas
from app.schemas.airtable import AIRTABLE_SCHEMAS
from app.schemas.asana import ASANA_SCHEMAS
from app.schemas.base import CapabilitySchema
from app.schemas.billcom import BILLCOM_SCHEMAS
from app.schemas.brex import BREX_SCHEMAS
from app.schemas.chase import CHASE_SCHEMAS
from app.schemas.clickup import CLICKUP_SCHEMAS
from app.schemas.docusign import DOCUSIGN_SCHEMAS
from app.schemas.dropbox import DROPBOX_SCHEMAS
from app.schemas.excel import EXCEL_SCHEMAS
from app.schemas.fci import FCI_SCHEMAS
from app.schemas.gmail import GMAIL_SCHEMAS
from app.schemas.google_drive import GOOGLE_DRIVE_SCHEMAS
from app.schemas.gusto import GUSTO_SCHEMAS
from app.schemas.hubspot import HUBSPOT_SCHEMAS
from app.schemas.mercury import MERCURY_SCHEMAS
from app.schemas.monday import MONDAY_SCHEMAS
from app.schemas.netsuite import NETSUITE_SCHEMAS
from app.schemas.onedrive import ONEDRIVE_SCHEMAS
from app.schemas.outlook import OUTLOOK_SCHEMAS
from app.schemas.plaid import PLAID_SCHEMAS
from app.schemas.quickbooks import QUICKBOOKS_SCHEMAS
from app.schemas.sage_intacct import SAGE_INTACCT_SCHEMAS
from app.schemas.shopify import SHOPIFY_SCHEMAS
from app.schemas.slack import SLACK_SCHEMAS
from app.schemas.square import SQUARE_SCHEMAS
from app.schemas.stripe import STRIPE_SCHEMAS

# Central schema registry - maps capability_key to CapabilitySchema
SCHEMA_REGISTRY: dict[str, CapabilitySchema] = {
    # Accounting & ERP
    **QUICKBOOKS_SCHEMAS,
    **NETSUITE_SCHEMAS,
    **SAGE_INTACCT_SCHEMAS,
    # Payments & Billing
    **STRIPE_SCHEMAS,
    **BILLCOM_SCHEMAS,
    **SQUARE_SCHEMAS,
    # E-commerce
    **SHOPIFY_SCHEMAS,
    # HR & Payroll
    **GUSTO_SCHEMAS,
    # Banking
    **PLAID_SCHEMAS,
    **CHASE_SCHEMAS,
    **MERCURY_SCHEMAS,
    **BREX_SCHEMAS,
    # Communication
    **GMAIL_SCHEMAS,
    **SLACK_SCHEMAS,
    **OUTLOOK_SCHEMAS,
    # CRM
    **HUBSPOT_SCHEMAS,
    # File Storage
    **GOOGLE_DRIVE_SCHEMAS,
    **ONEDRIVE_SCHEMAS,
    **DROPBOX_SCHEMAS,
    **EXCEL_SCHEMAS,
    # Productivity
    **MONDAY_SCHEMAS,
    **CLICKUP_SCHEMAS,
    **ASANA_SCHEMAS,
    **AIRTABLE_SCHEMAS,
    # E-Signature
    **DOCUSIGN_SCHEMAS,
    # FCI (Financial Command Interface) - Direct API layer
    **FCI_SCHEMAS,
}


def get_schema(capability_key: str) -> CapabilitySchema | None:
    """Get schema for a specific capability.

    Args:
        capability_key: The capability key (e.g., 'vendor.create')

    Returns:
        CapabilitySchema if found, None otherwise
    """
    return SCHEMA_REGISTRY.get(capability_key)


def list_schemas(service: str | None = None) -> dict[str, CapabilitySchema]:
    """List all available schemas, optionally filtered by service.

    Args:
        service: Optional service name to filter by (e.g., 'quickbooks')

    Returns:
        Dict of capability_key -> CapabilitySchema
    """
    if service is None:
        return SCHEMA_REGISTRY.copy()

    return {key: schema for key, schema in SCHEMA_REGISTRY.items() if schema.service == service}


def has_schema(capability_key: str) -> bool:
    """Check if a capability has a schema defined.

    Args:
        capability_key: The capability key to check

    Returns:
        True if schema exists, False otherwise
    """
    return capability_key in SCHEMA_REGISTRY


def get_services_with_schemas() -> dict[str, dict[str, Any]]:
    """Get summary of services that have schemas defined.

    Returns:
        Dict of service_name -> {capabilities_count, categories}
    """
    services: dict[str, dict[str, Any]] = {}

    for schema in SCHEMA_REGISTRY.values():
        if schema.service not in services:
            services[schema.service] = {
                "capabilities_count": 0,
                "categories": set(),
            }

        services[schema.service]["capabilities_count"] += 1
        if schema.category:
            services[schema.service]["categories"].add(schema.category)

    # Convert sets to lists for JSON serialization
    for service_info in services.values():
        service_info["categories"] = sorted(service_info["categories"])

    return services


__all__ = [
    "SCHEMA_REGISTRY",
    "CapabilitySchema",
    "get_schema",
    "get_services_with_schemas",
    "has_schema",
    "list_schemas",
]
