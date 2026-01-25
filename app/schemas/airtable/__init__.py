"""
Airtable Capability Schemas.

Rich metadata for Airtable database operations.
Finance teams use Airtable for project tracking, approval workflows, and data management.

API Docs: https://airtable.com/developers/web/api/introduction
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ BASES ============

AIRTABLE_BASES_LIST = CapabilitySchema(
    capability_key="airtable.bases.list",
    service="airtable",
    category="bases",
    description="List bases accessible to the user",
    parameters={},
    returns={
        "bases": ReturnFieldSchema(
            type="array",
            description="Bases with id, name, permission_level",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Airtable API key not configured",
            recovery_hint="User must provide Airtable personal access token",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["airtable.tables.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ TABLES ============

AIRTABLE_TABLES_LIST = CapabilitySchema(
    capability_key="airtable.tables.list",
    service="airtable",
    category="tables",
    description="List tables in a base",
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
    },
    returns={
        "tables": ReturnFieldSchema(
            type="array",
            description="Tables with id, name, primary_field_id, fields, views",
        ),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["airtable.bases.list"],
        typically_followed_by=["airtable.records.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

AIRTABLE_TABLES_CREATE = CapabilitySchema(
    capability_key="airtable.tables.create",
    service="airtable",
    category="tables",
    description="Create a new table in a base",
    description_detailed=(
        "Creates a new table with specified fields. "
        "At least one field must be provided. The first field becomes the primary field."
    ),
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "name": ParameterSchema(type="string", required=True, description="Table name"),
        "description": ParameterSchema(
            type="string", required=False, description="Table description"
        ),
        "fields": ParameterSchema(
            type="array",
            required=True,
            description="Fields to create with name, type, and optional options",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Created table ID"),
        "name": ReturnFieldSchema(type="string", description="Table name"),
        "primary_field_id": ReturnFieldSchema(type="string", description="Primary field ID"),
        "fields": ReturnFieldSchema(type="array", description="Created fields"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["airtable.bases.list"],
        typically_followed_by=["airtable.records.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ RECORDS ============

AIRTABLE_RECORDS_LIST = CapabilitySchema(
    capability_key="airtable.records.list",
    service="airtable",
    category="records",
    description="List records from an Airtable table",
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "table_id": ParameterSchema(type="string", required=True, description="Table ID or name"),
        "view": ParameterSchema(type="string", required=False, description="View ID or name"),
        "fields": ParameterSchema(
            type="array",
            required=False,
            description="Field names to return",
            items_type="string",
        ),
        "filter_by_formula": ParameterSchema(
            type="string",
            required=False,
            description="Airtable formula to filter records",
            example="{Status} = 'Approved'",
        ),
        "sort": ParameterSchema(
            type="array",
            required=False,
            description="Sort specification [{field, direction}]",
        ),
        "max_records": ParameterSchema(
            type="integer", required=False, description="Maximum records to return"
        ),
        "page_size": ParameterSchema(
            type="integer", required=False, description="Records per page (max 100)"
        ),
        "offset": ParameterSchema(type="string", required=False, description="Pagination offset"),
    },
    returns={
        "records": ReturnFieldSchema(
            type="array",
            description="Records with id, created_time, fields",
        ),
        "offset": ReturnFieldSchema(
            type="string", description="Offset for next page (if more records)"
        ),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["airtable.tables.list"],
        typically_followed_by=["airtable.records.get", "airtable.records.update"],
    ),
    idempotent=True,
    has_side_effects=False,
)

AIRTABLE_RECORDS_GET = CapabilitySchema(
    capability_key="airtable.records.get",
    service="airtable",
    category="records",
    description="Get a specific record from Airtable",
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "table_id": ParameterSchema(type="string", required=True, description="Table ID or name"),
        "record_id": ParameterSchema(
            type="string", required=True, description="Airtable record ID"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Record ID"),
        "created_time": ReturnFieldSchema(type="string", description="Created timestamp"),
        "fields": ReturnFieldSchema(type="object", description="Field values"),
    },
    idempotent=True,
    has_side_effects=False,
)

AIRTABLE_RECORDS_CREATE = CapabilitySchema(
    capability_key="airtable.records.create",
    service="airtable",
    category="records",
    description="Create record(s) in Airtable",
    description_detailed=(
        "Creates one or more records in an Airtable table. "
        "Can create up to 10 records per request."
    ),
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "table_id": ParameterSchema(type="string", required=True, description="Table ID or name"),
        "records": ParameterSchema(
            type="array",
            required=True,
            description="Records to create, each with {fields: {...}}",
        ),
        "typecast": ParameterSchema(
            type="boolean",
            required=False,
            description="Auto-convert strings to proper field types",
        ),
    },
    returns={
        "records": ReturnFieldSchema(
            type="array",
            description="Created records with id, created_time, fields",
        ),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["airtable.tables.list"],
    ),
    idempotent=False,
    has_side_effects=True,
)

AIRTABLE_RECORDS_UPDATE = CapabilitySchema(
    capability_key="airtable.records.update",
    service="airtable",
    category="records",
    description="Update record(s) in Airtable",
    description_detailed=(
        "Updates one or more records. PATCH updates only specified fields, "
        "PUT replaces all fields."
    ),
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "table_id": ParameterSchema(type="string", required=True, description="Table ID or name"),
        "records": ParameterSchema(
            type="array",
            required=True,
            description="Records to update, each with {id, fields: {...}}",
        ),
        "typecast": ParameterSchema(
            type="boolean", required=False, description="Auto-convert types"
        ),
    },
    returns={
        "records": ReturnFieldSchema(
            type="array",
            description="Updated records with id, created_time, fields",
        ),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["airtable.records.list", "airtable.records.get"],
    ),
    idempotent=True,
    has_side_effects=True,
)

AIRTABLE_RECORDS_DELETE = CapabilitySchema(
    capability_key="airtable.records.delete",
    service="airtable",
    category="records",
    description="Delete record(s) from Airtable",
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "table_id": ParameterSchema(type="string", required=True, description="Table ID or name"),
        "record_ids": ParameterSchema(
            type="array",
            required=True,
            description="Record IDs to delete (max 10)",
            items_type="string",
        ),
    },
    returns={
        "records": ReturnFieldSchema(
            type="array",
            description="Deleted records with id and deleted: true",
        ),
    },
    idempotent=True,
    has_side_effects=True,
)

# ============ FIELDS ============

AIRTABLE_FIELDS_CREATE = CapabilitySchema(
    capability_key="airtable.fields.create",
    service="airtable",
    category="fields",
    description="Create a new field in an Airtable table",
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "table_id": ParameterSchema(type="string", required=True, description="Table ID or name"),
        "name": ParameterSchema(type="string", required=True, description="Field name"),
        "type": ParameterSchema(
            type="string",
            required=True,
            enum=[
                "singleLineText",
                "multilineText",
                "number",
                "currency",
                "percent",
                "date",
                "dateTime",
                "checkbox",
                "singleSelect",
                "multipleSelects",
                "email",
                "url",
                "phoneNumber",
                "rating",
                "duration",
            ],
            description="Field type to create",
        ),
        "options": ParameterSchema(
            type="object",
            required=False,
            description="Type-specific options (e.g., select choices)",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Field ID"),
        "name": ReturnFieldSchema(type="string", description="Field name"),
        "type": ReturnFieldSchema(type="string", description="Field type"),
    },
    idempotent=False,
    has_side_effects=True,
)

AIRTABLE_FIELDS_UPDATE = CapabilitySchema(
    capability_key="airtable.fields.update",
    service="airtable",
    category="fields",
    description="Update a field's name or description",
    description_detailed=(
        "Updates an existing field. Only name and description can be modified. "
        "Field type cannot be changed after creation."
    ),
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "table_id": ParameterSchema(type="string", required=True, description="Table ID"),
        "field_id": ParameterSchema(type="string", required=True, description="Field ID to update"),
        "name": ParameterSchema(type="string", required=False, description="New field name"),
        "description": ParameterSchema(
            type="string", required=False, description="New field description"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Field ID"),
        "name": ReturnFieldSchema(type="string", description="Updated field name"),
        "type": ReturnFieldSchema(type="string", description="Field type (unchanged)"),
        "description": ReturnFieldSchema(type="string", description="Updated description"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["airtable.tables.list"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ WEBHOOKS ============

AIRTABLE_WEBHOOKS_LIST = CapabilitySchema(
    capability_key="airtable.webhooks.list",
    service="airtable",
    category="webhooks",
    description="List webhooks for a base",
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
    },
    returns={
        "webhooks": ReturnFieldSchema(
            type="array",
            description="Webhooks with id, notification_url, specification",
        ),
    },
    idempotent=True,
    has_side_effects=False,
)

AIRTABLE_WEBHOOKS_CREATE = CapabilitySchema(
    capability_key="airtable.webhooks.create",
    service="airtable",
    category="webhooks",
    description="Create a webhook for record changes",
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "notification_url": ParameterSchema(
            type="string", required=True, description="URL to receive notifications"
        ),
        "specification": ParameterSchema(
            type="object",
            required=True,
            description="Webhook specification (triggers, data types)",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Webhook ID"),
        "mac_secret_base64": ReturnFieldSchema(
            type="string", description="Secret for verifying payloads"
        ),
        "expiration_time": ReturnFieldSchema(type="string", description="Expiration"),
    },
    idempotent=False,
    has_side_effects=True,
)

AIRTABLE_WEBHOOKS_DELETE = CapabilitySchema(
    capability_key="airtable.webhooks.delete",
    service="airtable",
    category="webhooks",
    description="Delete a webhook",
    parameters={
        "base_id": ParameterSchema(type="string", required=True, description="Airtable base ID"),
        "webhook_id": ParameterSchema(
            type="string", required=True, description="Webhook ID to delete"
        ),
    },
    returns={
        "deleted": ReturnFieldSchema(type="boolean", description="True if successfully deleted"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["airtable.webhooks.list"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# Export all schemas
AIRTABLE_SCHEMAS: dict[str, CapabilitySchema] = {
    "airtable.bases.list": AIRTABLE_BASES_LIST,
    "airtable.tables.list": AIRTABLE_TABLES_LIST,
    "airtable.tables.create": AIRTABLE_TABLES_CREATE,
    "airtable.records.list": AIRTABLE_RECORDS_LIST,
    "airtable.records.get": AIRTABLE_RECORDS_GET,
    "airtable.records.create": AIRTABLE_RECORDS_CREATE,
    "airtable.records.update": AIRTABLE_RECORDS_UPDATE,
    "airtable.records.delete": AIRTABLE_RECORDS_DELETE,
    "airtable.fields.create": AIRTABLE_FIELDS_CREATE,
    "airtable.fields.update": AIRTABLE_FIELDS_UPDATE,
    "airtable.webhooks.list": AIRTABLE_WEBHOOKS_LIST,
    "airtable.webhooks.create": AIRTABLE_WEBHOOKS_CREATE,
    "airtable.webhooks.delete": AIRTABLE_WEBHOOKS_DELETE,
}

__all__ = ["AIRTABLE_SCHEMAS"]
