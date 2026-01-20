"""
Utility Test Suite
Tests for Phase 1 cognitive utilities: web_search, summarizer, financial_calculator
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# === FIXTURES ===


@pytest.fixture
def mock_tavily_response():
    """Standard Tavily search response."""
    return {
        "results": [
            {
                "title": "Test Result",
                "url": "https://test.com",
                "content": "Test content",
                "score": 0.9,
            }
        ],
        "answer": "Test answer",
        "response_time": 0.5,
    }


@pytest.fixture
def mock_tavily_extract_response():
    """Standard Tavily extract response."""
    return {
        "results": [{"url": "https://test.com", "raw_content": "Extracted content"}],
        "failed_results": [],
    }


@pytest.fixture
def mock_claude_response():
    """Standard Claude API response mock."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test summary")]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    return mock_response


@pytest.fixture
def reset_utility_singletons():
    """Reset singleton instances between tests."""
    import app.utilities.financial_calculator as fc
    import app.utilities.summarizer as summ
    import app.utilities.web_search as ws

    ws._web_search_utility = None
    summ._summarizer_utility = None
    fc._financial_calculator_utility = None
    yield
    ws._web_search_utility = None
    summ._summarizer_utility = None
    fc._financial_calculator_utility = None


# === FINANCIAL CALCULATOR TESTS (No mocking needed - pure Python) ===


class TestFinancialCalculatorNPV:
    """NPV calculation tests - pure Python, no external deps."""

    def test_npv_positive_returns_profitable(self):
        """NPV > 0 should mark is_profitable=True."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_npv(
            "org", "user", {"cash_flows": [-1000, 400, 500, 600], "discount_rate": 0.10}
        )

        assert result["status"] == "success"
        assert result["is_profitable"] is True
        assert result["npv"] > 0

    def test_npv_negative_returns_not_profitable(self):
        """NPV < 0 should mark is_profitable=False."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_npv(
            "org", "user", {"cash_flows": [-1000, 100, 100, 100], "discount_rate": 0.10}
        )

        assert result["status"] == "success"
        assert result["is_profitable"] is False
        assert result["npv"] < 0

    def test_npv_missing_cash_flows_raises_validation_error(self):
        """Missing cash_flows should raise ValidationError."""
        from app.errors import ValidationError
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        with pytest.raises(ValidationError):
            calc.calculate_npv("org", "user", {"discount_rate": 0.10})

    def test_npv_missing_discount_rate_raises_validation_error(self):
        """Missing discount_rate should raise ValidationError."""
        from app.errors import ValidationError
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        with pytest.raises(ValidationError):
            calc.calculate_npv("org", "user", {"cash_flows": [-1000, 500, 500]})

    def test_npv_zero_discount_rate(self):
        """Zero discount rate should work (sum of cash flows)."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_npv(
            "org", "user", {"cash_flows": [-1000, 500, 500, 500], "discount_rate": 0.0}
        )

        assert result["status"] == "success"
        assert result["npv"] == 500.0  # -1000 + 500 + 500 + 500

    def test_npv_present_values_calculated_correctly(self):
        """Each present value should be cf / (1+r)^n."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_npv(
            "org", "user", {"cash_flows": [-1000, 1100], "discount_rate": 0.10}
        )

        # PV of first cash flow (period 0) = -1000
        # PV of second cash flow (period 1) = 1100 / 1.1 = 1000
        assert len(result["present_values"]) == 2
        assert result["present_values"][0] == -1000.0
        assert result["present_values"][1] == 1000.0


class TestFinancialCalculatorIRR:
    """IRR calculation tests."""

    def test_irr_converges_for_standard_case(self):
        """Standard investment should converge."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_irr("org", "user", {"cash_flows": [-1000, 300, 400, 500, 200]})

        assert result["status"] == "success"
        assert result["converged"] is True
        assert 0 < result["irr"] < 1

    def test_irr_fewer_than_2_cash_flows_raises_error(self):
        """Need at least 2 cash flows for IRR."""
        from app.errors import ValidationError
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        with pytest.raises(ValidationError):
            calc.calculate_irr("org", "user", {"cash_flows": [-1000]})

    def test_irr_percentage_format(self):
        """IRR percentage should be formatted as 'XX.XX%'."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_irr("org", "user", {"cash_flows": [-1000, 1200]})

        assert "%" in result["irr_percentage"]
        assert result["irr_percentage"].endswith("%")


