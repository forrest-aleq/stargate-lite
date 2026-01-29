"""
QuickBooks Vendor Capability Schemas.

Rich metadata for vendor operations enabling AI agents to use these capabilities effectively.
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

VENDOR_CREATE = CapabilitySchema(
    capability_key="vendor.create",
    service="quickbooks",
    category="vendors",
    description="Create a vendor in QuickBooks",
    description_detailed=(
        "Creates a new vendor record in QuickBooks Online. Vendors are companies or "
        "individuals you pay (suppliers, contractors, service providers). The vendor_id "
        "returned can be used in bill.create to record money owed. Vendor names must be "
        "unique within QuickBooks - use vendor.search first to check for duplicates."
    ),
    parameters={
        "vendor_name": ParameterSchema(
            type="string",
            required=True,
            description="Display name for the vendor (must be unique in QuickBooks)",
            example="Acme Supply Co.",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Primary contact email address",
            example="accounting@acme-supply.com",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Primary phone number (free-form format)",
            example="(555) 123-4567",
        ),
        "website": ParameterSchema(
            type="string",
            required=False,
            description="Vendor website URL",
            example="https://www.acme-supply.com",
        ),
        "billing_address": ParameterSchema(
            type="object",
            required=False,
            description="Billing address with Line1, City, State, PostalCode",
            example={
                "Line1": "123 Main St",
                "City": "San Francisco",
                "CountrySubDivisionCode": "CA",
                "PostalCode": "94102",
            },
        ),
    },
    returns={
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="QuickBooks vendor ID prefixed with 'qb:'",
            example="qb:123",
        ),
        "display_name": ReturnFieldSchema(
            type="string",
            description="Confirmed display name as stored in QuickBooks",
            example="Acme Supply Co.",
        ),
        "email": ReturnFieldSchema(
            type="string",
            description="Email address if provided",
            example="accounting@acme-supply.com",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Vendor status ('active' or 'inactive')",
            example="active",
        ),
        "created_at": ReturnFieldSchema(
            type="string",
            description="ISO timestamp when vendor was created",
            example="2025-01-15T10:30:00Z",
        ),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this vendor in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/vendordetail?nameId=123",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow at /oauth/quickbooks/authorize",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Duplicate vendor name or missing required field",
            recovery_hint="Use vendor.search first to check if vendor already exists",
        ),
        ErrorHint(
            error_code=ErrorCode.RATE_LIMIT,
            description="QuickBooks API rate limit exceeded",
            recovery_hint="Retry after exponential backoff (typically 60 seconds)",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["vendor.search"],
        typically_followed_by=["bill.create", "vendor.get"],
        related_capabilities=["vendor.update", "vendor.list"],
    ),
    examples=[
        UsageExample(
            description="Create a basic vendor with name and email",
            args={"vendor_name": "Office Depot", "email": "orders@officedepot.com"},
            expected_output={
                "vendor_id": "qb:456",
                "display_name": "Office Depot",
                "email": "orders@officedepot.com",
                "status": "active",
                "deep_link": "https://app.qbo.intuit.com/app/vendordetail?nameId=456",
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

VENDOR_GET = CapabilitySchema(
    capability_key="vendor.get",
    service="quickbooks",
    category="vendors",
    description="Get vendor details from QuickBooks",
    description_detailed=(
        "Retrieves detailed information about a specific vendor by ID. Use this to "
        "get current contact information, status, and other vendor details. The vendor_id "
        "should include the 'qb:' prefix (e.g., 'qb:123')."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="QuickBooks vendor ID (with 'qb:' prefix)",
            example="qb:123",
        ),
    },
    returns={
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="QuickBooks vendor ID with 'qb:' prefix",
            example="qb:123",
        ),
        "display_name": ReturnFieldSchema(
            type="string",
            description="Vendor display name",
            example="Acme Supply Co.",
        ),
        "email": ReturnFieldSchema(
            type="string",
            description="Primary email address",
            example="accounting@acme-supply.com",
        ),
        "phone": ReturnFieldSchema(
            type="string",
            description="Primary phone number",
            example="(555) 123-4567",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Vendor status ('active' or 'inactive')",
            example="active",
        ),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this vendor in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/vendordetail?nameId=123",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Vendor not found with given ID",
            recovery_hint="Verify vendor_id is correct using vendor.search or vendor.list",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["vendor.search", "vendor.list", "vendor.create"],
        typically_followed_by=["vendor.update", "bill.create"],
        related_capabilities=["vendor.list", "vendor.search"],
    ),
    idempotent=True,
    has_side_effects=False,
)

VENDOR_LIST = CapabilitySchema(
    capability_key="vendor.list",
    service="quickbooks",
    category="vendors",
    description="List vendors from QuickBooks",
    description_detailed=(
        "Returns a paginated list of vendors from QuickBooks. By default returns only "
        "active vendors. Use this for bulk retrieval or when you need to see all vendors. "
        "For finding a specific vendor by name, use vendor.search instead."
    ),
    parameters={
        "max_results": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of vendors to return (1-1000)",
            default=100,
            example=50,
        ),
        "start_position": ParameterSchema(
            type="integer",
            required=False,
            description="Starting position for pagination (1-based)",
            default=1,
            example=1,
        ),
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="If true, only return active vendors",
            default=True,
            example=True,
        ),
    },
    returns={
        "vendors": ReturnFieldSchema(
            type="array",
            description="List of vendor objects (each includes deep_link URL to QBO)",
            items_type="object",
            example=[
                {
                    "vendor_id": "qb:123",
                    "display_name": "Acme Supply",
                    "status": "active",
                    "deep_link": "https://app.qbo.intuit.com/app/vendordetail?nameId=123",
                },
            ],
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of vendors returned in this response",
            example=25,
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["vendor.get", "bill.create"],
        related_capabilities=["vendor.search", "vendor.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

VENDOR_SEARCH = CapabilitySchema(
    capability_key="vendor.search",
    service="quickbooks",
    category="vendors",
    description="Search vendors by name with fuzzy matching",
    description_detailed=(
        "Searches for vendors by name using fuzzy (LIKE) matching. Use this before "
        "vendor.create to check if a vendor already exists and avoid duplicates. "
        "Also useful for finding vendors when you only have a partial name."
    ),
    parameters={
        "search_term": ParameterSchema(
            type="string",
            required=True,
            description="Search term to match against vendor display names",
            example="Acme",
        ),
        "max_results": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number of results to return",
            default=25,
            example=10,
        ),
    },
    returns={
        "vendors": ReturnFieldSchema(
            type="array",
            description="List of matching vendor objects (each includes deep_link URL to QBO)",
            items_type="object",
            example=[
                {
                    "vendor_id": "qb:123",
                    "display_name": "Acme Supply Co.",
                    "status": "active",
                    "deep_link": "https://app.qbo.intuit.com/app/vendordetail?nameId=123",
                },
            ],
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of vendors matching the search",
            example=3,
        ),
        "search_term": ReturnFieldSchema(
            type="string",
            description="The search term that was used",
            example="Acme",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected for this user/org",
            recovery_hint="User must complete QuickBooks OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["vendor.create", "vendor.get", "bill.create"],
        related_capabilities=["vendor.list", "vendor.get", "vendor.create"],
    ),
    examples=[
        UsageExample(
            description="Search for vendors containing 'Office' in their name",
            args={"search_term": "Office", "max_results": 10},
            expected_output={
                "vendors": [
                    {"vendor_id": "qb:456", "display_name": "Office Depot", "status": "active"},
                    {"vendor_id": "qb:789", "display_name": "Office Max", "status": "active"},
                ],
                "count": 2,
                "search_term": "Office",
            },
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

VENDOR_UPDATE = CapabilitySchema(
    capability_key="vendor.update",
    service="quickbooks",
    category="vendors",
    description="Update vendor details",
    description_detailed=(
        "Updates an existing vendor's information in QuickBooks. Only the fields "
        "provided will be updated - omitted fields retain their current values. "
        "QuickBooks requires the current SyncToken which is fetched automatically."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="QuickBooks vendor ID (with 'qb:' prefix)",
            example="qb:123",
        ),
        "vendor_name": ParameterSchema(
            type="string",
            required=False,
            description="New display name (must be unique if changed)",
            example="Acme Supply Co. (Updated)",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="New email address",
            example="newemail@acme-supply.com",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="New phone number",
            example="(555) 987-6543",
        ),
        "website": ParameterSchema(
            type="string",
            required=False,
            description="New website URL",
            example="https://www.acme-supply-new.com",
        ),
        "billing_address": ParameterSchema(
            type="object",
            required=False,
            description="New billing address object",
            example={"Line1": "456 Oak Ave", "City": "Oakland", "PostalCode": "94601"},
        ),
    },
    returns={
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="QuickBooks vendor ID",
            example="qb:123",
        ),
        "display_name": ReturnFieldSchema(
            type="string",
            description="Updated display name",
            example="Acme Supply Co. (Updated)",
        ),
        "updated": ReturnFieldSchema(
            type="boolean",
            description="True if update was successful",
            example=True,
        ),
        "deep_link": ReturnFieldSchema(
            type="string",
            description="Direct URL to open this vendor in QuickBooks Online",
            example="https://app.qbo.intuit.com/app/vendordetail?nameId=123",
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
            description="Duplicate vendor name or invalid field value",
            recovery_hint="Check that new vendor_name is unique",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Vendor not found or stale SyncToken",
            recovery_hint="Retry the update - SyncToken will be refreshed",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["vendor.get", "vendor.search"],
        typically_followed_by=["vendor.get"],
        related_capabilities=["vendor.create", "vendor.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)


# All vendor schemas
VENDOR_SCHEMAS: dict[str, CapabilitySchema] = {
    "vendor.create": VENDOR_CREATE,
    "vendor.get": VENDOR_GET,
    "vendor.list": VENDOR_LIST,
    "vendor.search": VENDOR_SEARCH,
    "vendor.update": VENDOR_UPDATE,
}
