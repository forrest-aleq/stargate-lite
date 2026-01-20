"""
DocuSign Capability Registry
eSignature: envelopes, recipients, documents, templates
"""

from app.connectors.docusign import docusign_connector

DOCUSIGN_CAPABILITIES = {
    # ========== ENVELOPES ==========
    "docusign.envelopes.list": {
        "handler": docusign_connector.list_envelopes,
        "tool_name": "docusign.list_envelopes",
        "description": "List envelopes from DocuSign",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "docusign.envelope.get": {
        "handler": docusign_connector.get_envelope,
        "tool_name": "docusign.get_envelope",
        "description": "Get envelope details",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "docusign.envelope.create": {
        "handler": docusign_connector.create_envelope,
        "tool_name": "docusign.create_envelope",
        "description": "Create and optionally send an envelope",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "docusign.envelope.send": {
        "handler": docusign_connector.send_envelope,
        "tool_name": "docusign.send_envelope",
        "description": "Send a draft envelope",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "docusign.envelope.void": {
        "handler": docusign_connector.void_envelope,
        "tool_name": "docusign.void_envelope",
        "description": "Void an envelope",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== RECIPIENTS ==========
    "docusign.recipients.list": {
        "handler": docusign_connector.list_recipients,
        "tool_name": "docusign.list_recipients",
        "description": "List recipients for an envelope",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "docusign.recipient.update": {
        "handler": docusign_connector.update_recipient,
        "tool_name": "docusign.update_recipient",
        "description": "Update recipient information",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== DOCUMENTS ==========
    "docusign.documents.list": {
        "handler": docusign_connector.list_documents,
        "tool_name": "docusign.list_documents",
        "description": "List documents in an envelope",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "docusign.document.download": {
        "handler": docusign_connector.download_document,
        "tool_name": "docusign.download_document",
        "description": "Download a document from an envelope",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== TEMPLATES ==========
    "docusign.templates.list": {
        "handler": docusign_connector.list_templates,
        "tool_name": "docusign.list_templates",
        "description": "List templates from DocuSign",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "docusign.envelope.create_from_template": {
        "handler": docusign_connector.create_envelope_from_template,
        "tool_name": "docusign.create_envelope_from_template",
        "description": "Create envelope from a template",
        "requires_oauth": True,
        "service": "docusign",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}