class TestFinancialCalculatorAmortization:
    """Amortization schedule tests."""

    def test_amortization_monthly_payment_formula(self):
        """Monthly payment should match amortization formula."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_amortization(
            "org", "user", {"principal": 100000, "annual_rate": 0.06, "term_months": 360}
        )

        assert result["status"] == "success"
        # Standard 30-year mortgage at 6% should be ~$600/month
        assert 590 < result["monthly_payment"] < 610

    def test_amortization_zero_interest_rate(self):
        """Zero rate: payment = principal / term_months."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_amortization(
            "org", "user", {"principal": 12000, "annual_rate": 0.0, "term_months": 12}
        )

        assert result["monthly_payment"] == 1000.0
        assert result["total_interest"] == 0.0

    def test_amortization_extra_payment_shortens_term(self):
        """Extra payments should reduce actual_term_months."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        # Without extra payment
        result_normal = calc.calculate_amortization(
            "org", "user", {"principal": 10000, "annual_rate": 0.12, "term_months": 24}
        )

        # With extra payment
        result_extra = calc.calculate_amortization(
            "org",
            "user",
            {"principal": 10000, "annual_rate": 0.12, "term_months": 24, "extra_payment": 100},
        )

        assert result_extra["actual_term_months"] < result_normal["actual_term_months"]

    def test_amortization_schedule_has_correct_structure(self):
        """Schedule entries should have required fields."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_amortization(
            "org", "user", {"principal": 1000, "annual_rate": 0.12, "term_months": 12}
        )

        assert len(result["schedule"]) > 0
        entry = result["schedule"][0]
        assert "month" in entry
        assert "date" in entry
        assert "payment" in entry
        assert "principal" in entry
        assert "interest" in entry
        assert "balance" in entry


class TestFinancialCalculatorDepreciation:
    """Depreciation calculation tests."""

    def test_straight_line_depreciation(self):
        """Straight line: equal depreciation each year."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_depreciation(
            "org",
            "user",
            {"cost": 10000, "salvage_value": 0, "useful_life_years": 5, "method": "straight_line"},
        )

        assert result["status"] == "success"
        assert result["total_depreciation"] == 10000.0
        # Each year should have equal depreciation
        for entry in result["schedule"]:
            assert entry["depreciation"] == 2000.0

    def test_declining_balance_depreciation(self):
        """Double declining: higher early, respects salvage."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_depreciation(
            "org",
            "user",
            {
                "cost": 10000,
                "salvage_value": 1000,
                "useful_life_years": 5,
                "method": "declining_balance",
            },
        )

        assert result["status"] == "success"
        # First year depreciation should be highest
        assert result["schedule"][0]["depreciation"] > result["schedule"][-1]["depreciation"]
        # Final book value should be >= salvage
        assert result["schedule"][-1]["book_value"] >= 1000

    def test_sum_of_years_depreciation(self):
        """Sum of years: accelerated but consistent."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_depreciation(
            "org",
            "user",
            {"cost": 10000, "salvage_value": 0, "useful_life_years": 5, "method": "sum_of_years"},
        )

        assert result["status"] == "success"
        # Sum of years for 5 years = 15, first year gets 5/15 of depreciable amount
        assert abs(result["schedule"][0]["depreciation"] - 3333.33) < 1

    def test_unknown_method_raises_error(self):
        """Unknown method should raise ValidationError."""
        from app.errors import ValidationError
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        with pytest.raises(ValidationError):
            calc.calculate_depreciation(
                "org",
                "user",
                {
                    "cost": 10000,
                    "salvage_value": 0,
                    "useful_life_years": 5,
                    "method": "unknown_method",
                },
            )


class TestFinancialCalculatorCompoundInterest:
    """Compound interest tests."""

    def test_compound_interest_no_contributions(self):
        """Basic compound interest formula."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_compound_interest(
            "org",
            "user",
            {
                "principal": 1000,
                "annual_rate": 0.10,
                "years": 1,
                "compounds_per_year": 1,
                "monthly_contribution": 0,
            },
        )

        assert result["status"] == "success"
        assert result["final_value"] == 1100.0  # 1000 * 1.10

    def test_compound_interest_with_monthly_contributions(self):
        """Contributions should be added each period."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_compound_interest(
            "org",
            "user",
            {
                "principal": 1000,
                "annual_rate": 0.12,
                "years": 1,
                "compounds_per_year": 12,
                "monthly_contribution": 100,
            },
        )

        assert result["status"] == "success"
        assert result["total_contributions"] == 2200.0  # 1000 + 12*100
        assert result["final_value"] > result["total_contributions"]  # Interest earned


class TestFinancialCalculatorPayback:
    """Payback period tests."""

    def test_payback_period_interpolation(self):
        """Fractional period should be interpolated."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_payback_period(
            "org", "user", {"initial_investment": 1000, "cash_flows": [400, 400, 400]}
        )

        assert result["status"] == "success"
        # Payback should be between 2 and 3 years (2.5)
        assert 2 < result["payback_period"] < 3

    def test_payback_never_recovers(self):
        """If never recovers, payback_period=None."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_payback_period(
            "org", "user", {"initial_investment": 1000, "cash_flows": [100, 100, 100]}
        )

        assert result["payback_period"] is None
        assert result["recovers_investment"] is False

    def test_discounted_payback(self):
        """Discounted payback uses present values."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.calculate_payback_period(
            "org",
            "user",
            {
                "initial_investment": 1000,
                "cash_flows": [400, 400, 400, 400],
                "discounted": True,
                "discount_rate": 0.10,
            },
        )

        assert result["status"] == "success"
        assert result["discounted"] is True
        # Discounted payback should be longer than undiscounted
        assert result["payback_period"] is not None


