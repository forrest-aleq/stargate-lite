"""Sage Intacct Company Schemas."""

from app.errors import ErrorCode
from app.schemas.base import CapabilitySchema, ErrorHint, ReturnFieldSchema

SAGE_COMPANY_GET = CapabilitySchema(
    capability_key="sage_intacct.company.get",
    service="sage_intacct",
    category="company",
    description="Get Sage Intacct company information",
    description_detailed="Retrieves company details including name, ID, and configuration.",
    parameters={},
    returns={
        "company_id": ReturnFieldSchema(type="string", description="Company ID"),
        "company_name": ReturnFieldSchema(type="string", description="Company name"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Sage Intacct OAuth not configured",
            recovery_hint="User must connect Sage Intacct account",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

COMPANY_SCHEMAS = {
    "sage_intacct.company.get": SAGE_COMPANY_GET,
}
