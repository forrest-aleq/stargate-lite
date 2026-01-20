"""
FCI Entity Lookup Schemas.

These handle entity resolution across services:
- @customer:name - Find customer across QB, Stripe, Recurly, etc.
- @vendor:name - Find vendor across QB, Bill.com, NetSuite, etc.
- @invoice:id - Find invoice by ID across systems

Entity lookups MAY require fuzzy matching (Layer 2) but simple exact
lookups can be direct (Layer 1). The schema supports both modes.
"""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
)

# =============================================================================
# @customer:name - Cross-service customer lookup
# =============================================================================
FCI_CUSTOMER_LOOKUP = CapabilitySchema(
    capability_key="fci.customer.lookup",
    service="fci",
    category="entities",
    description="Look up a customer across all connected services",
    description_detailed="""
    Searches for a customer by name or ID across:
    - QuickBooks
    - Stripe
    - Recurly
    - Shopify
    - HubSpot

    Returns matches from each service with confidence scores.
    For fuzzy matching, routes through Baby Mars orchestration.
    Maps to FCI primitive: @customer:name
    """,
    parameters={
        "name": ParameterSchema(
            type="string",
            required=False,
            description="Customer name to search (supports partial/fuzzy)",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Customer email (exact match preferred)",
        ),
        "id": ParameterSchema(
            type="string",
            required=False,
            description="Customer ID with service prefix (e.g., 'qb:123', 'stripe:cus_xxx')",
        ),
        "services": ParameterSchema(
            type="array",
            required=False,
            description="Limit search to specific services",
            items_type="string",
        ),
        "fuzzy": ParameterSchema(
            type="boolean",
            required=False,
            description="Enable fuzzy name matching (requires orchestration)",
            default=False,
        ),
    },
    returns={
        "matches": ReturnFieldSchema(
            type="array",
            description="All matches: {service, id, name, email, confidence}",
        ),
        "primary": ReturnFieldSchema(
            type="object",
            description="Best match: {service, id, name, email, balance, last_activity}",
        ),
        "match_count": ReturnFieldSchema(
            type="integer",
            description="Number of matches found",
        ),
    },
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @vendor:name - Cross-service vendor lookup
# =============================================================================
FCI_VENDOR_LOOKUP = CapabilitySchema(
    capability_key="fci.vendor.lookup",
    service="fci",
    category="entities",
    description="Look up a vendor across all connected services",
    description_detailed="""
    Searches for a vendor by name or ID across:
    - QuickBooks
    - Bill.com
    - NetSuite
    - Xero
    - Sage Intacct

    Returns matches from each service with confidence scores.
    For fuzzy matching, routes through Baby Mars orchestration.
    Maps to FCI primitive: @vendor:name
    """,
    parameters={
        "name": ParameterSchema(
            type="string",
            required=False,
            description="Vendor name to search (supports partial/fuzzy)",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Vendor email (exact match preferred)",
        ),
        "id": ParameterSchema(
            type="string",
            required=False,
            description="Vendor ID with service prefix (e.g., 'qb:123', 'billcom:xxx')",
        ),
        "services": ParameterSchema(
            type="array",
            required=False,
            description="Limit search to specific services",
            items_type="string",
        ),
        "fuzzy": ParameterSchema(
            type="boolean",
            required=False,
            description="Enable fuzzy name matching (requires orchestration)",
            default=False,
        ),
    },
    returns={
        "matches": ReturnFieldSchema(
            type="array",
            description="All matches: {service, id, name, email, confidence}",
        ),
        "primary": ReturnFieldSchema(
            type="object",
            description="Best match with full details: {service, id, name, balance, last_payment}",
        ),
        "match_count": ReturnFieldSchema(
            type="integer",
            description="Number of matches found",
        ),
    },
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# @invoice:id - Cross-service invoice lookup
# =============================================================================
FCI_INVOICE_LOOKUP = CapabilitySchema(
    capability_key="fci.invoice.lookup",
    service="fci",
    category="entities",
    description="Look up an invoice across all connected services",
    description_detailed="""
    Searches for an invoice by number or ID across:
    - QuickBooks
    - Stripe
    - Recurly
    - Xero
    - NetSuite

    Can search by invoice number (customer-facing) or internal ID.
    Maps to FCI primitive: @invoice:id
    """,
    parameters={
        "invoice_number": ParameterSchema(
            type="string",
            required=False,
            description="Customer-facing invoice number",
        ),
        "id": ParameterSchema(
            type="string",
            required=False,
            description="Internal invoice ID with service prefix",
        ),
        "customer_name": ParameterSchema(
            type="string",
            required=False,
            description="Filter by customer name (narrows search)",
        ),
        "services": ParameterSchema(
            type="array",
            required=False,
            description="Limit search to specific services",
            items_type="string",
        ),
    },
    returns={
        "matches": ReturnFieldSchema(
            type="array",
            description="All matches: {service, id, number, customer, amount, status}",
        ),
        "primary": ReturnFieldSchema(
            type="object",
            description="Best match with full details",
        ),
        "match_count": ReturnFieldSchema(
            type="integer",
            description="Number of matches found",
        ),
    },
    idempotent=True,
    has_side_effects=False,
)

# =============================================================================
# Registry of all FCI entity schemas
# =============================================================================
FCI_ENTITY_SCHEMAS = {
    "fci.customer.lookup": FCI_CUSTOMER_LOOKUP,
    "fci.vendor.lookup": FCI_VENDOR_LOOKUP,
    "fci.invoice.lookup": FCI_INVOICE_LOOKUP,
}
