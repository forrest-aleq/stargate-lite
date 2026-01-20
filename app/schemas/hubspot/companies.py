"""
HubSpot Company Capability Schemas.

Company operations: create, get, list, update, delete, search.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ COMPANY CREATE ============

COMPANY_CREATE = CapabilitySchema(
    capability_key="crm.company.create",
    service="hubspot",
    category="companies",
    description="Create a company in HubSpot CRM",
    description_detailed=(
        "Creates a new company record in HubSpot CRM. "
        "Companies represent organizations you do business with."
    ),
    parameters={
        "company_name": ParameterSchema(
            type="string",
            required=True,
            description="Company name",
            example="Acme Corporation",
        ),
        "domain": ParameterSchema(
            type="string",
            required=False,
            description="Company website domain",
            example="acme.com",
        ),
        "industry": ParameterSchema(
            type="string",
            required=False,
            description="Industry category",
            example="Technology",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Company phone number",
        ),
    },
    returns={
        "company_id": ReturnFieldSchema(
            type="string",
            description="HubSpot company ID (prefixed with hs:)",
            example="hs:456789",
        ),
        "company_name": ReturnFieldSchema(type="string", description="Company name"),
        "domain": ReturnFieldSchema(type="string", description="Website domain"),
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
            description="Company with domain already exists",
            recovery_hint="Check for existing company with same domain",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["crm.contact.create", "crm.deal.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ COMPANY GET ============

COMPANY_GET = CapabilitySchema(
    capability_key="crm.company.get",
    service="hubspot",
    category="companies",
    description="Get company details from HubSpot CRM",
    description_detailed=("Retrieves details for a specific company by ID."),
    parameters={
        "company_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot company ID (with or without hs: prefix)",
        ),
    },
    returns={
        "company_id": ReturnFieldSchema(type="string", description="Company ID"),
        "company_name": ReturnFieldSchema(type="string", description="Company name"),
        "domain": ReturnFieldSchema(type="string", description="Website domain"),
        "industry": ReturnFieldSchema(type="string", description="Industry"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Company not found",
            recovery_hint="Verify company ID is correct",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ COMPANY LIST ============

COMPANY_LIST = CapabilitySchema(
    capability_key="crm.company.list",
    service="hubspot",
    category="companies",
    description="List companies from HubSpot CRM",
    description_detailed=("Retrieves a list of companies from HubSpot CRM."),
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of companies to return",
            default=100,
        ),
    },
    returns={
        "companies": ReturnFieldSchema(type="array", description="List of company objects"),
        "count": ReturnFieldSchema(type="integer", description="Number of companies"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["crm.company.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ COMPANY UPDATE ============

COMPANY_UPDATE = CapabilitySchema(
    capability_key="crm.company.update",
    service="hubspot",
    category="companies",
    description="Update a company in HubSpot CRM",
    description_detailed=("Updates an existing company's properties in HubSpot."),
    parameters={
        "company_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot company ID",
        ),
        "company_name": ParameterSchema(
            type="string",
            required=False,
            description="Updated company name",
        ),
        "domain": ParameterSchema(
            type="string",
            required=False,
            description="Updated website domain",
        ),
        "industry": ParameterSchema(
            type="string",
            required=False,
            description="Updated industry",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Updated phone number",
        ),
    },
    returns={
        "company_id": ReturnFieldSchema(type="string", description="Company ID"),
        "company_name": ReturnFieldSchema(type="string", description="Company name"),
        "domain": ReturnFieldSchema(type="string", description="Domain"),
        "updated_at": ReturnFieldSchema(type="string", description="Update timestamp"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["crm.company.get", "crm.company.search"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ COMPANY DELETE ============

COMPANY_DELETE = CapabilitySchema(
    capability_key="crm.company.delete",
    service="hubspot",
    category="companies",
    description="Delete a company from HubSpot CRM",
    description_detailed=("Permanently deletes a company from HubSpot."),
    parameters={
        "company_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot company ID",
        ),
    },
    returns={
        "company_id": ReturnFieldSchema(type="string", description="Company ID"),
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

# ============ COMPANY SEARCH ============

COMPANY_SEARCH = CapabilitySchema(
    capability_key="crm.company.search",
    service="hubspot",
    category="companies",
    description="Search companies in HubSpot CRM",
    description_detailed=("Searches for companies using HubSpot's search API."),
    parameters={
        "query": ParameterSchema(
            type="string",
            required=True,
            description="Search query string",
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
        "companies": ReturnFieldSchema(type="array", description="Matching companies"),
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
        typically_followed_by=["crm.company.get", "crm.company.update"],
    ),
    idempotent=True,
    has_side_effects=False,
)

HUBSPOT_COMPANY_SCHEMAS: dict[str, CapabilitySchema] = {
    "crm.company.create": COMPANY_CREATE,
    "crm.company.get": COMPANY_GET,
    "crm.company.list": COMPANY_LIST,
    "crm.company.update": COMPANY_UPDATE,
    "crm.company.delete": COMPANY_DELETE,
    "crm.company.search": COMPANY_SEARCH,
}

__all__ = ["HUBSPOT_COMPANY_SCHEMAS"]
