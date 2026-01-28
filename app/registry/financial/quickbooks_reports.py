"""
QuickBooks Reports & Organization Capability Registry
"""

from app.connectors.quickbooks import QuickBooksConnector

# Initialize connector
qb_connector = QuickBooksConnector()

QUICKBOOKS_REPORT_CAPABILITIES = {
    # ========== FINANCIAL REPORTS ==========
    "report.profitloss": {
        "handler": qb_connector.get_profit_loss_report,
        "tool_name": "quickbooks.get_profit_loss_report",
        "description": "Get P&L report from QuickBooks",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "report.balancesheet": {
        "handler": qb_connector.get_balance_sheet,
        "tool_name": "quickbooks.get_balance_sheet",
        "description": "Get Balance Sheet report from QuickBooks",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "report.profitloss.detail": {
        "handler": qb_connector.get_profit_loss_detail,
        "tool_name": "quickbooks.get_profit_loss_detail",
        "description": (
            "Get detailed P&L report with individual transactions "
            "by account/category (October 2025 API)"
        ),
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "report.cashflow": {
        "handler": qb_connector.get_cashflow_report,
        "tool_name": "quickbooks.get_cashflow_report",
        "description": "Get Cash Flow Statement report from QuickBooks",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "report.generalledger": {
        "handler": qb_connector.get_general_ledger,
        "tool_name": "quickbooks.get_general_ledger",
        "description": "Get General Ledger report",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== AGING REPORTS ==========
    "report.ar_aging": {
        "handler": qb_connector.get_ar_aging,
        "tool_name": "quickbooks.get_ar_aging",
        "description": "Get AR Aging Summary report",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "report.ap_aging": {
        "handler": qb_connector.get_ap_aging,
        "tool_name": "quickbooks.get_ap_aging",
        "description": "Get AP Aging Summary report",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "report.ar_aging_detail": {
        "handler": qb_connector.get_ar_aging_detail,
        "tool_name": "quickbooks.get_ar_aging_detail",
        "description": "Get detailed AR Aging with individual invoices",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "report.ap_aging_detail": {
        "handler": qb_connector.get_ap_aging_detail,
        "tool_name": "quickbooks.get_ap_aging_detail",
        "description": "Get detailed AP Aging with individual bills",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== BUDGET ==========
    "budget.get": {
        "handler": qb_connector.get_budget,
        "tool_name": "quickbooks.get_budget",
        "description": "Get budget data for variance analysis (actual vs budget comparison)",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== DOCUMENT ==========
    "document.upload": {
        "handler": qb_connector.upload_attachment,
        "tool_name": "quickbooks.upload_attachment",
        "description": (
            "Upload document (W-9, invoice, receipt) and attach to vendor/customer/bill/invoice"
        ),
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== ORGANIZATION: CLASS & DEPARTMENT ==========
    "class.list": {
        "handler": qb_connector.list_classes,
        "tool_name": "quickbooks.list_classes",
        "description": "List classes for class tracking/filtering",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "department.list": {
        "handler": qb_connector.list_departments,
        "tool_name": "quickbooks.list_departments",
        "description": "List departments/locations",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== EMPLOYEE ==========
    "employee.list": {
        "handler": qb_connector.list_employees,
        "tool_name": "quickbooks.list_employees",
        "description": "List employees",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "employee.get": {
        "handler": qb_connector.get_employee,
        "tool_name": "quickbooks.get_employee",
        "description": "Get employee details",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== TERMS & TAX ==========
    "term.list": {
        "handler": qb_connector.list_terms,
        "tool_name": "quickbooks.list_terms",
        "description": "List payment terms",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "taxcode.list": {
        "handler": qb_connector.list_tax_codes,
        "tool_name": "quickbooks.list_tax_codes",
        "description": "List tax codes",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    # ========== COMPANY INFO ==========
    "company.info": {
        "handler": qb_connector.get_company_info,
        "tool_name": "quickbooks.get_company_info",
        "description": "Get company information",
        "requires_oauth": True,
        "service": "quickbooks",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}
