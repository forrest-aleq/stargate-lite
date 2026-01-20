"""
Airtable Capability Registry
Databases: bases, tables, records, fields, webhooks
"""

from app.connectors.airtable import airtable_connector

AIRTABLE_CAPABILITIES = {
    # ========== BASES ==========
    "airtable.bases.list": {
        "handler": airtable_connector.list_bases,
        "tool_name": "airtable.list_bases",
        "description": "List bases accessible to the user",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== TABLES ==========
    "airtable.tables.list": {
        "handler": airtable_connector.list_tables,
        "tool_name": "airtable.list_tables",
        "description": "List tables in a base",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "airtable.tables.create": {
        "handler": airtable_connector.create_table,
        "tool_name": "airtable.create_table",
        "description": "Create a new table in a base",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== RECORDS ==========
    "airtable.records.list": {
        "handler": airtable_connector.list_records,
        "tool_name": "airtable.list_records",
        "description": "List records from an Airtable table",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "airtable.records.get": {
        "handler": airtable_connector.get_record,
        "tool_name": "airtable.get_record",
        "description": "Get a specific record from Airtable",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "airtable.records.create": {
        "handler": airtable_connector.create_records,
        "tool_name": "airtable.create_records",
        "description": "Create record(s) in Airtable",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "airtable.records.update": {
        "handler": airtable_connector.update_records,
        "tool_name": "airtable.update_records",
        "description": "Update record(s) in Airtable",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "airtable.records.delete": {
        "handler": airtable_connector.delete_records,
        "tool_name": "airtable.delete_records",
        "description": "Delete record(s) from Airtable",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== FIELDS ==========
    "airtable.fields.create": {
        "handler": airtable_connector.create_field,
        "tool_name": "airtable.create_field",
        "description": "Create a new field in an Airtable table",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "airtable.fields.update": {
        "handler": airtable_connector.update_field,
        "tool_name": "airtable.update_field",
        "description": "Update a field's name or description",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== WEBHOOKS ==========
    "airtable.webhooks.list": {
        "handler": airtable_connector.list_webhooks,
        "tool_name": "airtable.list_webhooks",
        "description": "List webhooks for a base",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "airtable.webhooks.create": {
        "handler": airtable_connector.create_webhook,
        "tool_name": "airtable.create_webhook",
        "description": "Create a webhook for record changes",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "airtable.webhooks.delete": {
        "handler": airtable_connector.delete_webhook,
        "tool_name": "airtable.delete_webhook",
        "description": "Delete a webhook",
        "requires_oauth": True,
        "service": "airtable",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}
