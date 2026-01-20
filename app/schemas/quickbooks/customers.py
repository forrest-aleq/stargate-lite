"""
QuickBooks Customer Capability Schemas.

Rich metadata for customer operations enabling AI agents to use these capabilities effectively.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    UsageExample,
    WorkflowHints,
)

CUSTOMER_CREATE = CapabilitySchema(
    capability_key="qb.customer.create",
    service="quickbooks",
    category="customers",
    description="Create a customer in QuickBooks",
    description_detailed=(
        "Creates a new customer record in QuickBooks Online. Customers are individuals or "
        "businesses who purchase goods or services from you. The customer_id returned can be "
        "used in invoice.create and payment.create. Customer names should be unique."
    ),
    parameters={
        "customer_name": ParameterSchema(
            type="string",
            required=True,
            description="Display name for the customer (should be unique)",
            example="Acme Corporation",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Primary contact email address",
            example="billing@acme-corp.com",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Primary phone number",
            example="(555) 123-4567",
        ),
        "company_name": ParameterSchema(
            type="string",
            required=False,
            description="Company/business name (if different from display name)",
            example="Acme Corporation Inc.",
        ),
        "billing_address": ParameterSchema(
            type="object",
            required=False,
            description="Billing address with Line1, City, CountrySubDivisionCode, PostalCode",
            example={
                "Line1": "123 Main St",
                "City": "San Francisco",
                "CountrySubDivisionCode": "CA",
                "PostalCode": "94102",
            },
        ),
        "shipping_address": ParameterSchema(
            type="object",
            required=False,
            description="Shipping address (same structure as billing_address)",
        ),
    },
    returns={
        "customer_id": ReturnFieldSchema(
            type="string",
            description="QuickBooks customer ID with 'qb:' prefix",
            example="qb:123",
        ),
        "display_name": ReturnFieldSchema(
            type="string",
            description="Customer display name as stored",
            example="Acme Corporation",
        ),
        "email": ReturnFieldSchema(
            type="string",
            description="Email address if provided",
        ),
        "balance": ReturnFieldSchema(
            type="number",
            description="Current balance (0 for new customers)",
            example=0,
        ),
        "created_at": ReturnFieldSchema(
            type="string",
            description="ISO timestamp when customer was created",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Duplicate customer name or invalid field",
            recovery_hint="Use qb.customer.search to check if customer exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.customer.search"],
        typically_followed_by=["invoice.create", "estimate.create"],
        related_capabilities=["qb.customer.update", "qb.customer.list"],
    ),
    examples=[
        UsageExample(
            description="Create a new business customer",
            args={
                "customer_name": "Tech Startup LLC",
                "email": "accounts@techstartup.io",
                "phone": "(415) 555-0100",
            },
            expected_output={
                "customer_id": "qb:456",
                "display_name": "Tech Startup LLC",
                "email": "accounts@techstartup.io",
                "balance": 0,
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

CUSTOMER_GET = CapabilitySchema(
    capability_key="qb.customer.get",
    service="quickbooks",
    category="customers",
    description="Get customer details from QuickBooks",
    description_detailed=(
        "Retrieves detailed information about a specific customer including contact info, "
        "current balance, and status. Use this to verify customer details before creating "
        "invoices or to check outstanding balances."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="QuickBooks customer ID (with 'qb:' prefix)",
            example="qb:123",
        ),
    },
    returns={
        "customer_id": ReturnFieldSchema(type="string", description="Customer ID"),
        "display_name": ReturnFieldSchema(type="string", description="Display name"),
        "email": ReturnFieldSchema(type="string", description="Email address"),
        "phone": ReturnFieldSchema(type="string", description="Phone number"),
        "balance": ReturnFieldSchema(
            type="number",
            description="Current outstanding balance",
            example=1500.00,
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="'active' or 'inactive'",
            example="active",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Customer not found",
            recovery_hint="Verify customer_id with qb.customer.search",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.customer.search", "qb.customer.list"],
        typically_followed_by=["invoice.create", "qb.customer.update"],
        related_capabilities=["qb.customer.list", "invoice.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

CUSTOMER_UPDATE = CapabilitySchema(
    capability_key="qb.customer.update",
    service="quickbooks",
    category="customers",
    description="Update a customer in QuickBooks",
    description_detailed=(
        "Updates an existing customer's information. Only provided fields are updated; "
        "omitted fields retain current values. Automatically handles SyncToken."
    ),
    parameters={
        "customer_id": ParameterSchema(
            type="string",
            required=True,
            description="Customer ID to update",
            example="qb:123",
        ),
        "customer_name": ParameterSchema(
            type="string",
            required=False,
            description="New display name",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="New email address",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="New phone number",
        ),
    },
    returns={
        "customer_id": ReturnFieldSchema(type="string", description="Customer ID"),
        "display_name": ReturnFieldSchema(type="string", description="Updated name"),
        "updated": ReturnFieldSchema(type="boolean", description="True if successful"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Duplicate name or invalid value",
            recovery_hint="Ensure customer_name is unique",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["qb.customer.get"],
        typically_followed_by=["qb.customer.get"],
        related_capabilities=["qb.customer.get", "qb.customer.search"],
    ),
    idempotent=False,
    has_side_effects=True,
)

CUSTOMER_LIST = CapabilitySchema(
    capability_key="qb.customer.list",
    service="quickbooks",
    category="customers",
    description="List customers from QuickBooks",
    description_detailed=(
        "Returns a paginated list of customers. Use for bulk retrieval or browsing. "
        "For finding a specific customer by name, use qb.customer.search instead."
    ),
    parameters={
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return active customers",
            default=False,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results (1-1000)",
            default=100,
        ),
    },
    returns={
        "customers": ReturnFieldSchema(
            type="array",
            description="List of customer objects",
            items_type="object",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number returned"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["qb.customer.get", "invoice.create"],
        related_capabilities=["qb.customer.search", "qb.customer.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

CUSTOMER_SEARCH = CapabilitySchema(
    capability_key="qb.customer.search",
    service="quickbooks",
    category="customers",
    description="Search customers by name with fuzzy matching",
    description_detailed=(
        "Searches for customers using LIKE matching on display name. Use before "
        "qb.customer.create to check for duplicates or to find customers by partial name."
    ),
    parameters={
        "search_term": ParameterSchema(
            type="string",
            required=True,
            description="Search term to match against customer names",
            example="Acme",
        ),
        "max_results": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results to return",
            default=25,
        ),
    },
    returns={
        "customers": ReturnFieldSchema(
            type="array",
            description="Matching customers",
            items_type="object",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of matches"),
        "search_term": ReturnFieldSchema(type="string", description="Term used"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["qb.customer.create", "qb.customer.get", "invoice.create"],
        related_capabilities=["qb.customer.list", "qb.customer.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# Aliases for MARS compatibility
CUSTOMER_CREATE_ALIAS = CapabilitySchema(
    capability_key="customer.create",
    service="quickbooks",
    category="customers",
    description="Create a customer in QuickBooks (MARS alias)",
    description_detailed=CUSTOMER_CREATE.description_detailed,
    parameters=CUSTOMER_CREATE.parameters,
    returns=CUSTOMER_CREATE.returns,
    errors=CUSTOMER_CREATE.errors,
    workflow=CUSTOMER_CREATE.workflow,
    idempotent=False,
    has_side_effects=True,
)

CUSTOMER_GET_ALIAS = CapabilitySchema(
    capability_key="customer.get",
    service="quickbooks",
    category="customers",
    description="Get customer details from QuickBooks (MARS alias)",
    description_detailed=CUSTOMER_GET.description_detailed,
    parameters=CUSTOMER_GET.parameters,
    returns=CUSTOMER_GET.returns,
    errors=CUSTOMER_GET.errors,
    workflow=CUSTOMER_GET.workflow,
    idempotent=True,
    has_side_effects=False,
)

CUSTOMER_UPDATE_ALIAS = CapabilitySchema(
    capability_key="customer.update",
    service="quickbooks",
    category="customers",
    description="Update a customer in QuickBooks (MARS alias)",
    description_detailed=CUSTOMER_UPDATE.description_detailed,
    parameters=CUSTOMER_UPDATE.parameters,
    returns=CUSTOMER_UPDATE.returns,
    errors=CUSTOMER_UPDATE.errors,
    workflow=CUSTOMER_UPDATE.workflow,
    idempotent=False,
    has_side_effects=True,
)

CUSTOMER_LIST_ALIAS = CapabilitySchema(
    capability_key="customer.list",
    service="quickbooks",
    category="customers",
    description="List customers from QuickBooks (MARS alias)",
    description_detailed=CUSTOMER_LIST.description_detailed,
    parameters=CUSTOMER_LIST.parameters,
    returns=CUSTOMER_LIST.returns,
    errors=CUSTOMER_LIST.errors,
    workflow=CUSTOMER_LIST.workflow,
    idempotent=True,
    has_side_effects=False,
)

CUSTOMER_SCHEMAS: dict[str, CapabilitySchema] = {
    "qb.customer.create": CUSTOMER_CREATE,
    "qb.customer.get": CUSTOMER_GET,
    "qb.customer.update": CUSTOMER_UPDATE,
    "qb.customer.list": CUSTOMER_LIST,
    "qb.customer.search": CUSTOMER_SEARCH,
    "customer.create": CUSTOMER_CREATE_ALIAS,
    "customer.get": CUSTOMER_GET_ALIAS,
    "customer.update": CUSTOMER_UPDATE_ALIAS,
    "customer.list": CUSTOMER_LIST_ALIAS,
}
