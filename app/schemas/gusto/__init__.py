"""
Gusto Capability Schemas.

Rich metadata for Gusto payroll and HR operations.
Small business finance teams use Gusto for payroll, benefits, and compliance.

API Docs: https://docs.gusto.com/
"""

from app.schemas.base import CapabilitySchema
from app.schemas.gusto.company import COMPANY_SCHEMAS
from app.schemas.gusto.contractors import CONTRACTOR_SCHEMAS
from app.schemas.gusto.employees import EMPLOYEE_SCHEMAS
from app.schemas.gusto.payroll import PAYROLL_SCHEMAS
from app.schemas.gusto.tax_forms import TAX_FORMS_SCHEMAS

# Export all schemas
GUSTO_SCHEMAS: dict[str, CapabilitySchema] = {
    **COMPANY_SCHEMAS,
    **EMPLOYEE_SCHEMAS,
    **PAYROLL_SCHEMAS,
    **CONTRACTOR_SCHEMAS,
    **TAX_FORMS_SCHEMAS,
}

__all__ = ["GUSTO_SCHEMAS"]
