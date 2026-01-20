"""Gusto Contractor Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
)

GUSTO_CONTRACTORS_LIST = CapabilitySchema(
    capability_key="gusto.contractors.list",
    service="gusto",
    category="contractors",
    description="List contractors from Gusto",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
    },
    returns={
        "contractors": ReturnFieldSchema(
            type="array",
            description="Contractors with id, name, email, type (individual/business)",
        ),
        "count": ReturnFieldSchema(type="integer", description="Contractor count"),
    },
    idempotent=True,
    has_side_effects=False,
)

GUSTO_CONTRACTOR_CREATE = CapabilitySchema(
    capability_key="gusto.contractor.create",
    service="gusto",
    category="contractors",
    description="Create a contractor in Gusto",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "first_name": ParameterSchema(
            type="string", required=True, description="Contractor first name"
        ),
        "last_name": ParameterSchema(
            type="string", required=True, description="Contractor last name"
        ),
        "start_date": ParameterSchema(
            type="string", required=True, description="Contract start date (YYYY-MM-DD)"
        ),
        "type": ParameterSchema(
            type="string",
            required=False,
            enum=["Individual", "Business"],
            description="Contractor type",
        ),
        "wage_type": ParameterSchema(
            type="string",
            required=False,
            enum=["Hourly", "Fixed"],
            description="How contractor is paid",
        ),
        "hourly_rate": ParameterSchema(
            type="string", required=False, description="Hourly rate if wage_type is Hourly"
        ),
        "self_onboarding": ParameterSchema(
            type="boolean", required=False, description="Allow contractor to self-onboard"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Created contractor UUID"),
    },
    idempotent=False,
    has_side_effects=True,
)

GUSTO_CONTRACTOR_PAYMENTS_LIST = CapabilitySchema(
    capability_key="gusto.contractor_payments.list",
    service="gusto",
    category="contractors",
    description="List contractor payments from Gusto",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "start_date": ParameterSchema(
            type="string", required=False, description="Filter start date (YYYY-MM-DD)"
        ),
        "end_date": ParameterSchema(
            type="string", required=False, description="Filter end date (YYYY-MM-DD)"
        ),
        "contractor_id": ParameterSchema(
            type="string", required=False, description="Filter by contractor UUID"
        ),
    },
    returns={
        "payments": ReturnFieldSchema(
            type="array",
            description="Payments with contractor, date, amount, reimbursements",
        ),
        "count": ReturnFieldSchema(type="integer", description="Payment count"),
    },
    idempotent=True,
    has_side_effects=False,
)

CONTRACTOR_SCHEMAS = {
    "gusto.contractors.list": GUSTO_CONTRACTORS_LIST,
    "gusto.contractor.create": GUSTO_CONTRACTOR_CREATE,
    "gusto.contractor_payments.list": GUSTO_CONTRACTOR_PAYMENTS_LIST,
}
