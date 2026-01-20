"""Gusto Company Capability Schemas."""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
)

GUSTO_COMPANY_GET = CapabilitySchema(
    capability_key="gusto.company.get",
    service="gusto",
    category="company",
    description="Get Gusto company information",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Company UUID"),
        "name": ReturnFieldSchema(type="string", description="Company name"),
        "ein": ReturnFieldSchema(type="string", description="Employer ID Number"),
        "entity_type": ReturnFieldSchema(type="string", description="LLC, Corp, etc."),
        "locations": ReturnFieldSchema(type="array", description="Work locations"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Gusto OAuth not configured",
            recovery_hint="User must connect Gusto account",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

COMPANY_SCHEMAS = {
    "gusto.company.get": GUSTO_COMPANY_GET,
}
