"""
Sage Intacct Capability Schemas.

Rich metadata for Sage Intacct ERP operations via REST API.
Mid-market finance teams use Sage Intacct for GL, AP, AR, and cash management.

Sage Intacct is a Tier 2 system (24K instances in training data).
Total: 25 capabilities across GL, AP, AR, Cash Management, and Reports.
"""

from app.schemas.sage_intacct.accounts_payable import AP_SCHEMAS
from app.schemas.sage_intacct.accounts_receivable import AR_SCHEMAS
from app.schemas.sage_intacct.cash_management import CASH_SCHEMAS
from app.schemas.sage_intacct.company import COMPANY_SCHEMAS
from app.schemas.sage_intacct.general_ledger import GL_SCHEMAS
from app.schemas.sage_intacct.reports import REPORT_SCHEMAS

# Export all schemas
SAGE_INTACCT_SCHEMAS = {
    **COMPANY_SCHEMAS,
    **GL_SCHEMAS,
    **AP_SCHEMAS,
    **AR_SCHEMAS,
    **CASH_SCHEMAS,
    **REPORT_SCHEMAS,
}

__all__ = ["SAGE_INTACCT_SCHEMAS"]
