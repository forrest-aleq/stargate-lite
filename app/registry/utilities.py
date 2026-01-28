"""
Utilities Capability Registry
OCR, Hyperbrowser, Web Search, Summarizer, Financial Calculator, Workflow
"""

import threading
from collections.abc import Callable
from typing import Any

from app.connectors.hyperbrowser_v2 import HyperbrowserConnectorV2
from app.connectors.ocr_utility import OCRUtility
from app.utilities import (
    get_financial_calculator_utility,
    get_summarizer_utility,
    get_web_search_utility,
)

# Initialize connectors
ocr_utility = OCRUtility()
hyperbrowser_connector = HyperbrowserConnectorV2()

# Thread-safe lazy initialization for cognitive utilities
_utilities_lock = threading.Lock()
_web_search_utility = None
_summarizer_utility = None
_financial_calc_utility = None


def _lazy_web_search(method_name: str) -> Callable[[str, str, dict[str, Any]], dict[str, Any]]:
    """Create lazy handler for web search utility methods."""

    def handler(org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        global _web_search_utility
        if _web_search_utility is None:
            with _utilities_lock:
                if _web_search_utility is None:
                    _web_search_utility = get_web_search_utility()
        result: dict[str, Any] = getattr(_web_search_utility, method_name)(org_id, user_id, args)
        return result

    return handler


def _lazy_summarizer(method_name: str) -> Callable[[str, str, dict[str, Any]], dict[str, Any]]:
    """Create lazy handler for summarizer utility methods."""

    def handler(org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        global _summarizer_utility
        if _summarizer_utility is None:
            with _utilities_lock:
                if _summarizer_utility is None:
                    _summarizer_utility = get_summarizer_utility()
        result: dict[str, Any] = getattr(_summarizer_utility, method_name)(org_id, user_id, args)
        return result

    return handler


def _lazy_financial_calc(method_name: str) -> Callable[[str, str, dict[str, Any]], dict[str, Any]]:
    """Create lazy handler for financial calculator utility methods."""

    def handler(org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        global _financial_calc_utility
        if _financial_calc_utility is None:
            with _utilities_lock:
                if _financial_calc_utility is None:
                    _financial_calc_utility = get_financial_calculator_utility()
        calc_method = getattr(_financial_calc_utility, method_name)
        result: dict[str, Any] = calc_method(org_id, user_id, args)
        return result

    return handler


UTILITIES_CAPABILITIES = {
    # ========== OCR / DOCUMENT INTELLIGENCE ==========
    "ocr.text.extract": {
        "handler": ocr_utility.extract_text,
        "tool_name": "ocr.extract_text",
        "description": "Extract raw text from document (PDF or image) using deepdoctection",
        "requires_oauth": False,
        "service": "ocr",
        "credential_type": None,
        "supports_delegation": False,
    },
    "ocr.w9.parse": {
        "handler": ocr_utility.parse_w9,
        "tool_name": "ocr.parse_w9",
        "description": "Extract structured data from W-9 form using deepdoctection",
        "requires_oauth": False,
        "service": "ocr",
        "credential_type": None,
        "supports_delegation": False,
    },
    "ocr.invoice.parse": {
        "handler": ocr_utility.parse_invoice,
        "tool_name": "ocr.parse_invoice",
        "description": "Extract structured data from invoice using deepdoctection",
        "requires_oauth": False,
        "service": "ocr",
        "credential_type": None,
        "supports_delegation": False,
    },
    "ocr.bankstatement.parse": {
        "handler": ocr_utility.parse_bank_statement,
        "tool_name": "ocr.parse_bank_statement",
        "description": "Extract structured data from bank statement using deepdoctection",
        "requires_oauth": False,
        "service": "ocr",
        "credential_type": None,
        "supports_delegation": False,
    },
    "ocr.gemini.extract": {
        "handler": ocr_utility.extract_with_gemini,
        "tool_name": "ocr.extract_with_gemini",
        "description": (
            "Extract structured data from document using Gemini Flash - supports custom prompts"
        ),
        "requires_oauth": False,
        "service": "ocr",
        "credential_type": None,
        "supports_delegation": False,
    },
    "ocr.gemini.tables": {
        "handler": ocr_utility.extract_tables,
        "tool_name": "ocr.extract_tables",
        "description": "Extract tables from document using Gemini Flash",
        "requires_oauth": False,
        "service": "ocr",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== HYPERBROWSER / BROWSER AUTOMATION ==========
    "browser.navigate": {
        "handler": hyperbrowser_connector.navigate_to,
        "tool_name": "hyperbrowser.navigate_to",
        "description": (
            "Navigate browser to URL and wait for page load (October 2025 computer use API)"
        ),
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    "browser.click": {
        "handler": hyperbrowser_connector.click_element,
        "tool_name": "hyperbrowser.click_element",
        "description": "Click element by description or CSS selector",
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    "browser.fill_form": {
        "handler": hyperbrowser_connector.fill_form,
        "tool_name": "hyperbrowser.fill_form",
        "description": "Fill form fields with values and optionally submit",
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    "browser.extract_data": {
        "handler": hyperbrowser_connector.extract_data,
        "tool_name": "hyperbrowser.extract_data",
        "description": (
            "Extract data from page using natural language description (returns JSON/CSV/text)"
        ),
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    "browser.download": {
        "handler": hyperbrowser_connector.download_file,
        "tool_name": "hyperbrowser.download_file",
        "description": "Trigger file download by clicking download button/link",
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    "browser.screenshot": {
        "handler": hyperbrowser_connector.take_screenshot,
        "tool_name": "hyperbrowser.take_screenshot",
        "description": "Take screenshot of current browser state (returns base64 PNG)",
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    "powerbi.export": {
        "handler": hyperbrowser_connector.export_powerbi_report,
        "tool_name": "hyperbrowser.export_powerbi_report",
        "description": (
            "Export Power BI report to Excel (automates dashboard -> filters -> export workflow)"
        ),
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    "portal.login": {
        "handler": hyperbrowser_connector.login_to_portal,
        "tool_name": "hyperbrowser.login_to_portal",
        "description": "Login to web portal (bank, ERP, etc.) with optional MFA support",
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    "browser.reset_session": {
        "handler": hyperbrowser_connector.reset_session,
        "tool_name": "hyperbrowser.reset_session",
        "description": "Reset browser session (clear history and state for fresh workflow)",
        "requires_oauth": False,
        "service": "hyperbrowser",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== WEB SEARCH ==========
    "search.web": {
        "handler": _lazy_web_search("search"),
        "tool_name": "web_search.search",
        "description": "Search the web for information (returns results with AI-generated answer)",
        "requires_oauth": False,
        "service": "web_search",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "search.news": {
        "handler": _lazy_web_search("search_news"),
        "tool_name": "web_search.search_news",
        "description": "Search for recent news articles on a topic",
        "requires_oauth": False,
        "service": "web_search",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "search.extract": {
        "handler": _lazy_web_search("extract_content"),
        "tool_name": "web_search.extract_content",
        "description": "Extract content from specific URLs",
        "requires_oauth": False,
        "service": "web_search",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    # ========== SUMMARIZER ==========
    "summarize.text": {
        "handler": _lazy_summarizer("summarize"),
        "tool_name": "summarizer.summarize",
        "description": "Summarize text content (concise, detailed, or executive style)",
        "requires_oauth": False,
        "service": "summarizer",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "summarize.executive": {
        "handler": _lazy_summarizer("executive_summary"),
        "tool_name": "summarizer.executive_summary",
        "description": "Generate executive summary with key takeaways and recommendations",
        "requires_oauth": False,
        "service": "summarizer",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "summarize.bullets": {
        "handler": _lazy_summarizer("extract_bullets"),
        "tool_name": "summarizer.extract_bullets",
        "description": "Extract key points as bullet points from text",
        "requires_oauth": False,
        "service": "summarizer",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "summarize.key_facts": {
        "handler": _lazy_summarizer("extract_key_facts"),
        "tool_name": "summarizer.extract_key_facts",
        "description": "Extract key facts, figures, and named entities from text",
        "requires_oauth": False,
        "service": "summarizer",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    # ========== FINANCIAL CALCULATOR ==========
    "calc.npv": {
        "handler": _lazy_financial_calc("calculate_npv"),
        "tool_name": "financial_calculator.calculate_npv",
        "description": "Calculate Net Present Value (NPV) of cash flows",
        "requires_oauth": False,
        "service": "financial_calculator",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.irr": {
        "handler": _lazy_financial_calc("calculate_irr"),
        "tool_name": "financial_calculator.calculate_irr",
        "description": "Calculate Internal Rate of Return (IRR) of cash flows",
        "requires_oauth": False,
        "service": "financial_calculator",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.amortization": {
        "handler": _lazy_financial_calc("calculate_amortization"),
        "tool_name": "financial_calculator.calculate_amortization",
        "description": "Generate loan amortization schedule",
        "requires_oauth": False,
        "service": "financial_calculator",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.depreciation": {
        "handler": _lazy_financial_calc("calculate_depreciation"),
        "tool_name": "financial_calculator.calculate_depreciation",
        "description": (
            "Calculate asset depreciation (straight-line, declining balance, sum-of-years)"
        ),
        "requires_oauth": False,
        "service": "financial_calculator",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.compound_interest": {
        "handler": _lazy_financial_calc("calculate_compound_interest"),
        "tool_name": "financial_calculator.calculate_compound_interest",
        "description": "Calculate compound interest growth with optional contributions",
        "requires_oauth": False,
        "service": "financial_calculator",
        "credential_type": None,
        "supports_delegation": False,
    },
    "calc.payback_period": {
        "handler": _lazy_financial_calc("calculate_payback_period"),
        "tool_name": "financial_calculator.calculate_payback_period",
        "description": "Calculate investment payback period (simple or discounted)",
        "requires_oauth": False,
        "service": "financial_calculator",
        "credential_type": None,
        "supports_delegation": False,
    },
    # ========== UTILITY METRICS ==========
    "utility.metrics.web_search": {
        "handler": _lazy_web_search("get_metrics"),
        "tool_name": "web_search.get_metrics",
        "description": "Get usage metrics for web search utility",
        "requires_oauth": False,
        "service": "web_search",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "utility.metrics.summarizer": {
        "handler": _lazy_summarizer("get_metrics"),
        "tool_name": "summarizer.get_metrics",
        "description": "Get usage metrics for summarizer utility (tokens, cost)",
        "requires_oauth": False,
        "service": "summarizer",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    # ========== WORKFLOW CAPABILITIES ==========
    "workflow.request_information": {
        "handler": lambda org_id, user_id, args: {"status": "request_sent", "request": args},
        "tool_name": "workflow.request_information",
        "description": "Request additional information from user (orchestration passthrough)",
        "requires_oauth": False,
        "service": "workflow",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "workflow.send_notification": {
        "handler": lambda org_id, user_id, args: {
            "status": "notification_queued",
            "notification": args,
        },
        "tool_name": "workflow.send_notification",
        "description": "Send notification to user (orchestration passthrough)",
        "requires_oauth": False,
        "service": "workflow",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "workflow.await_approval": {
        "handler": lambda org_id, user_id, args: {"status": "approval_pending", "request": args},
        "tool_name": "workflow.await_approval",
        "description": "Request approval from user before proceeding (orchestration passthrough)",
        "requires_oauth": False,
        "service": "workflow",
        "credential_type": "agent",
        "supports_delegation": False,
    },
    "workflow.schedule_task": {
        "handler": lambda org_id, user_id, args: {"status": "task_scheduled", "task": args},
        "tool_name": "workflow.schedule_task",
        "description": "Schedule a task for later execution (orchestration passthrough)",
        "requires_oauth": False,
        "service": "workflow",
        "credential_type": "agent",
        "supports_delegation": False,
    },
}
