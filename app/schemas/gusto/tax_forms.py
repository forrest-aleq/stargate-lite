"""Gusto Tax Forms Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
)

GUSTO_TAX_FORMS_LIST = CapabilitySchema(
    capability_key="gusto.tax_forms.list",
    service="gusto",
    category="tax_forms",
    description="List tax forms from Gusto (W-2s, 1099s)",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "year": ParameterSchema(type="integer", required=True, description="Tax year (e.g., 2025)"),
    },
    returns={
        "forms": ReturnFieldSchema(
            type="array",
            description="Tax forms (W-2s and 1099s) with employee/contractor, wages, taxes",
        ),
        "count": ReturnFieldSchema(type="integer", description="Form count"),
    },
    idempotent=True,
    has_side_effects=False,
)

TAX_FORMS_SCHEMAS = {
    "gusto.tax_forms.list": GUSTO_TAX_FORMS_LIST,
}
