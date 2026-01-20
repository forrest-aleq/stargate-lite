"""
Stripe Terminal Capability Schemas.

Rich metadata for in-person payment hardware and readers.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ READERS ============

READER_CREATE = CapabilitySchema(
    capability_key="stripe.terminal.reader.create",
    service="stripe",
    category="terminal",
    description="Register a Terminal reader",
    description_detailed=(
        "Registers a new Terminal reader to your Stripe account. "
        "Readers are physical devices that accept in-person payments."
    ),
    parameters={
        "registration_code": ParameterSchema(
            type="string",
            required=True,
            description="Registration code from the reader",
            example="puppies-plug-could",
        ),
        "label": ParameterSchema(
            type="string",
            required=False,
            description="Custom label for the reader",
            example="Front Counter",
        ),
        "location": ParameterSchema(
            type="string",
            required=False,
            description="Location ID to assign reader to",
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
            description="Reader ID",
            example="tmr_ABC123",
        ),
        "device_type": ReturnFieldSchema(type="string", description="Reader model"),
        "label": ReturnFieldSchema(type="string", description="Custom label"),
        "location": ReturnFieldSchema(type="string", description="Location ID"),
        "status": ReturnFieldSchema(type="string", description="Reader status"),
        "serial_number": ReturnFieldSchema(type="string", description="Serial number"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Stripe API key not configured",
            recovery_hint="Set STRIPE_SECRET_KEY environment variable",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid registration code",
            recovery_hint="Get code from reader display or documentation",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

READER_RETRIEVE = CapabilitySchema(
    capability_key="stripe.terminal.reader.retrieve",
    service="stripe",
    category="terminal",
    description="Retrieve a Terminal reader",
    parameters={
        "reader_id": ParameterSchema(
            type="string",
            required=True,
            description="Reader ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Reader ID"),
        "device_type": ReturnFieldSchema(type="string", description="Model"),
        "label": ReturnFieldSchema(type="string", description="Label"),
        "location": ReturnFieldSchema(type="string", description="Location"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "ip_address": ReturnFieldSchema(type="string", description="IP address"),
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

READER_UPDATE = CapabilitySchema(
    capability_key="stripe.terminal.reader.update",
    service="stripe",
    category="terminal",
    description="Update a Terminal reader",
    parameters={
        "reader_id": ParameterSchema(
            type="string",
            required=True,
            description="Reader ID to update",
        ),
        "label": ParameterSchema(
            type="string",
            required=False,
            description="New label",
        ),
        "metadata": ParameterSchema(
            type="object",
            required=False,
            description="Updated metadata",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Reader ID"),
        "label": ReturnFieldSchema(type="string", description="Updated label"),
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

READER_DELETE = CapabilitySchema(
    capability_key="stripe.terminal.reader.delete",
    service="stripe",
    category="terminal",
    description="Delete a Terminal reader",
    parameters={
        "reader_id": ParameterSchema(
            type="string",
            required=True,
            description="Reader ID to delete",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Deleted reader ID"),
        "deleted": ReturnFieldSchema(type="boolean", description="True if deleted"),
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

READER_LIST = CapabilitySchema(
    capability_key="stripe.terminal.reader.list",
    service="stripe",
    category="terminal",
    description="List Terminal readers",
    parameters={
        "location": ParameterSchema(
            type="string",
            required=False,
            description="Filter by location ID",
        ),
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["online", "offline"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of readers"),
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

READER_PROCESS_PAYMENT = CapabilitySchema(
    capability_key="stripe.terminal.reader.process_payment",
    service="stripe",
    category="terminal",
    description="Process a payment on a Terminal reader",
    description_detailed=(
        "Initiates a payment on a Terminal reader. The reader will prompt "
        "the customer to present their card."
    ),
    parameters={
        "reader_id": ParameterSchema(
            type="string",
            required=True,
            description="Reader ID to process on",
        ),
        "payment_intent": ParameterSchema(
            type="string",
            required=True,
            description="PaymentIntent ID to collect",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Reader ID"),
        "action": ReturnFieldSchema(type="object", description="Current action"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Reader offline or payment intent invalid",
            recovery_hint="Verify reader is online and payment intent exists",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["stripe.payment.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

READER_CANCEL_ACTION = CapabilitySchema(
    capability_key="stripe.terminal.reader.cancel_action",
    service="stripe",
    category="terminal",
    description="Cancel the current action on a reader",
    parameters={
        "reader_id": ParameterSchema(
            type="string",
            required=True,
            description="Reader ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Reader ID"),
        "action": ReturnFieldSchema(type="object", description="Canceled action"),
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

TERMINAL_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.terminal.reader.create": READER_CREATE,
    "stripe.terminal.reader.retrieve": READER_RETRIEVE,
    "stripe.terminal.reader.update": READER_UPDATE,
    "stripe.terminal.reader.delete": READER_DELETE,
    "stripe.terminal.reader.list": READER_LIST,
    "stripe.terminal.reader.process_payment": READER_PROCESS_PAYMENT,
    "stripe.terminal.reader.cancel_action": READER_CANCEL_ACTION,
}
