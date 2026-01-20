"""
HubSpot Contact Capability Schemas.

Contact operations: create, get, list, update, delete, search.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ CONTACT CREATE ============

CONTACT_CREATE = CapabilitySchema(
    capability_key="crm.contact.create",
    service="hubspot",
    category="contacts",
    description="Create a contact in HubSpot CRM",
    description_detailed=(
        "Creates a new contact record in HubSpot CRM. "
        "Contacts represent individual people you interact with."
    ),
    parameters={
        "email": ParameterSchema(
            type="string",
            required=True,
            description="Contact email address (must be unique)",
            example="john@example.com",
        ),
        "first_name": ParameterSchema(
            type="string",
            required=False,
            description="Contact first name",
            example="John",
        ),
        "last_name": ParameterSchema(
            type="string",
            required=False,
            description="Contact last name",
            example="Doe",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Contact phone number",
        ),
        "company": ParameterSchema(
            type="string",
            required=False,
            description="Company name",
        ),
    },
    returns={
        "contact_id": ReturnFieldSchema(
            type="string",
            description="HubSpot contact ID (prefixed with hs:)",
            example="hs:123456",
        ),
        "email": ReturnFieldSchema(type="string", description="Contact email"),
        "first_name": ReturnFieldSchema(type="string", description="First name"),
        "last_name": ReturnFieldSchema(type="string", description="Last name"),
        "created_at": ReturnFieldSchema(type="string", description="Creation timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Contact with email already exists",
            recovery_hint="Use crm.contact.get to find existing contact",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["crm.deal.create", "crm.contact.get"],
        related_capabilities=["crm.company.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ CONTACT GET ============

CONTACT_GET = CapabilitySchema(
    capability_key="crm.contact.get",
    service="hubspot",
    category="contacts",
    description="Get contact details from HubSpot CRM",
    description_detailed=("Retrieves details for a specific contact by ID."),
    parameters={
        "contact_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot contact ID (with or without hs: prefix)",
            example="hs:123456",
        ),
    },
    returns={
        "contact_id": ReturnFieldSchema(type="string", description="Contact ID"),
        "email": ReturnFieldSchema(type="string", description="Email address"),
        "first_name": ReturnFieldSchema(type="string", description="First name"),
        "last_name": ReturnFieldSchema(type="string", description="Last name"),
        "company": ReturnFieldSchema(type="string", description="Company name"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Contact not found",
            recovery_hint="Verify contact ID is correct",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ CONTACT LIST ============

CONTACT_LIST = CapabilitySchema(
    capability_key="crm.contact.list",
    service="hubspot",
    category="contacts",
    description="List contacts from HubSpot CRM",
    description_detailed=("Retrieves a list of contacts from HubSpot CRM."),
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of contacts to return",
            default=100,
        ),
    },
    returns={
        "contacts": ReturnFieldSchema(
            type="array",
            description="List of contact objects",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of contacts"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["crm.contact.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ CONTACT UPDATE ============

CONTACT_UPDATE = CapabilitySchema(
    capability_key="crm.contact.update",
    service="hubspot",
    category="contacts",
    description="Update a contact in HubSpot CRM",
    description_detailed=("Updates an existing contact's properties in HubSpot."),
    parameters={
        "contact_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot contact ID (with or without hs: prefix)",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Updated email address",
        ),
        "first_name": ParameterSchema(
            type="string",
            required=False,
            description="Updated first name",
        ),
        "last_name": ParameterSchema(
            type="string",
            required=False,
            description="Updated last name",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Updated phone number",
        ),
        "company": ParameterSchema(
            type="string",
            required=False,
            description="Updated company name",
        ),
    },
    returns={
        "contact_id": ReturnFieldSchema(type="string", description="Contact ID"),
        "email": ReturnFieldSchema(type="string", description="Email"),
        "first_name": ReturnFieldSchema(type="string", description="First name"),
        "last_name": ReturnFieldSchema(type="string", description="Last name"),
        "updated_at": ReturnFieldSchema(type="string", description="Update timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Contact not found",
            recovery_hint="Verify contact ID is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["crm.contact.get", "crm.contact.search"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ CONTACT DELETE ============

CONTACT_DELETE = CapabilitySchema(
    capability_key="crm.contact.delete",
    service="hubspot",
    category="contacts",
    description="Delete a contact from HubSpot CRM",
    description_detailed=("Permanently deletes a contact from HubSpot."),
    parameters={
        "contact_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot contact ID (with or without hs: prefix)",
        ),
    },
    returns={
        "contact_id": ReturnFieldSchema(type="string", description="Contact ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'deleted'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

# ============ CONTACT SEARCH ============

CONTACT_SEARCH = CapabilitySchema(
    capability_key="crm.contact.search",
    service="hubspot",
    category="contacts",
    description="Search contacts in HubSpot CRM",
    description_detailed=(
        "Searches for contacts using HubSpot's search API. "
        "Supports full-text search across contact properties."
    ),
    parameters={
        "query": ParameterSchema(
            type="string",
            required=True,
            description="Search query string",
            example="john@example.com",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of results",
            default=10,
        ),
    },
    returns={
        "query": ReturnFieldSchema(type="string", description="Search query used"),
        "contacts": ReturnFieldSchema(type="array", description="Matching contacts"),
        "count": ReturnFieldSchema(type="integer", description="Number of results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["crm.contact.get", "crm.contact.update"],
    ),
    idempotent=True,
    has_side_effects=False,
)

HUBSPOT_CONTACT_SCHEMAS: dict[str, CapabilitySchema] = {
    "crm.contact.create": CONTACT_CREATE,
    "crm.contact.get": CONTACT_GET,
    "crm.contact.list": CONTACT_LIST,
    "crm.contact.update": CONTACT_UPDATE,
    "crm.contact.delete": CONTACT_DELETE,
    "crm.contact.search": CONTACT_SEARCH,
}

__all__ = ["HUBSPOT_CONTACT_SCHEMAS"]
