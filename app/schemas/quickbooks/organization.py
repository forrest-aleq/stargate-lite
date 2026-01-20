"""
QuickBooks Organization Capability Schemas.

Rich metadata for company info, employees, classes, departments, terms, tax codes, etc.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ BUDGET ============

BUDGET_GET = CapabilitySchema(
    capability_key="budget.get",
    service="quickbooks",
    category="organization",
    description="Get budget data for variance analysis (actual vs budget comparison)",
    description_detailed=(
        "Retrieves budget data from QuickBooks for comparison against actual performance. "
        "Use for variance analysis and financial planning."
    ),
    parameters={
        "fiscal_year": ParameterSchema(
            type="string",
            required=False,
            description="Fiscal year to retrieve budget for",
            example="2026",
        ),
    },
    returns={
        "budgets": ReturnFieldSchema(
            type="array",
            description="List of budget objects",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of budgets"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        related_capabilities=["report.profitloss", "report.balancesheet"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ DOCUMENT UPLOAD ============

DOCUMENT_UPLOAD = CapabilitySchema(
    capability_key="document.upload",
    service="quickbooks",
    category="organization",
    description="Upload document (W-9, invoice, receipt) and attach to entity",
    description_detailed=(
        "Uploads a document file and attaches it to a QuickBooks entity like a vendor, "
        "customer, bill, or invoice. Useful for storing W-9s, receipts, and source documents."
    ),
    parameters={
        "file_path": ParameterSchema(
            type="string",
            required=True,
            description="Local path to the file to upload",
            example="./documents/vendor_w9.pdf",
        ),
        "entity_type": ParameterSchema(
            type="string",
            required=True,
            description="Type of entity to attach to",
            enum=["Vendor", "Customer", "Bill", "Invoice", "PurchaseOrder"],
            example="Vendor",
        ),
        "entity_id": ParameterSchema(
            type="string",
            required=True,
            description="ID of the entity (with 'qb:' prefix)",
            example="qb:123",
        ),
    },
    returns={
        "attachment_id": ReturnFieldSchema(type="string", description="Attachment ID"),
        "file_name": ReturnFieldSchema(type="string", description="Uploaded file name"),
        "size": ReturnFieldSchema(type="integer", description="File size in bytes"),
        "entity_type": ReturnFieldSchema(type="string", description="Entity type"),
        "entity_id": ReturnFieldSchema(type="string", description="Entity ID"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="File not found or unsupported format",
            recovery_hint="Verify file path and format (PDF, PNG, JPG supported)",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["vendor.create", "bill.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ CLASS & DEPARTMENT ============

CLASS_LIST = CapabilitySchema(
    capability_key="class.list",
    service="quickbooks",
    category="organization",
    description="List classes for class tracking/filtering",
    description_detailed=(
        "Retrieves all classes defined in QuickBooks. Classes are used for categorization "
        "and tracking (e.g., by project, product line, or business segment)."
    ),
    parameters={
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return active classes",
            default=False,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results to return",
            default=100,
        ),
    },
    returns={
        "classes": ReturnFieldSchema(
            type="array",
            description="List of class objects",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of classes"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["report.profitloss", "qb.invoice.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

DEPARTMENT_LIST = CapabilitySchema(
    capability_key="department.list",
    service="quickbooks",
    category="organization",
    description="List departments/locations",
    description_detailed=(
        "Retrieves all departments (locations) defined in QuickBooks. Departments are "
        "used for location tracking and reporting."
    ),
    parameters={
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return active departments",
            default=False,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results to return",
            default=100,
        ),
    },
    returns={
        "departments": ReturnFieldSchema(
            type="array",
            description="List of department objects",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of departments"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["report.profitloss"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ EMPLOYEE ============

EMPLOYEE_LIST = CapabilitySchema(
    capability_key="employee.list",
    service="quickbooks",
    category="organization",
    description="List employees",
    description_detailed=(
        "Retrieves all employees defined in QuickBooks. Employees can be assigned to "
        "time activities and used for tracking billable work."
    ),
    parameters={
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return active employees",
            default=False,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results to return",
            default=100,
        ),
    },
    returns={
        "employees": ReturnFieldSchema(
            type="array",
            description="List of employee objects",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of employees"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["timeactivity.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

EMPLOYEE_GET = CapabilitySchema(
    capability_key="employee.get",
    service="quickbooks",
    category="organization",
    description="Get employee details",
    description_detailed="Retrieves detailed information about a specific employee.",
    parameters={
        "employee_id": ParameterSchema(
            type="string",
            required=True,
            description="Employee ID with 'qb:' prefix",
            example="qb:5",
        ),
    },
    returns={
        "employee_id": ReturnFieldSchema(type="string", description="Employee ID"),
        "display_name": ReturnFieldSchema(type="string", description="Display name"),
        "given_name": ReturnFieldSchema(type="string", description="First name"),
        "family_name": ReturnFieldSchema(type="string", description="Last name"),
        "email": ReturnFieldSchema(type="string", description="Email address"),
        "phone": ReturnFieldSchema(type="string", description="Phone number"),
        "hired_date": ReturnFieldSchema(type="string", description="Hire date"),
        "active": ReturnFieldSchema(type="boolean", description="Is active"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Employee not found",
            recovery_hint="Verify employee_id with employee.list",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ TERMS & TAX ============

TERM_LIST = CapabilitySchema(
    capability_key="term.list",
    service="quickbooks",
    category="organization",
    description="List payment terms",
    description_detailed=(
        "Retrieves all payment terms defined in QuickBooks (e.g., Net 30, Due on Receipt). "
        "Terms define when payment is due and any early payment discounts."
    ),
    parameters={
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return active terms",
            default=False,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results to return",
            default=100,
        ),
    },
    returns={
        "terms": ReturnFieldSchema(
            type="array",
            description="List of term objects",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of terms"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["qb.invoice.create", "bill.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

TAX_CODE_LIST = CapabilitySchema(
    capability_key="taxcode.list",
    service="quickbooks",
    category="organization",
    description="List tax codes",
    description_detailed=(
        "Retrieves all tax codes defined in QuickBooks. Tax codes determine how sales "
        "tax is calculated on transactions."
    ),
    parameters={
        "active_only": ParameterSchema(
            type="boolean",
            required=False,
            description="Only return active tax codes",
            default=False,
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Maximum results to return",
            default=100,
        ),
    },
    returns={
        "tax_codes": ReturnFieldSchema(
            type="array",
            description="List of tax code objects",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of tax codes"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["qb.invoice.create", "salesreceipt.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ COMPANY INFO ============

COMPANY_INFO = CapabilitySchema(
    capability_key="company.info",
    service="quickbooks",
    category="organization",
    description="Get company information",
    description_detailed=(
        "Retrieves company profile information including name, address, contact details, "
        "and fiscal year settings."
    ),
    parameters={},
    returns={
        "company_name": ReturnFieldSchema(type="string", description="Company name"),
        "legal_name": ReturnFieldSchema(type="string", description="Legal business name"),
        "company_addr": ReturnFieldSchema(type="object", description="Company address"),
        "email": ReturnFieldSchema(type="string", description="Company email"),
        "phone": ReturnFieldSchema(type="string", description="Company phone"),
        "fiscal_year_start": ReturnFieldSchema(
            type="string",
            description="Fiscal year start month",
        ),
        "country": ReturnFieldSchema(type="string", description="Country code"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="QuickBooks not connected",
            recovery_hint="Complete OAuth flow",
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

ORGANIZATION_SCHEMAS: dict[str, CapabilitySchema] = {
    "budget.get": BUDGET_GET,
    "document.upload": DOCUMENT_UPLOAD,
    "class.list": CLASS_LIST,
    "department.list": DEPARTMENT_LIST,
    "employee.list": EMPLOYEE_LIST,
    "employee.get": EMPLOYEE_GET,
    "term.list": TERM_LIST,
    "taxcode.list": TAX_CODE_LIST,
    "company.info": COMPANY_INFO,
}
