"""
DocuSign Capability Schemas.

Rich metadata for DocuSign e-signature operations.
Finance teams use DocuSign for contracts, agreements, and approval workflows.

API Docs: https://developers.docusign.com/docs/esign-rest-api/reference/
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ ENVELOPES ============

DOCUSIGN_ENVELOPES_LIST = CapabilitySchema(
    capability_key="docusign.envelopes.list",
    service="docusign",
    category="envelopes",
    description="List envelopes from DocuSign",
    parameters={
        "from_date": ParameterSchema(
            type="string", required=False, description="Start date (ISO 8601)"
        ),
        "to_date": ParameterSchema(
            type="string", required=False, description="End date (ISO 8601)"
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            enum=["created", "sent", "delivered", "signed", "completed", "declined", "voided"],
            description="Envelope status filter",
        ),
        "folder_ids": ParameterSchema(type="string", required=False, description="Folder IDs to filter by"),
        "count": ParameterSchema(type="integer", required=False, description="Max 100"),
    },
    returns={
        "envelopes": ReturnFieldSchema(
            type="array",
            description="Envelopes with envelope_id, status, subject, sent_date, completed_date",
        ),
        "result_set_size": ReturnFieldSchema(type="integer", description="Count returned"),
        "total_set_size": ReturnFieldSchema(type="integer", description="Total available"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="DocuSign OAuth not configured",
            recovery_hint="User must connect DocuSign account",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["docusign.envelopes.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

DOCUSIGN_ENVELOPES_GET = CapabilitySchema(
    capability_key="docusign.envelopes.get",
    service="docusign",
    category="envelopes",
    description="Get envelope details from DocuSign",
    parameters={
        "envelope_id": ParameterSchema(type="string", required=True, description="DocuSign envelope ID"),
    },
    returns={
        "envelope_id": ReturnFieldSchema(type="string", description="Envelope ID"),
        "status": ReturnFieldSchema(type="string", description="Envelope status"),
        "email_subject": ReturnFieldSchema(type="string", description="Email subject"),
        "email_blurb": ReturnFieldSchema(type="string", description="Email message"),
        "sender": ReturnFieldSchema(type="object", description="Sender info"),
        "recipients": ReturnFieldSchema(type="object", description="Recipients by type"),
        "documents": ReturnFieldSchema(type="array", description="Document list"),
        "created_date_time": ReturnFieldSchema(type="string", description="Created"),
        "sent_date_time": ReturnFieldSchema(type="string", description="Sent"),
        "completed_date_time": ReturnFieldSchema(type="string", description="Completed"),
    },
    idempotent=True,
    has_side_effects=False,
)

DOCUSIGN_ENVELOPES_CREATE = CapabilitySchema(
    capability_key="docusign.envelopes.create",
    service="docusign",
    category="envelopes",
    description="Create and send envelope for signature",
    description_detailed=(
        "Creates a new envelope with documents and recipients. "
        "Can be sent immediately or saved as draft."
    ),
    parameters={
        "email_subject": ParameterSchema(type="string", required=True, description="Email subject line"),
        "email_blurb": ParameterSchema(type="string", required=False, description="Email body text"),
        "documents": ParameterSchema(
            type="array",
            required=True,
            description="Documents with document_id, name, file_extension, document_base64",
        ),
        "recipients": ParameterSchema(
            type="object",
            required=True,
            description="Recipients: signers, carbonCopies, etc.",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            enum=["created", "sent"],
            description="'sent' to send immediately, 'created' for draft",
        ),
    },
    returns={
        "envelope_id": ReturnFieldSchema(type="string", description="Created envelope ID"),
        "status": ReturnFieldSchema(type="string", description="Envelope status"),
        "uri": ReturnFieldSchema(type="string", description="Envelope URI"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["docusign.envelopes.get", "docusign.recipients.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

DOCUSIGN_ENVELOPES_SEND = CapabilitySchema(
    capability_key="docusign.envelopes.send",
    service="docusign",
    category="envelopes",
    description="Send a draft envelope",
    parameters={
        "envelope_id": ParameterSchema(type="string", required=True, description="Envelope ID to send"),
    },
    returns={
        "envelope_id": ReturnFieldSchema(type="string", description="Sent envelope ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'sent'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["docusign.envelopes.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

DOCUSIGN_ENVELOPES_VOID = CapabilitySchema(
    capability_key="docusign.envelopes.void",
    service="docusign",
    category="envelopes",
    description="Void an envelope",
    parameters={
        "envelope_id": ParameterSchema(type="string", required=True, description="Envelope ID to void"),
        "voided_reason": ParameterSchema(
            type="string", required=True, description="Reason for voiding"
        ),
    },
    returns={
        "envelope_id": ReturnFieldSchema(type="string", description="Voided envelope ID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'voided'"),
    },
    idempotent=True,
    has_side_effects=True,
)

# ============ RECIPIENTS ============

DOCUSIGN_RECIPIENTS_LIST = CapabilitySchema(
    capability_key="docusign.recipients.list",
    service="docusign",
    category="recipients",
    description="List recipients for an envelope",
    parameters={
        "envelope_id": ParameterSchema(type="string", required=True, description="Envelope ID"),
    },
    returns={
        "signers": ReturnFieldSchema(type="array", description="Signers"),
        "carbon_copies": ReturnFieldSchema(type="array", description="CC recipients"),
        "recipient_count": ReturnFieldSchema(type="integer", description="Total recipients"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["docusign.envelopes.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

DOCUSIGN_RECIPIENTS_UPDATE = CapabilitySchema(
    capability_key="docusign.recipients.update",
    service="docusign",
    category="recipients",
    description="Update recipient information",
    parameters={
        "envelope_id": ParameterSchema(type="string", required=True, description="Envelope ID"),
        "recipient_id": ParameterSchema(type="string", required=True, description="Recipient ID to update"),
        "name": ParameterSchema(type="string", required=False, description="Updated recipient name"),
        "email": ParameterSchema(type="string", required=False, description="Updated recipient email"),
    },
    returns={
        "recipient_id": ReturnFieldSchema(type="string", description="Updated recipient ID"),
        "status": ReturnFieldSchema(type="string", description="Update status"),
    },
    idempotent=True,
    has_side_effects=True,
)

# ============ DOCUMENTS ============

DOCUSIGN_DOCUMENTS_LIST = CapabilitySchema(
    capability_key="docusign.documents.list",
    service="docusign",
    category="documents",
    description="List documents in an envelope",
    parameters={
        "envelope_id": ParameterSchema(type="string", required=True, description="Envelope ID"),
    },
    returns={
        "documents": ReturnFieldSchema(
            type="array",
            description="Documents with document_id, name, type, uri",
        ),
    },
    idempotent=True,
    has_side_effects=False,
)

DOCUSIGN_DOCUMENTS_DOWNLOAD = CapabilitySchema(
    capability_key="docusign.documents.download",
    service="docusign",
    category="documents",
    description="Download a document from an envelope",
    parameters={
        "envelope_id": ParameterSchema(type="string", required=True, description="Envelope ID"),
        "document_id": ParameterSchema(
            type="string",
            required=True,
            description="Document ID or 'combined' for all docs",
        ),
    },
    returns={
        "document_base64": ReturnFieldSchema(
            type="string", description="Base64 encoded document"
        ),
        "content_type": ReturnFieldSchema(type="string", description="MIME type"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["docusign.documents.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ TEMPLATES ============

DOCUSIGN_TEMPLATES_LIST = CapabilitySchema(
    capability_key="docusign.templates.list",
    service="docusign",
    category="templates",
    description="List templates from DocuSign",
    parameters={
        "folder_id": ParameterSchema(type="string", required=False, description="Folder ID to filter by"),
        "search_text": ParameterSchema(type="string", required=False, description="Search text filter"),
        "count": ParameterSchema(type="integer", required=False, description="Maximum templates to return"),
    },
    returns={
        "templates": ReturnFieldSchema(
            type="array",
            description="Templates with template_id, name, description, created",
        ),
        "result_set_size": ReturnFieldSchema(type="integer", description="Count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["docusign.envelopes.create_from_template"],
    ),
    idempotent=True,
    has_side_effects=False,
)

DOCUSIGN_ENVELOPES_CREATE_FROM_TEMPLATE = CapabilitySchema(
    capability_key="docusign.envelopes.create_from_template",
    service="docusign",
    category="envelopes",
    description="Create envelope from a template",
    parameters={
        "template_id": ParameterSchema(type="string", required=True, description="Template ID to use"),
        "email_subject": ParameterSchema(type="string", required=False, description="Override email subject"),
        "template_roles": ParameterSchema(
            type="array",
            required=True,
            description="Role assignments with role_name, name, email",
        ),
        "status": ParameterSchema(
            type="string", required=False, enum=["created", "sent"],
            description="'sent' to send immediately, 'created' for draft",
        ),
    },
    returns={
        "envelope_id": ReturnFieldSchema(type="string", description="Created envelope ID"),
        "status": ReturnFieldSchema(type="string", description="Envelope status"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["docusign.templates.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# Export all schemas
DOCUSIGN_SCHEMAS: dict[str, CapabilitySchema] = {
    "docusign.envelopes.list": DOCUSIGN_ENVELOPES_LIST,
    "docusign.envelopes.get": DOCUSIGN_ENVELOPES_GET,
    "docusign.envelopes.create": DOCUSIGN_ENVELOPES_CREATE,
    "docusign.envelopes.send": DOCUSIGN_ENVELOPES_SEND,
    "docusign.envelopes.void": DOCUSIGN_ENVELOPES_VOID,
    "docusign.recipients.list": DOCUSIGN_RECIPIENTS_LIST,
    "docusign.recipients.update": DOCUSIGN_RECIPIENTS_UPDATE,
    "docusign.documents.list": DOCUSIGN_DOCUMENTS_LIST,
    "docusign.documents.download": DOCUSIGN_DOCUMENTS_DOWNLOAD,
    "docusign.templates.list": DOCUSIGN_TEMPLATES_LIST,
    "docusign.envelopes.create_from_template": DOCUSIGN_ENVELOPES_CREATE_FROM_TEMPLATE,
}

__all__ = ["DOCUSIGN_SCHEMAS"]
