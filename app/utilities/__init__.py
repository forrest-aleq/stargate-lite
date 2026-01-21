"""
Stargate Lite Utilities Package

Cognitive utilities that extend Stargate beyond API connectors into
AI-powered research, analysis, and generation capabilities.

Unlike connectors (which wrap external SaaS APIs with customer OAuth),
utilities use Aleq's own API keys and provide cognitive augmentation.

FCI (Financial Command Interface) utilities aggregate data from multiple
connectors into unified financial primitives (@cash, @ar, @ap, etc.).
"""

from app.utilities.base import BaseUtility, MultiProviderUtility
from app.utilities.fci import FCIUtility, get_fci_utility
from app.utilities.financial_calculator import (
    FinancialCalculatorUtility,
    get_financial_calculator_utility,
)
from app.utilities.financial_ops import (
    FinancialOpsUtility,
    get_financial_ops_utility,
)
from app.utilities.summarizer import SummarizerUtility, get_summarizer_utility
from app.utilities.web_search import WebSearchUtility, get_web_search_utility

__all__ = [
    "BaseUtility",
    "FCIUtility",
    "FinancialCalculatorUtility",
    "FinancialOpsUtility",
    "MultiProviderUtility",
    "SummarizerUtility",
    "WebSearchUtility",
    "get_fci_utility",
    "get_financial_calculator_utility",
    "get_financial_ops_utility",
    "get_summarizer_utility",
    "get_web_search_utility",
]
