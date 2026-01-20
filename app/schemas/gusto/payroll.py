"""Gusto Payroll Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

GUSTO_PAYROLLS_LIST = CapabilitySchema(
    capability_key="gusto.payrolls.list",
    service="gusto",
    category="payroll",
    description="List payroll runs from Gusto",
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
        "processed": ParameterSchema(
            type="boolean", required=False, description="Only return processed payrolls"
        ),
    },
    returns={
        "payrolls": ReturnFieldSchema(
            type="array",
            description="Payrolls with id, pay_period, check_date, totals, status",
        ),
        "count": ReturnFieldSchema(type="integer", description="Payroll count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["gusto.payrolls.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

GUSTO_PAYROLL_GET = CapabilitySchema(
    capability_key="gusto.payroll.get",
    service="gusto",
    category="payroll",
    description="Get payroll details from Gusto",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "payroll_id": ParameterSchema(
            type="string", required=True, description="Payroll UUID"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Payroll UUID"),
        "pay_period": ReturnFieldSchema(type="object", description="Start/end dates"),
        "check_date": ReturnFieldSchema(type="string", description="Check date"),
        "processed": ReturnFieldSchema(type="boolean", description="Is processed"),
        "totals": ReturnFieldSchema(
            type="object",
            description="Gross pay, net pay, employer taxes, employee taxes",
        ),
        "employee_compensations": ReturnFieldSchema(
            type="array",
            description="Per-employee breakdown",
        ),
    },
    idempotent=True,
    has_side_effects=False,
)

GUSTO_PAYROLLS_UPDATE = CapabilitySchema(
    capability_key="gusto.payrolls.update",
    service="gusto",
    category="payroll",
    description="Update payroll with employee hours and compensations",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "payroll_id": ParameterSchema(
            type="string", required=True, description="Payroll UUID to update"
        ),
        "version": ParameterSchema(
            type="string", required=True, description="Current version for optimistic locking"
        ),
        "employee_compensations": ParameterSchema(
            type="array", required=True, description="Employee compensations with hours/wages"
        ),
    },
    returns={
        "payroll_id": ReturnFieldSchema(type="string", description="Updated payroll UUID"),
        "version": ReturnFieldSchema(type="string", description="New version"),
        "employee_compensations": ReturnFieldSchema(
            type="array", description="Updated employee compensations"
        ),
    },
    workflow=WorkflowHints(
        typically_followed_by=["gusto.payrolls.calculate"],
    ),
    idempotent=True,
    has_side_effects=True,
)

GUSTO_PAYROLL_CALCULATE = CapabilitySchema(
    capability_key="gusto.payroll.calculate",
    service="gusto",
    category="payroll",
    description="Calculate payroll (preview before submitting)",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "payroll_id": ParameterSchema(
            type="string", required=True, description="Payroll UUID to calculate"
        ),
    },
    returns={
        "payroll_id": ReturnFieldSchema(type="string", description="Payroll UUID"),
        "totals": ReturnFieldSchema(type="object", description="Calculated totals"),
        "employee_compensations": ReturnFieldSchema(
            type="array", description="Per-employee calculations"
        ),
    },
    workflow=WorkflowHints(
        typically_followed_by=["gusto.payrolls.submit"],
    ),
    idempotent=True,
    has_side_effects=False,
)

GUSTO_PAYROLL_SUBMIT = CapabilitySchema(
    capability_key="gusto.payroll.submit",
    service="gusto",
    category="payroll",
    description="Submit payroll for processing",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "payroll_id": ParameterSchema(
            type="string", required=True, description="Payroll UUID to submit"
        ),
    },
    returns={
        "payroll_id": ReturnFieldSchema(type="string", description="Submitted payroll"),
        "status": ReturnFieldSchema(type="string", description="Should be 'processed'"),
    },
    workflow=WorkflowHints(
        typically_preceded_by=["gusto.payrolls.calculate"],
    ),
    idempotent=False,
    has_side_effects=True,
)

PAYROLL_SCHEMAS = {
    "gusto.payrolls.list": GUSTO_PAYROLLS_LIST,
    "gusto.payroll.get": GUSTO_PAYROLL_GET,
    "gusto.payroll.calculate": GUSTO_PAYROLL_CALCULATE,
    "gusto.payroll.submit": GUSTO_PAYROLL_SUBMIT,
}
