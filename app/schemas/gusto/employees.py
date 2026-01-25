"""Gusto Employee Capability Schemas."""

from app.schemas.base import (
    CapabilitySchema,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

GUSTO_EMPLOYEES_LIST = CapabilitySchema(
    capability_key="gusto.employees.list",
    service="gusto",
    category="employees",
    description="List employees from Gusto",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "terminated": ParameterSchema(
            type="boolean", required=False, description="Include terminated employees"
        ),
    },
    returns={
        "employees": ReturnFieldSchema(
            type="array",
            description="Employees with id, first_name, last_name, email, department",
        ),
        "count": ReturnFieldSchema(type="integer", description="Employee count"),
    },
    workflow=WorkflowHints(
        typically_followed_by=["gusto.employees.get", "gusto.payrolls.list"],
    ),
    idempotent=True,
    has_side_effects=False,
)

GUSTO_EMPLOYEE_GET = CapabilitySchema(
    capability_key="gusto.employee.get",
    service="gusto",
    category="employees",
    description="Get employee details from Gusto",
    parameters={
        "employee_id": ParameterSchema(
            type="string", required=True, description="Gusto employee UUID"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Employee UUID"),
        "first_name": ReturnFieldSchema(type="string", description="First name"),
        "last_name": ReturnFieldSchema(type="string", description="Last name"),
        "email": ReturnFieldSchema(type="string", description="Email"),
        "ssn": ReturnFieldSchema(type="string", description="Last 4 of SSN"),
        "date_of_birth": ReturnFieldSchema(type="string", description="DOB"),
        "jobs": ReturnFieldSchema(type="array", description="Job assignments"),
        "compensations": ReturnFieldSchema(type="array", description="Pay rates"),
        "home_address": ReturnFieldSchema(type="object", description="Address"),
    },
    idempotent=True,
    has_side_effects=False,
)

GUSTO_EMPLOYEE_CREATE = CapabilitySchema(
    capability_key="gusto.employee.create",
    service="gusto",
    category="employees",
    description="Create an employee in Gusto",
    parameters={
        "company_id": ParameterSchema(
            type="string", required=True, description="Gusto company UUID"
        ),
        "first_name": ParameterSchema(
            type="string", required=True, description="Employee first name"
        ),
        "last_name": ParameterSchema(
            type="string", required=True, description="Employee last name"
        ),
        "email": ParameterSchema(
            type="string", required=True, description="Employee email address"
        ),
        "date_of_birth": ParameterSchema(
            type="string", required=False, description="Date of birth (YYYY-MM-DD)"
        ),
        "ssn": ParameterSchema(type="string", required=False, description="Social Security Number"),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Created employee UUID"),
        "status": ReturnFieldSchema(type="string", description="Should be 'created'"),
    },
    idempotent=False,
    has_side_effects=True,
)

GUSTO_EMPLOYEE_UPDATE = CapabilitySchema(
    capability_key="gusto.employee.update",
    service="gusto",
    category="employees",
    description="Update an employee in Gusto",
    parameters={
        "employee_id": ParameterSchema(
            type="string", required=True, description="Gusto employee UUID"
        ),
        "version": ParameterSchema(
            type="string", required=True, description="Current version for optimistic locking"
        ),
        "first_name": ParameterSchema(
            type="string", required=False, description="Employee first name"
        ),
        "last_name": ParameterSchema(
            type="string", required=False, description="Employee last name"
        ),
        "email": ParameterSchema(
            type="string", required=False, description="Employee email address"
        ),
        "date_of_birth": ParameterSchema(
            type="string", required=False, description="Date of birth (YYYY-MM-DD)"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Employee UUID"),
        "version": ReturnFieldSchema(type="string", description="New version"),
    },
    idempotent=True,
    has_side_effects=True,
)

GUSTO_EMPLOYEE_TERMINATE = CapabilitySchema(
    capability_key="gusto.employee.terminate",
    service="gusto",
    category="employees",
    description="Terminate an employee in Gusto",
    parameters={
        "employee_id": ParameterSchema(
            type="string", required=True, description="Gusto employee UUID"
        ),
        "effective_date": ParameterSchema(
            type="string", required=True, description="Last day of work (YYYY-MM-DD)"
        ),
        "run_termination_payroll": ParameterSchema(
            type="boolean", required=False, description="Run a separate termination payroll"
        ),
    },
    returns={
        "id": ReturnFieldSchema(type="string", description="Termination UUID"),
        "employee_id": ReturnFieldSchema(type="string", description="Employee UUID"),
        "effective_date": ReturnFieldSchema(type="string", description="Termination date"),
    },
    idempotent=False,
    has_side_effects=True,
)

EMPLOYEE_SCHEMAS = {
    "gusto.employees.list": GUSTO_EMPLOYEES_LIST,
    "gusto.employee.get": GUSTO_EMPLOYEE_GET,
    "gusto.employee.create": GUSTO_EMPLOYEE_CREATE,
    "gusto.employee.update": GUSTO_EMPLOYEE_UPDATE,
    "gusto.employee.terminate": GUSTO_EMPLOYEE_TERMINATE,
}
