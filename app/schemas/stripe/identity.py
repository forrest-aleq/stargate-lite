"""
Stripe Identity Capability Schemas.

Rich metadata for identity verification operations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

VERIFICATION_SESSION_CREATE = CapabilitySchema(
    capability_key="stripe.identity.verification_session.create",
    service="stripe",
    category="identity",
    description="Create an Identity verification session",
    description_detailed=(
        "Creates a VerificationSession for collecting and verifying identity "
        "documents. Sessions guide users through document capture and selfie "
        "verification using Stripe's hosted UI or embedded SDK."
    ),
    parameters={
        "type": ParameterSchema(
            type="string",
            required=True,
            description="Type of verification",
            enum=["document", "id_number"],
            example="document",
        ),
        "options": ParameterSchema(
            type="object",
            required=False,
            description="Verification options",
            example={"document": {"require_matching_selfie": True}},
        ),
        "return_url": ParameterSchema(
            type="string",
            required=False,
            description="URL to redirect after verification",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Key-value pairs for your use",
        ),
    },
    returns={
        "id": ReturnFieldSchema(
            type="string",
            description="Verification session ID",
            example="vs_ABC123",
        ),
        "status": ReturnFieldSchema(type="string", description="Session status"),
        "url": ReturnFieldSchema(type="string", description="Hosted verification URL"),
        "client_secret": ReturnFieldSchema(type="string", description="Client secret"),
        "type": ReturnFieldSchema(type="string", description="Verification type"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["stripe.identity.verification_session.retrieve"],
    ),
    idempotent=False,
    has_side_effects=True,
)

VERIFICATION_SESSION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.identity.verification_session.retrieve",
    service="stripe",
    category="identity",
    description="Retrieve an Identity verification session",
    parameters={
        "session_id": ParameterSchema(
            type="string",
            required=True,
            description="Verification session ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Session ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "type": ReturnFieldSchema(type="string", description="Type"),
        "verified_outputs": ReturnFieldSchema(type="object", description="Outputs"),
        "last_error": ReturnFieldSchema(type="object", description="Last error"),
        "last_verification_report": ReturnFieldSchema(type="string", description="Report"),
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

VERIFICATION_SESSION_UPDATE = CapabilitySchema(
    capability_key="stripe.identity.verification_session.update",
    service="stripe",
    category="identity",
    description="Update an Identity verification session",
    parameters={
        "session_id": ParameterSchema(
            type="string",
            required=True,
            description="Session ID to update",
        ),
        "type": ParameterSchema(
            type="string",
            required=False,
            description="New verification type",
            enum=["document", "id_number"],
        ),
        "options": ParameterSchema(
            type="object",
            required=False,
            description="Updated options",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Session ID"),
        "status": ReturnFieldSchema(type="string", description="Status"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Session already submitted or expired",
            recovery_hint="Only created sessions can be updated",
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

VERIFICATION_SESSION_CANCEL = CapabilitySchema(
    capability_key="stripe.identity.verification_session.cancel",
    service="stripe",
    category="identity",
    description="Cancel an Identity verification session",
    parameters={
        "session_id": ParameterSchema(
            type="string",
            required=True,
            description="Session ID to cancel",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Session ID"),
        "status": ReturnFieldSchema(type="string", description="Should be canceled"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Session already completed or expired",
            recovery_hint="Only active sessions can be canceled",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

VERIFICATION_SESSION_REDACT = CapabilitySchema(
    capability_key="stripe.identity.verification_session.redact",
    service="stripe",
    category="identity",
    description="Redact an Identity verification session",
    description_detailed=(
        "Redacts a VerificationSession to remove all collected identity data. "
        "Use for GDPR compliance or when data is no longer needed."
    ),
    parameters={
        "session_id": ParameterSchema(
            type="string",
            required=True,
            description="Session ID to redact",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Session ID"),
        "status": ReturnFieldSchema(type="string", description="Should be redacted"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Session not in redactable state",
            recovery_hint="Session must be verified or canceled first",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

VERIFICATION_SESSION_LIST = CapabilitySchema(
    capability_key="stripe.identity.verification_session.list",
    service="stripe",
    category="identity",
    description="List Identity verification sessions",
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["created", "processing", "verified", "requires_input", "canceled"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of sessions"),
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

# ============ VERIFICATION REPORTS ============

VERIFICATION_REPORT_RETRIEVE = CapabilitySchema(
    capability_key="stripe.identity.verification_report.retrieve",
    service="stripe",
    category="identity",
    description="Retrieve an Identity verification report",
    description_detailed=(
        "Retrieves a VerificationReport containing the results of identity "
        "verification including document data and selfie match results."
    ),
    parameters={
        "report_id": ParameterSchema(
            type="string",
            required=True,
            description="Verification report ID",
            example="vr_ABC123",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Report ID"),
        "type": ReturnFieldSchema(type="string", description="Report type"),
        "verification_session": ReturnFieldSchema(type="string", description="Session ID"),
        "document": ReturnFieldSchema(type="object", description="Document data"),
        "selfie": ReturnFieldSchema(type="object", description="Selfie check results"),
        "id_number": ReturnFieldSchema(type="object", description="ID number data"),
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

VERIFICATION_REPORT_LIST = CapabilitySchema(
    capability_key="stripe.identity.verification_report.list",
    service="stripe",
    category="identity",
    description="List Identity verification reports",
    parameters={
        "verification_session": ParameterSchema(
            type="string",
            required=False,
            description="Filter by session ID",
        ),
        "type": ParameterSchema(
            type="string",
            required=False,
            description="Filter by type",
            enum=["document", "id_number"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of reports"),
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

IDENTITY_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.identity.verification_session.create": VERIFICATION_SESSION_CREATE,
    "stripe.identity.verification_session.retrieve": VERIFICATION_SESSION_RETRIEVE,
    "stripe.identity.verification_session.update": VERIFICATION_SESSION_UPDATE,
    "stripe.identity.verification_session.cancel": VERIFICATION_SESSION_CANCEL,
    "stripe.identity.verification_session.redact": VERIFICATION_SESSION_REDACT,
    "stripe.identity.verification_session.list": VERIFICATION_SESSION_LIST,
    "stripe.identity.verification_report.retrieve": VERIFICATION_REPORT_RETRIEVE,
    "stripe.identity.verification_report.list": VERIFICATION_REPORT_LIST,
}