# === WEB SEARCH TESTS (Mock Tavily API) ===


class TestWebSearchInitialization:
    """Lazy initialization tests."""

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_api_key_raises_error(self, reset_utility_singletons):
        """Missing TAVILY_API_KEY should raise an error on first use."""
        from app.errors import ExecutionError
        from app.utilities.web_search import WebSearchUtility

        utility = WebSearchUtility()
        # CredentialMissingError gets wrapped in ExecutionError by base class
        with pytest.raises(ExecutionError):
            utility.search("org", "user", {"query": "test"})

    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_initialization_succeeds_with_key(self, reset_utility_singletons):
        """Valid key should initialize successfully."""
        from app.utilities.web_search import WebSearchUtility

        utility = WebSearchUtility()
        utility._ensure_initialized()
        assert utility._initialized is True
        assert "tavily" in utility._available_providers


class TestWebSearchSearch:
    """search() method tests."""

    @patch("app.utilities.web_search.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_search_success(self, mock_post, mock_tavily_response, reset_utility_singletons):
        """Successful search returns results and answer."""
        from app.utilities.web_search import WebSearchUtility

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_tavily_response

        utility = WebSearchUtility()
        result = utility.search("org", "user", {"query": "test query"})

        assert result["status"] == "success"
        assert len(result["results"]) == 1
        assert result["answer"] == "Test answer"

    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_search_missing_query_raises_error(self, reset_utility_singletons):
        """Missing query should raise ValidationError."""
        from app.errors import ValidationError
        from app.utilities.web_search import WebSearchUtility

        utility = WebSearchUtility()
        with pytest.raises(ValidationError):
            utility.search("org", "user", {})

    @patch("app.utilities.web_search.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_search_rate_limit_raises_error(self, mock_post, reset_utility_singletons):
        """HTTP 429 should raise RateLimitError."""
        from app.errors import ProviderUnavailableError
        from app.utilities.web_search import WebSearchUtility

        mock_post.return_value.status_code = 429

        utility = WebSearchUtility()
        with pytest.raises(ProviderUnavailableError):
            utility.search("org", "user", {"query": "test"})

    @patch("app.utilities.web_search.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_search_timeout_raises_network_error(self, mock_post, reset_utility_singletons):
        """Timeout should raise NetworkError."""
        import requests

        from app.errors import ProviderUnavailableError
        from app.utilities.web_search import WebSearchUtility

        mock_post.side_effect = requests.exceptions.Timeout()

        utility = WebSearchUtility()
        with pytest.raises(ProviderUnavailableError):
            utility.search("org", "user", {"query": "test"})


class TestWebSearchExtract:
    """extract_content() method tests."""

    @patch("app.utilities.web_search.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_extract_single_url_string(
        self, mock_post, mock_tavily_extract_response, reset_utility_singletons
    ):
        """Single URL string should be converted to list."""
        from app.utilities.web_search import WebSearchUtility

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_tavily_extract_response

        utility = WebSearchUtility()
        result = utility.extract_content("org", "user", {"urls": "https://test.com"})

        assert result["status"] == "success"
        assert len(result["results"]) == 1

    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_extract_missing_urls_raises_error(self, reset_utility_singletons):
        """Missing urls should raise ValidationError."""
        from app.errors import ValidationError
        from app.utilities.web_search import WebSearchUtility

        utility = WebSearchUtility()
        with pytest.raises(ValidationError):
            utility.extract_content("org", "user", {})


# === SUMMARIZER TESTS (Mock Anthropic API) ===


class TestSummarizerInitialization:
    """Lazy initialization tests."""

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_api_key_raises_error(self, reset_utility_singletons):
        """Missing ANTHROPIC_API_KEY should raise CredentialMissingError."""
        from app.errors import CredentialMissingError
        from app.utilities.summarizer import SummarizerUtility

        utility = SummarizerUtility()
        with pytest.raises(CredentialMissingError):
            utility.summarize("org", "user", {"text": "test"})


class TestSummarizerSummarize:
    """summarize() method tests."""

    @patch("app.utilities.summarizer.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_summarize_success(
        self, mock_anthropic, mock_claude_response, reset_utility_singletons
    ):
        """Successful summarization returns summary text."""
        from app.utilities.summarizer import SummarizerUtility

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic.return_value = mock_client

        utility = SummarizerUtility()
        result = utility.summarize("org", "user", {"text": "Test text to summarize"})

        assert result["status"] == "success"
        assert result["summary"] == "Test summary"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_summarize_missing_text_raises_error(self, reset_utility_singletons):
        """Missing text should raise ValidationError."""
        from app.errors import ValidationError
        from app.utilities.summarizer import SummarizerUtility

        utility = SummarizerUtility()
        with pytest.raises(ValidationError):
            utility.summarize("org", "user", {})

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_summarize_oversized_text_raises_error(self, reset_utility_singletons):
        """Text > 100k tokens should raise ContentTooLargeError."""
        from app.errors import ContentTooLargeError
        from app.utilities.summarizer import SummarizerUtility

        utility = SummarizerUtility()
        # 100k tokens * 4 chars/token = 400k chars
        oversized_text = "x" * 500000

        with pytest.raises(ContentTooLargeError):
            utility.summarize("org", "user", {"text": oversized_text})

    @patch("app.utilities.summarizer.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_summarize_uses_haiku_by_default(
        self, mock_anthropic, mock_claude_response, reset_utility_singletons
    ):
        """Default style should use Haiku model."""
        from app.utilities.summarizer import SummarizerUtility

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic.return_value = mock_client

        utility = SummarizerUtility()
        utility.summarize("org", "user", {"text": "Test text", "style": "concise"})

        call_args = mock_client.messages.create.call_args
        assert "haiku" in call_args.kwargs["model"]

    @patch("app.utilities.summarizer.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_summarize_uses_sonnet_for_detailed(
        self, mock_anthropic, mock_claude_response, reset_utility_singletons
    ):
        """Detailed style should use Sonnet model."""
        from app.utilities.summarizer import SummarizerUtility

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic.return_value = mock_client

        utility = SummarizerUtility()
        utility.summarize("org", "user", {"text": "Test text", "style": "detailed"})

        call_args = mock_client.messages.create.call_args
        assert "sonnet" in call_args.kwargs["model"]


class TestSummarizerExecutiveSummary:
    """executive_summary() method tests."""

    @patch("app.utilities.summarizer.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_executive_summary_parses_json(self, mock_anthropic, reset_utility_singletons):
        """Should parse JSON response into structured output."""
        import json

        from app.utilities.summarizer import SummarizerUtility

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "summary": "Executive summary text",
                        "key_takeaways": ["Point 1", "Point 2"],
                        "recommendations": ["Do this"],
                    }
                )
            )
        ]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        utility = SummarizerUtility()
        result = utility.executive_summary("org", "user", {"text": "Test text"})

        assert result["summary"] == "Executive summary text"
        assert len(result["key_takeaways"]) == 2
        assert len(result["recommendations"]) == 1

    @patch("app.utilities.summarizer.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_executive_summary_json_fallback(
        self, mock_anthropic, mock_claude_response, reset_utility_singletons
    ):
        """Non-JSON response should fallback gracefully."""
        from app.utilities.summarizer import SummarizerUtility

        # Response that is not valid JSON
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not JSON")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        utility = SummarizerUtility()
        result = utility.executive_summary("org", "user", {"text": "Test text"})

        assert result["status"] == "success"
        assert result["summary"] == "This is not JSON"
        assert result["key_takeaways"] == []


