"""
Stripe Files & Reporting Capability Schemas.

Rich metadata for file uploads and report generation.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ FILES ============

FILE_CREATE = CapabilitySchema(
    capability_key="stripe.file.create",
    service="stripe",
    category="files",
    description="Upload a file to Stripe",
    description_detailed=(
        "Uploads a file to Stripe for use in disputes, identity verification, "
        "or account onboarding."
    ),
    parameters={
        "file": ParameterSchema(
            type="string",
            required=True,
            description="File contents (base64 encoded)",
        ),
        "purpose": ParameterSchema(
            type="string",
            required=True,
            description="Purpose of the file",
            enum=[
                "account_requirement",
                "additional_verification",
                "business_icon",
                "business_logo",
                "customer_signature",
                "dispute_evidence",
                "identity_document",
                "pci_document",
                "tax_document_user_upload",
            ],
        ),
        "file_link_data": ParameterSchema(
            type="object",
            required=False,
            description="Create a file link",
            example={"create": True},
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="File ID",
            example="file_ABC123",
        ),
        "purpose": ReturnFieldSchema(type="string", description="File purpose"),
        "size": ReturnFieldSchema(type="integer", description="Size in bytes"),
        "type": ReturnFieldSchema(type="string", description="MIME type"),
        "url": ReturnFieldSchema(type="string", description="Download URL"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid file or purpose",
            recovery_hint="Check file size and format requirements",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

FILE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.file.retrieve",
    service="stripe",
    category="files",
    description="Retrieve a file",
    parameters={
        "file_id": ParameterSchema(
            type="string",
            required=True,
            description="File ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="File ID"),
        "purpose": ReturnFieldSchema(type="string", description="Purpose"),
        "size": ReturnFieldSchema(type="integer", description="Size"),
        "type": ReturnFieldSchema(type="string", description="MIME type"),
        "url": ReturnFieldSchema(type="string", description="URL"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

FILE_LIST = CapabilitySchema(
    capability_key="stripe.file.list",
    service="stripe",
    category="files",
    description="List files",
    parameters={
        "purpose": ParameterSchema(
            type="string",
            required=False,
            description="Filter by purpose",
        ),
        "created": ParameterSchema(
            type="object",
            required=False,
            description="Filter by created date",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of files"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ FILE LINKS ============

FILE_LINK_CREATE = CapabilitySchema(
    capability_key="stripe.file_link.create",
    service="stripe",
    category="files",
    description="Create a file link",
    description_detailed=(
        "Creates a shareable link for a file that can be accessed without "
        "authentication for a limited time."
    ),
    parameters={
        "file": ParameterSchema(
            type="string",
            required=True,
            description="File ID to link",
        ),
        "expires_at": ParameterSchema(
            type="integer",
            required=False,
            description="Link expiration timestamp",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="File link ID"),
        "file": ReturnFieldSchema(type="string", description="File ID"),
        "url": ReturnFieldSchema(type="string", description="Shareable URL"),
        "expires_at": ReturnFieldSchema(type="integer", description="Expiration"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

FILE_LINK_RETRIEVE = CapabilitySchema(
    capability_key="stripe.file_link.retrieve",
    service="stripe",
    category="files",
    description="Retrieve a file link",
    parameters={
        "file_link_id": ParameterSchema(
            type="string",
            required=True,
            description="File link ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="File link ID"),
        "file": ReturnFieldSchema(type="string", description="File ID"),
        "url": ReturnFieldSchema(type="string", description="URL"),
        "expired": ReturnFieldSchema(type="boolean", description="Is expired"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

FILE_LINK_UPDATE = CapabilitySchema(
    capability_key="stripe.file_link.update",
    service="stripe",
    category="files",
    description="Update a file link",
    parameters={
        "file_link_id": ParameterSchema(
            type="string",
            required=True,
            description="File link ID to update",
        ),
        "expires_at": ParameterSchema(
            type="string",
            required=False,
            description="New expiration ('now' to expire)",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="File link ID"),
        "expired": ReturnFieldSchema(type="boolean", description="Is expired"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

FILE_LINK_LIST = CapabilitySchema(
    capability_key="stripe.file_link.list",
    service="stripe",
    category="files",
    description="List file links",
    parameters={
        "file": ParameterSchema(
            type="string",
            required=False,
            description="Filter by file ID",
        ),
        "expired": ParameterSchema(
            type="boolean",
            required=False,
            description="Filter by expired status",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of file links"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ REPORTING ============

REPORT_RUN_CREATE = CapabilitySchema(
    capability_key="stripe.reporting.report_run.create",
    service="stripe",
    category="reporting",
    description="Create a report run",
    description_detailed=(
        "Creates a new report run to generate a report of a specific type. "
        "Reports are generated asynchronously."
    ),
    parameters={
        "report_type": ParameterSchema(
            type="string",
            required=True,
            description="Type of report",
            example="balance.summary.1",
        ),
        "parameters": ParameterSchema(
            type="object",
            required=False,
            description="Report parameters",
            example={
                "interval_start": 1609459200,
                "interval_end": 1612137600,
            },
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Report run ID"),
        "report_type": ReturnFieldSchema(type="string", description="Report type"),
        "status": ReturnFieldSchema(type="string", description="Run status"),
        "result": ReturnFieldSchema(type="object", description="Result when done"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid report type or parameters",
            recovery_hint="Check report type and parameter format",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

REPORT_RUN_RETRIEVE = CapabilitySchema(
    capability_key="stripe.reporting.report_run.retrieve",
    service="stripe",
    category="reporting",
    description="Retrieve a report run",
    parameters={
        "report_run_id": ParameterSchema(
            type="string",
            required=True,
            description="Report run ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Report run ID"),
        "report_type": ReturnFieldSchema(type="string", description="Type"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "result": ReturnFieldSchema(type="object", description="Result file info"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

REPORT_RUN_LIST = CapabilitySchema(
    capability_key="stripe.reporting.report_run.list",
    service="stripe",
    category="reporting",
    description="List report runs",
    parameters={
        "created": ParameterSchema(
            type="object",
            required=False,
            description="Filter by created date",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of report runs"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

REPORT_TYPE_RETRIEVE = CapabilitySchema(
    capability_key="stripe.reporting.report_type.retrieve",
    service="stripe",
    category="reporting",
    description="Retrieve a report type",
    parameters={
        "report_type": ParameterSchema(
            type="string",
            required=True,
            description="Report type ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Report type ID"),
        "name": ReturnFieldSchema(type="string", description="Human-readable name"),
        "data_available_start": ReturnFieldSchema(type="integer", description="Data start"),
        "data_available_end": ReturnFieldSchema(type="integer", description="Data end"),
        "default_columns": ReturnFieldSchema(type="array", description="Default columns"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

REPORT_TYPE_LIST = CapabilitySchema(
    capability_key="stripe.reporting.report_type.list",
    service="stripe",
    category="reporting",
    description="List available report types",
    parameters={},
    returns={
        "data": ReturnFieldSchema(type="array", description="List of report types"),
        "has_more": ReturnFieldSchema(type="boolean", description="More results"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

FILE_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.file.create": FILE_CREATE,
    "stripe.file.retrieve": FILE_RETRIEVE,
    "stripe.file.list": FILE_LIST,
    "stripe.file_link.create": FILE_LINK_CREATE,
    "stripe.file_link.retrieve": FILE_LINK_RETRIEVE,
    "stripe.file_link.update": FILE_LINK_UPDATE,
    "stripe.file_link.list": FILE_LINK_LIST,
    "stripe.reporting.report_run.create": REPORT_RUN_CREATE,
    "stripe.reporting.report_run.retrieve": REPORT_RUN_RETRIEVE,
    "stripe.reporting.report_run.list": REPORT_RUN_LIST,
    "stripe.reporting.report_type.retrieve": REPORT_TYPE_RETRIEVE,
    "stripe.reporting.report_type.list": REPORT_TYPE_LIST,
}
