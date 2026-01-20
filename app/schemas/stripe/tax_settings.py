"""
Stripe Tax Settings & Registrations Capability Schemas.

Rich metadata for tax configuration and jurisdiction registrations.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

# ============ TAX SETTINGS ============

TAX_SETTINGS_RETRIEVE = CapabilitySchema(
    capability_key="stripe.tax.settings.retrieve",
    service="stripe",
    category="tax",
    description="Retrieve tax settings",
    description_detailed=(
        "Retrieves your Stripe Tax settings including head office location "
        "and default tax behavior."
    ),
    parameters={},
    returns={
        "defaults": ReturnFieldSchema(type="object", description="Default settings"),
        "head_office": ReturnFieldSchema(type="object", description="Head office"),
        "status_details": ReturnFieldSchema(type="object", description="Status"),
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

TAX_SETTINGS_UPDATE = CapabilitySchema(
    capability_key="stripe.tax.settings.update",
    service="stripe",
    category="tax",
    description="Update tax settings",
    parameters={
        "defaults": ParameterSchema(
            type="object",
            required=False,
            description="Update default settings",
        ),
        "head_office": ParameterSchema(
            type="object",
            required=False,
            description="Update head office location",
        ),
    },
    returns={
        "defaults": ReturnFieldSchema(type="object", description="Updated defaults"),
        "head_office": ReturnFieldSchema(type="object", description="Updated office"),
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

# ============ TAX REGISTRATIONS ============

TAX_REGISTRATION_CREATE = CapabilitySchema(
    capability_key="stripe.tax.registration.create",
    service="stripe",
    category="tax",
    description="Create a tax registration",
    description_detailed=(
        "Creates a tax registration indicating you're registered to collect "
        "tax in a jurisdiction. Required for accurate tax calculations."
    ),
    parameters={
        "country": ParameterSchema(
            type="string",
            required=True,
            description="Two-letter country code",
            example="US",
        ),
        "active_from": ParameterSchema(
            type="string",
            required=True,
            description="When registration becomes active",
            enum=["now"],
            example="now",
        ),
        "country_options": ParameterSchema(
            type="object",
            required=True,
            description="Country-specific options",
            example={"us": {"state": "CA", "type": "state_sales_tax"}},
        ),
        "expires_at": ParameterSchema(
            type="integer",
            required=False,
            description="When registration expires",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Registration ID"),
        "country": ReturnFieldSchema(type="string", description="Country"),
        "status": ReturnFieldSchema(type="string", description="Status"),
        "active_from": ReturnFieldSchema(type="integer", description="Active from"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid country or registration options",
            recovery_hint="Check country code and options format",
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

TAX_REGISTRATION_RETRIEVE = CapabilitySchema(
    capability_key="stripe.tax.registration.retrieve",
    service="stripe",
    category="tax",
    description="Retrieve a tax registration",
    parameters={
        "registration_id": ParameterSchema(
            type="string",
            required=True,
            description="Registration ID",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Registration ID"),
        "country": ReturnFieldSchema(type="string", description="Country"),
        "status": ReturnFieldSchema(type="string", description="Status"),
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

TAX_REGISTRATION_UPDATE = CapabilitySchema(
    capability_key="stripe.tax.registration.update",
    service="stripe",
    category="tax",
    description="Update a tax registration",
    parameters={
        "registration_id": ParameterSchema(
            type="string",
            required=True,
            description="Registration ID to update",
        ),
        "expires_at": ParameterSchema(
            type="integer",
            required=False,
            description="New expiration timestamp",
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Registration ID"),
        "expires_at": ReturnFieldSchema(type="integer", description="New expiration"),
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

TAX_REGISTRATION_LIST = CapabilitySchema(
    capability_key="stripe.tax.registration.list",
    service="stripe",
    category="tax",
    description="List tax registrations",
    parameters={
        "status": ParameterSchema(
            type="string",
            required=False,
            description="Filter by status",
            enum=["active", "expired", "scheduled"],
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum number to return",
            default=10,
        ),
    },
    returns={
        "data": ReturnFieldSchema(type="array", description="List of registrations"),
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

TAX_SETTINGS_SCHEMAS: dict[str, CapabilitySchema] = {
    "stripe.tax.settings.retrieve": TAX_SETTINGS_RETRIEVE,
    "stripe.tax.settings.update": TAX_SETTINGS_UPDATE,
    "stripe.tax.registration.create": TAX_REGISTRATION_CREATE,
    "stripe.tax.registration.retrieve": TAX_REGISTRATION_RETRIEVE,
    "stripe.tax.registration.update": TAX_REGISTRATION_UPDATE,
    "stripe.tax.registration.list": TAX_REGISTRATION_LIST,
}