class TestSummarizerErrorHandling:
    """Error handling tests."""

    @patch("app.utilities.summarizer.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_rate_limit_error_handling(self, mock_anthropic, reset_utility_singletons):
        """RateLimitError from Anthropic should be caught."""
        import anthropic

        from app.errors import RateLimitError
        from app.utilities.summarizer import SummarizerUtility

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limited", response=MagicMock(status_code=429), body={}
        )
        mock_anthropic.return_value = mock_client

        utility = SummarizerUtility()
        with pytest.raises(RateLimitError):
            utility.summarize("org", "user", {"text": "Test text"})

    @patch("app.utilities.summarizer.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_empty_response_raises_error(self, mock_anthropic, reset_utility_singletons):
        """Empty response.content should raise ExecutionError."""
        from app.errors import ExecutionError
        from app.utilities.summarizer import SummarizerUtility

        mock_response = MagicMock()
        mock_response.content = []  # Empty content
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 0

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        utility = SummarizerUtility()
        with pytest.raises(ExecutionError):
            utility.summarize("org", "user", {"text": "Test text"})


# === BASE UTILITY TESTS ===


class TestBaseUtilityMetrics:
    """Metrics tracking tests."""

    def test_metrics_increment_on_each_call(self):
        """total_calls should increment."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        initial_calls = calc.metrics["total_calls"]

        calc.calculate_npv("org", "user", {"cash_flows": [-1000, 500, 500], "discount_rate": 0.10})

        assert calc.metrics["total_calls"] == initial_calls + 1

    def test_first_call_at_set_on_first_call(self):
        """first_call_at should be set only once."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        assert calc.metrics["first_call_at"] is None

        calc.calculate_npv("org", "user", {"cash_flows": [-1000, 500], "discount_rate": 0.10})

        first_call_time = calc.metrics["first_call_at"]
        assert first_call_time is not None

        calc.calculate_npv("org", "user", {"cash_flows": [-1000, 500], "discount_rate": 0.10})

        # Should remain the same after second call
        assert calc.metrics["first_call_at"] == first_call_time

    def test_get_metrics_returns_service_info(self):
        """get_metrics should return service name and metrics."""
        from app.utilities.financial_calculator import FinancialCalculatorUtility

        calc = FinancialCalculatorUtility()

        result = calc.get_metrics("org", "user", {})

        assert result["service"] == "financial_calculator"
        assert "metrics" in result
        assert "total_calls" in result["metrics"]


class TestMultiProviderFallback:
    """Provider fallback logic tests."""

    @patch("app.utilities.web_search.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_provider_used_in_response(
        self, mock_post, mock_tavily_response, reset_utility_singletons
    ):
        """Response should include provider_used field."""
        from app.utilities.web_search import WebSearchUtility

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_tavily_response

        utility = WebSearchUtility()
        result = utility.search("org", "user", {"query": "test"})

        assert "provider_used" in result
        assert result["provider_used"] == "tavily"


class TestSingletonPattern:
    """Singleton getter function tests."""

    def test_financial_calculator_singleton(self, reset_utility_singletons):
        """get_financial_calculator_utility should return same instance."""
        from app.utilities.financial_calculator import get_financial_calculator_utility

        instance1 = get_financial_calculator_utility()
        instance2 = get_financial_calculator_utility()

        assert instance1 is instance2

    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_web_search_singleton(self, reset_utility_singletons):
        """get_web_search_utility should return same instance."""
        from app.utilities.web_search import get_web_search_utility

        instance1 = get_web_search_utility()
        instance2 = get_web_search_utility()

        assert instance1 is instance2

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    def test_summarizer_singleton(self, reset_utility_singletons):
        """get_summarizer_utility should return same instance."""
        from app.utilities.summarizer import get_summarizer_utility

        instance1 = get_summarizer_utility()
        instance2 = get_summarizer_utility()

        assert instance1 is instance2


if __name__ == "__main__":
    print("Running utility tests...")
    pytest.main([__file__, "-v"])
