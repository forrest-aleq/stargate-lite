"""
FCI Capability Registry.

Registers all FCI primitives, reports, and entity lookup capabilities.
These are registered with lazy loading to avoid circular imports.
"""

import time
from collections.abc import Callable
from typing import Any


def _lazy_fci_handler(method_name: str) -> Callable[..., dict[str, Any]]:
    """
    Create a lazy handler for FCI methods with PostHog tracking.

    This avoids importing FCI at module load time, which would cause
    circular imports with connectors.
    """

    def handler(org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        from structlog.contextvars import get_contextvars

        from app.posthog_client import track_fci_aggregation
        from app.utilities.fci import get_fci_utility

        # Get session_id from logging context (bound in execute router)
        context = get_contextvars()
        session_id = context.get("session_id")

        start_time = time.time()

        fci = get_fci_utility()
        method = getattr(fci, method_name)
        result = method(org_id, user_id, args)

        duration_ms = (time.time() - start_time) * 1000

        # Track FCI aggregation to PostHog
        track_fci_aggregation(
            user_id=user_id,
            org_id=org_id,
            fci_type=method_name.replace("get_", "").replace("lookup_", ""),
            sources=result.get("sources", []),
            session_id=session_id,
            duration_ms=duration_ms,
            partial=result.get("status") == "partial",
        )

        return result  # type: ignore[no-any-return]

    return handler


# =============================================================================
# FCI Primitives
# =============================================================================
FCI_PRIMITIVE_CAPABILITIES = {
    "fci.cash": {
        "handler": _lazy_fci_handler("get_cash"),
        "tool_name": "fci.get_cash",
        "description": "Get total cash position across all connected bank accounts",
        "requires_oauth": False,  # Uses connector credentials
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.ar": {
        "handler": _lazy_fci_handler("get_ar"),
        "tool_name": "fci.get_ar",
        "description": "Get accounts receivable totals with aging buckets",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.ap": {
        "handler": _lazy_fci_handler("get_ap"),
        "tool_name": "fci.get_ap",
        "description": "Get accounts payable totals with aging buckets",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.revenue": {
        "handler": _lazy_fci_handler("get_revenue"),
        "tool_name": "fci.get_revenue",
        "description": "Get revenue totals from P&L and payment systems",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.expenses": {
        "handler": _lazy_fci_handler("get_expenses"),
        "tool_name": "fci.get_expenses",
        "description": "Get expense totals from P&L",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.burn": {
        "handler": _lazy_fci_handler("get_burn"),
        "tool_name": "fci.get_burn",
        "description": "Get monthly burn rate from P&L expenses",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.runway": {
        "handler": _lazy_fci_handler("get_runway"),
        "tool_name": "fci.get_runway",
        "description": "Calculate runway in months (cash / burn)",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.payroll": {
        "handler": _lazy_fci_handler("get_payroll"),
        "tool_name": "fci.get_payroll",
        "description": "Get payroll summary from Gusto",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}

# =============================================================================
# FCI Reports
# =============================================================================
FCI_REPORT_CAPABILITIES = {
    "fci.report.profitloss": {
        "handler": _lazy_fci_handler("get_profit_loss"),
        "tool_name": "fci.get_profit_loss",
        "description": "Get Profit & Loss report",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.report.balancesheet": {
        "handler": _lazy_fci_handler("get_balance_sheet"),
        "tool_name": "fci.get_balance_sheet",
        "description": "Get Balance Sheet report",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.report.ar_aging": {
        "handler": _lazy_fci_handler("get_ar_aging_report"),
        "tool_name": "fci.get_ar_aging_report",
        "description": "Get detailed AR Aging report with customer breakdown",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.report.ap_aging": {
        "handler": _lazy_fci_handler("get_ap_aging_report"),
        "tool_name": "fci.get_ap_aging_report",
        "description": "Get detailed AP Aging report with vendor breakdown",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.report.cashflow": {
        "handler": _lazy_fci_handler("get_cashflow_report"),
        "tool_name": "fci.get_cashflow_report",
        "description": "Get Cash Flow statement",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}

# =============================================================================
# FCI Entity Lookups
# =============================================================================
FCI_ENTITY_CAPABILITIES = {
    "fci.customer.lookup": {
        "handler": _lazy_fci_handler("lookup_customer"),
        "tool_name": "fci.lookup_customer",
        "description": "Look up a customer across all connected services",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.vendor.lookup": {
        "handler": _lazy_fci_handler("lookup_vendor"),
        "tool_name": "fci.lookup_vendor",
        "description": "Look up a vendor across all connected services",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
    "fci.invoice.lookup": {
        "handler": _lazy_fci_handler("lookup_invoice"),
        "tool_name": "fci.lookup_invoice",
        "description": "Look up an invoice across all connected services",
        "requires_oauth": False,
        "service": "fci",
        "credential_type": "customer",
        "supports_delegation": False,
    },
}

# =============================================================================
# Combined FCI Capabilities
# =============================================================================
FCI_CAPABILITIES = {
    **FCI_PRIMITIVE_CAPABILITIES,
    **FCI_REPORT_CAPABILITIES,
    **FCI_ENTITY_CAPABILITIES,
}
