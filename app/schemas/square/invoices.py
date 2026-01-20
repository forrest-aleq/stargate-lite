"""Square Invoice Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

SQUARE_INVOICES_LIST = CapabilitySchema(
    capability_key="square.invoices.list",
    service="square",
    category="invoices",
    description="List invoices from Square",
    parameters={
        "location_id": ParameterSchema(
            type="string", required=True, description="Location ID"
        ),
        "cursor": ParameterSchema(
            type="string", required=False, description="Pagination cursor"
        ),
        "limit": ParameterSchema(
            type="integer", required=False, description="Maximum invoices to return"
        ),
    },
    returns={
        "invoices": ReturnFieldSchema(
            type="array",
            description="Invoices with id, invoice_number, status, payment_requests",
        ),
        "cursor": ReturnFieldSchema(type="string", description="Pagination cursor"),
    },
    idempotent=True,
    has_side_effects=False,
)

SQUARE_INVOICES_GET = CapabilitySchema(
    capability_key="square.invoices.get",
    service="square",
    category="invoices",
    description="Get invoice details from Square",
    parameters={
        "invoice_id": ParameterSchema(
            type="string", required=True, description="Square invoice ID"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Invoice ID"),
        "invoice_number": ReturnFieldSchema(type="string", description="Invoice number"),
        "status": ReturnFieldSchema(type="string", description="DRAFT, SCHEDULED, etc."),
        "version": ReturnFieldSchema(type="integer", description="Invoice version"),
        "primary_recipient": ReturnFieldSchema(type="object", description="Customer info"),
        "payment_requests": ReturnFieldSchema(type="array", description="Payment requests"),
    },
    idempotent=True,
    has_side_effects=False,
)

SQUARE_INVOICES_CREATE = CapabilitySchema(
    capability_key="square.invoices.create",
    service="square",
    category="invoices",
    description="Create an invoice in Square",
    parameters={
        "idempotency_key": ParameterSchema(
            type="string", required=True, description="Unique key for idempotency"
        ),
        "location_id": ParameterSchema(
            type="string", required=True, description="Location ID"
        ),
        "order_id": ParameterSchema(
            type="string", required=True, description="Order ID to invoice"
        ),
        "primary_recipient": ParameterSchema(
            type="object", required=True, description="Customer recipient"
        ),
        "payment_requests": ParameterSchema(
            type="array", required=True, description="Payment request details"
        ),
        "delivery_method": ParameterSchema(
            type="string",
            required=False,
            enum=["EMAIL", "SMS", "SHARE_MANUALLY"],
            description="How to deliver the invoice",
        ),
    },
    returns={
        "invoice_id": ReturnFieldSchema(type="string", description="Created invoice ID"),
        "invoice_number": ReturnFieldSchema(type="string", description="Invoice number"),
        "status": ReturnFieldSchema(type="string", description="DRAFT, UNPAID, etc."),
    },
    idempotent=True,
    has_side_effects=True,
)

SQUARE_INVOICES_UPDATE = CapabilitySchema(
    capability_key="square.invoices.update",
    service="square",
    category="invoices",
    description="Update an invoice in Square",
    parameters={
        "invoice_id": ParameterSchema(
            type="string", required=True, description="Square invoice ID"
        ),
        "version": ParameterSchema(
            type="integer", required=True, description="Current invoice version"
        ),
        "invoice": ParameterSchema(
            type="object", required=True, description="Invoice fields to update"
        ),
        "idempotency_key": ParameterSchema(
            type="string", required=False, description="Unique key for idempotency"
        ),
    },
    returns={
        "invoice_id": ReturnFieldSchema(type="string", description="Updated invoice ID"),
        "version": ReturnFieldSchema(type="integer", description="New version"),
    },
    idempotent=True,
    has_side_effects=True,
)

SQUARE_INVOICES_PUBLISH = CapabilitySchema(
    capability_key="square.invoices.publish",
    service="square",
    category="invoices",
    description="Publish a draft invoice to send to customer",
    parameters={
        "invoice_id": ParameterSchema(
            type="string", required=True, description="Square invoice ID"
        ),
        "version": ParameterSchema(
            type="integer", required=True, description="Current invoice version"
        ),
        "idempotency_key": ParameterSchema(
            type="string", required=False, description="Unique key for idempotency"
        ),
    },
    returns={
        "invoice_id": ReturnFieldSchema(type="string", description="Published invoice ID"),
        "status": ReturnFieldSchema(
            type="string", description="Should be UNPAID or SCHEDULED"
        ),
        "public_url": ReturnFieldSchema(type="string", description="Customer payment URL"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["square.invoices.create"],
    ),
    idempotent=True,
    has_side_effects=True,
)

SQUARE_INVOICES_CANCEL = CapabilitySchema(
    capability_key="square.invoices.cancel",
    service="square",
    category="invoices",
    description="Cancel a published invoice",
    parameters={
        "invoice_id": ParameterSchema(
            type="string", required=True, description="Square invoice ID"
        ),
        "version": ParameterSchema(
            type="integer", required=True, description="Current invoice version"
        ),
    },
    returns={
        "invoice_id": ReturnFieldSchema(type="string", description="Cancelled invoice ID"),
        "status": ReturnFieldSchema(type="string", description="Should be CANCELED"),
    },
    idempotent=True,
    has_side_effects=True,
)

INVOICE_SCHEMAS = {
    "square.invoices.list": SQUARE_INVOICES_LIST,
    "square.invoices.get": SQUARE_INVOICES_GET,
    "square.invoices.create": SQUARE_INVOICES_CREATE,
    "square.invoices.update": SQUARE_INVOICES_UPDATE,
    "square.invoices.publish": SQUARE_INVOICES_PUBLISH,
    "square.invoices.cancel": SQUARE_INVOICES_CANCEL,
}
