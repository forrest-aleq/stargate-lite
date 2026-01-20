"""
HubSpot Deal Capability Schemas.

Deal operations: create, get, list, update, delete, search.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ DEAL CREATE ============

DEAL_CREATE = CapabilitySchema(
    capability_key="crm.deal.create",
    service="hubspot",
    category="deals",
    description="Create a deal in HubSpot CRM",
    description_detailed=(
        "Creates a new deal record in HubSpot CRM. "
        "Deals represent potential revenue opportunities in your sales pipeline."
    ),
    parameters={
        "deal_name": ParameterSchema(
            type="string",
            required=True,
            description="Deal name/title",
            example="Enterprise Contract Q1",
        ),
        "amount": ParameterSchema(
            type="number",
            required=False,
            description="Deal value/amount",
            example=50000,
        ),
        "deal_stage": ParameterSchema(
            type="string",
            required=False,
            description="Pipeline stage",
            default="appointmentscheduled",
            example="qualifiedtobuy",
        ),
        "pipeline": ParameterSchema(
            type="string",
            required=False,
            description="Pipeline ID",
            default="default",
        ),
    },
    returns={
        "deal_id": ReturnFieldSchema(
            type="string",
            description="HubSpot deal ID (prefixed with hs:)",
            example="hs:789012",
        ),
        "deal_name": ReturnFieldSchema(type="string", description="Deal name"),
        "amount": ReturnFieldSchema(type="number", description="Deal amount"),
        "stage": ReturnFieldSchema(type="string", description="Current stage"),
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
            description="Invalid pipeline or stage",
            recovery_hint="Verify pipeline and stage names exist",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["crm.contact.create", "crm.company.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ DEAL GET ============

DEAL_GET = CapabilitySchema(
    capability_key="crm.deal.get",
    service="hubspot",
    category="deals",
    description="Get deal details from HubSpot CRM",
    description_detailed=("Retrieves details for a specific deal by ID."),
    parameters={
        "deal_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot deal ID (with or without hs: prefix)",
        ),
    },
    returns={
        "deal_id": ReturnFieldSchema(type="string", description="Deal ID"),
        "deal_name": ReturnFieldSchema(type="string", description="Deal name"),
        "amount": ReturnFieldSchema(type="number", description="Deal amount"),
        "stage": ReturnFieldSchema(type="string", description="Pipeline stage"),
        "close_date": ReturnFieldSchema(type="string", description="Expected close date"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Deal not found",
            recovery_hint="Verify deal ID is correct",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ DEAL LIST ============

DEAL_LIST = CapabilitySchema(
    capability_key="crm.deal.list",
    service="hubspot",
    category="deals",
    description="List deals from HubSpot CRM",
    description_detailed=("Retrieves a list of deals from HubSpot CRM."),
    parameters={
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of deals to return",
            default=100,
        ),
    },
    returns={
        "deals": ReturnFieldSchema(type="array", description="List of deal objects"),
        "count": ReturnFieldSchema(type="integer", description="Number of deals"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="HubSpot OAuth credentials not configured",
            recovery_hint="User must complete HubSpot OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["crm.deal.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ DEAL UPDATE ============

DEAL_UPDATE = CapabilitySchema(
    capability_key="crm.deal.update",
    service="hubspot",
    category="deals",
    description="Update a deal in HubSpot CRM",
    description_detailed=("Updates an existing deal's properties in HubSpot."),
    parameters={
        "deal_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot deal ID",
        ),
        "deal_name": ParameterSchema(
            type="string",
            required=False,
            description="Updated deal name",
        ),
        "amount": ParameterSchema(
            type="number",
            required=False,
            description="Updated deal amount",
        ),
        "deal_stage": ParameterSchema(
            type="string",
            required=False,
            description="Updated pipeline stage",
        ),
        "close_date": ParameterSchema(
            type="string",
            required=False,
            description="Updated close date (YYYY-MM-DD)",
        ),
    },
    returns={
        "deal_id": ReturnFieldSchema(type="string", description="Deal ID"),
        "deal_name": ReturnFieldSchema(type="string", description="Deal name"),
        "amount": ReturnFieldSchema(type="number", description="Amount"),
        "stage": ReturnFieldSchema(type="string", description="Stage"),
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
        typically_preceded_by=["crm.deal.get", "crm.deal.search"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ DEAL DELETE ============

DEAL_DELETE = CapabilitySchema(
    capability_key="crm.deal.delete",
    service="hubspot",
    category="deals",
    description="Delete a deal from HubSpot CRM",
    description_detailed=("Permanently deletes a deal from HubSpot."),
    parameters={
        "deal_id": ParameterSchema(
            type="string",
            required=True,
            description="HubSpot deal ID",
        ),
    },
    returns={
        "deal_id": ReturnFieldSchema(type="string", description="Deal ID"),
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

# ============ DEAL SEARCH ============

DEAL_SEARCH = CapabilitySchema(
    capability_key="crm.deal.search",
    service="hubspot",
    category="deals",
    description="Search deals in HubSpot CRM",
    description_detailed=("Searches for deals using HubSpot's search API."),
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
        "deals": ReturnFieldSchema(type="array", description="Matching deals"),
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
        typically_followed_by=["crm.deal.get", "crm.deal.update"],
    ),
    idempotent=True,
    has_side_effects=False,
)

HUBSPOT_DEAL_SCHEMAS: dict[str, CapabilitySchema] = {
    "crm.deal.create": DEAL_CREATE,
    "crm.deal.get": DEAL_GET,
    "crm.deal.list": DEAL_LIST,
    "crm.deal.update": DEAL_UPDATE,
    "crm.deal.delete": DEAL_DELETE,
    "crm.deal.search": DEAL_SEARCH,
}

__all__ = ["HUBSPOT_DEAL_SCHEMAS"]
