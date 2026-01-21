"""
Unit tests for FCI Utilities.

Tests the aggregation layer that transforms raw connector data into
unified financial primitives.
"""

from unittest.mock import MagicMock, patch

from app.utilities.fci import FCIUtility, get_fci_utility


class TestFCIUtilityInstantiation:
    """Test FCI utility instantiation and singleton pattern."""

    def test_fci_utility_instantiation(self):
        """FCIUtility can be instantiated."""
        fci = FCIUtility()
        assert fci is not None

    def test_get_fci_utility_singleton(self):
        """get_fci_utility returns singleton."""
        fci1 = get_fci_utility()
        fci2 = get_fci_utility()
        assert fci1 is fci2

    def test_fci_has_all_methods(self):
        """FCIUtility has all expected methods."""
        fci = FCIUtility()

        # Primitives
        assert hasattr(fci, "get_cash")
        assert hasattr(fci, "get_ar")
        assert hasattr(fci, "get_ap")
        assert hasattr(fci, "get_revenue")
        assert hasattr(fci, "get_expenses")
        assert hasattr(fci, "get_burn")
        assert hasattr(fci, "get_runway")
        assert hasattr(fci, "get_payroll")

        # Reports
        assert hasattr(fci, "get_profit_loss")
        assert hasattr(fci, "get_balance_sheet")
        assert hasattr(fci, "get_ar_aging_report")
        assert hasattr(fci, "get_ap_aging_report")
        assert hasattr(fci, "get_cashflow_report")

        # Entity lookups
        assert hasattr(fci, "lookup_customer")
        assert hasattr(fci, "lookup_vendor")
        assert hasattr(fci, "lookup_invoice")


class TestFCIBaseHelpers:
    """Test FCIBase helper methods."""

    def test_calculate_change_positive(self):
        """Calculate positive change correctly."""
        fci = FCIUtility()
        change, pct = fci._calculate_change(110, 100)
        assert change == 10
        assert pct == 10.0

    def test_calculate_change_negative(self):
        """Calculate negative change correctly."""
        fci = FCIUtility()
        change, pct = fci._calculate_change(90, 100)
        assert change == -10
        assert pct == -10.0

    def test_calculate_change_zero_prior(self):
        """Handle zero prior value."""
        fci = FCIUtility()
        change, pct = fci._calculate_change(100, 0)
        assert change == 100
        assert pct == 100.0

    def test_determine_trend_direction(self):
        """Determine trend direction from values."""
        fci = FCIUtility()

        # Increasing
        assert fci._determine_trend_direction([100, 110, 120, 130]) == "increasing"

        # Decreasing
        assert fci._determine_trend_direction([130, 120, 110, 100]) == "decreasing"

        # Stable
        assert fci._determine_trend_direction([100, 101, 99, 100]) == "stable"

    def test_generate_insight(self):
        """Generate insight strings."""
        fci = FCIUtility()

        insight = fci._generate_insight("Cash", 1000000, 7.5)
        assert "Cash" in insight
        assert "up" in insight
        assert "7.5" in insight

        insight = fci._generate_insight("AR", 500000, -3.2)
        assert "AR" in insight
        assert "down" in insight

    def test_parse_period_mtd(self):
        """Parse MTD period correctly."""
        fci = FCIUtility()
        start, end = fci._parse_period("mtd")

        assert start.day == 1
        assert start.month == end.month
        assert end >= start

    def test_parse_period_ytd(self):
        """Parse YTD period correctly."""
        fci = FCIUtility()
        start, end = fci._parse_period("ytd")

        assert start.month == 1
        assert start.day == 1
        assert end >= start

    def test_parse_period_explicit_dates(self):
        """Parse explicit date range."""
        fci = FCIUtility()
        start, end = fci._parse_period(
            None,
            from_date="2026-01-01",
            to_date="2026-01-31"
        )

        assert start.year == 2026
        assert start.month == 1
        assert start.day == 1
        assert end.day == 31


class TestFCIResponseFormatting:
    """Test response formatting."""

    def test_format_response_success(self):
        """Format successful response."""
        fci = FCIUtility()
        response = fci._format_response(
            total=100000,
            sources=["plaid", "mercury"],
            errors=None,
            custom_field="custom_value"
        )

        assert response["total"] == 100000
        assert response["status"] == "success"
        assert response["sources"] == ["plaid", "mercury"]
        assert "lastUpdated" in response
        assert response["custom_field"] == "custom_value"

    def test_format_response_partial(self):
        """Format partial response with errors."""
        fci = FCIUtility()
        response = fci._format_response(
            total=100000,
            sources=["plaid"],
            errors=[{"service": "mercury", "error": "Connection failed"}]
        )

        assert response["total"] == 100000
        assert response["status"] == "partial"
        assert len(response["errors"]) == 1


class TestCashMixin:
    """Test cash position aggregation."""

    @patch.object(FCIUtility, "_get_connected_services")
    @patch.object(FCIUtility, "_call_service_method")
    def test_get_cash_aggregates_sources(self, mock_call, mock_services):
        """Cash aggregates data from multiple sources."""
        mock_services.return_value = ["plaid", "mercury"]
        mock_call.side_effect = [
            {
                "_source": "plaid",
                "accounts": [
                    {
                        "name": "Checking",
                        "institution_name": "Chase",
                        "balances": {"current": 500000},
                        "account_id": "plaid_123"
                    }
                ]
            },
            {
                "_source": "mercury",
                "accounts": [
                    {
                        "name": "Mercury Checking",
                        "current_balance": 300000,
                        "id": "merc_456"
                    }
                ]
            }
        ]

        fci = FCIUtility()
        result = fci.get_cash("org_123", "user_456", {})

        assert result["total"] == 800000
        assert result["status"] == "success"
        assert len(result["accounts"]) == 2
        assert "plaid" in result["sources"]
        assert "mercury" in result["sources"]

    @patch.object(FCIUtility, "_get_connected_services")
    def test_get_cash_no_services(self, mock_services):
        """Cash returns empty when no services connected."""
        mock_services.return_value = []

        fci = FCIUtility()
        result = fci.get_cash("org_123", "user_456", {})

        assert result["total"] == 0
        assert len(result["accounts"]) == 0


class TestARMixin:
    """Test accounts receivable aggregation."""

    @patch.object(FCIUtility, "_get_connected_services")
    @patch.object(FCIUtility, "_call_service_method")
    def test_get_ar_from_quickbooks(self, mock_call, mock_services):
        """AR retrieves data from QuickBooks."""
        mock_services.return_value = ["quickbooks"]
        mock_call.return_value = {
            "_source": "quickbooks",
            "Rows": {
                "Row": [
                    {
                        "type": "Data",
                        "ColData": [
                            {"value": "Customer A"},
                            {"value": "10000"},  # current
                            {"value": "5000"},   # 30
                            {"value": "3000"},   # 60
                            {"value": "1000"},   # 90
                            {"value": "500"},    # 90+
                        ]
                    }
                ]
            }
        }

        fci = FCIUtility()
        result = fci.get_ar("org_123", "user_456", {})

        assert result["total"] > 0
        assert "current" in result
        assert "days_30" in result
        assert "quickbooks" in result["sources"]


class TestAPMixin:
    """Test accounts payable aggregation."""

    @patch.object(FCIUtility, "_get_connected_services")
    @patch.object(FCIUtility, "_call_service_method")
    def test_get_ap_from_quickbooks(self, mock_call, mock_services):
        """AP retrieves data from QuickBooks."""
        mock_services.return_value = ["quickbooks"]
        mock_call.return_value = {
            "_source": "quickbooks",
            "Rows": {
                "Row": [
                    {
                        "type": "Data",
                        "ColData": [
                            {"value": "Vendor A"},
                            {"value": "8000"},
                            {"value": "4000"},
                            {"value": "2000"},
                            {"value": "500"},
                            {"value": "200"},
                        ]
                    }
                ]
            }
        }

        fci = FCIUtility()
        result = fci.get_ap("org_123", "user_456", {})

        assert result["total"] > 0
        assert "current" in result
        assert "quickbooks" in result["sources"]


class TestBurnMixin:
    """Test burn rate calculation."""

    @patch.object(FCIUtility, "_get_connected_services")
    @patch.object(FCIUtility, "_call_service_method")
    def test_get_burn_calculates_average(self, mock_call, mock_services):
        """Burn calculates monthly average."""
        mock_services.return_value = ["quickbooks"]

        # Return different expense amounts for each month
        mock_call.side_effect = [
            {"_source": "quickbooks", "Rows": {"Row": []}},  # Month 1
            {"_source": "quickbooks", "Rows": {"Row": []}},  # Month 2
            {"_source": "quickbooks", "Rows": {"Row": []}},  # Month 3
        ]

        fci = FCIUtility()
        result = fci.get_burn("org_123", "user_456", {"months": 3})

        assert "monthly_avg" in result
        assert "trend_direction" in result
        assert "months_analyzed" in result


class TestRunwayMixin:
    """Test runway calculation."""

    @patch.object(FCIUtility, "get_cash")
    @patch.object(FCIUtility, "get_burn")
    def test_get_runway_calculates_months(self, mock_burn, mock_cash):
        """Runway calculates months correctly."""
        mock_cash.return_value = {
            "total": 1200000,
            "accounts": [],
            "sources": ["mercury"],
            "errors": None
        }
        mock_burn.return_value = {
            "monthly_avg": 100000,
            "sources": ["quickbooks"],
            "errors": None,
            "months_analyzed": 3,
            "trend_direction": "stable"
        }

        fci = FCIUtility()
        result = fci.get_runway("org_123", "user_456", {})

        assert result["months"] == 12.0
        assert result["cash"] == 1200000
        assert result["burn"] == 100000
        assert result["cash_out_date"] is not None
        assert result["confidence"] in ["high", "medium", "low"]


class TestEntityMixin:
    """Test entity lookup functionality."""

    def test_lookup_customer_requires_params(self):
        """Customer lookup requires name, email, or id."""
        fci = FCIUtility()
        result = fci.lookup_customer("org_123", "user_456", {})

        assert result["match_count"] == 0
        assert len(result["errors"]) > 0

    def test_lookup_vendor_requires_params(self):
        """Vendor lookup requires name, email, or id."""
        fci = FCIUtility()
        result = fci.lookup_vendor("org_123", "user_456", {})

        assert result["match_count"] == 0
        assert len(result["errors"]) > 0

    def test_lookup_invoice_requires_params(self):
        """Invoice lookup requires invoice_number or id."""
        fci = FCIUtility()
        result = fci.lookup_invoice("org_123", "user_456", {})

        assert result["match_count"] == 0
        assert len(result["errors"]) > 0


class TestFCIRegistry:
    """Test FCI registry integration."""

    def test_fci_capabilities_registered(self):
        """FCI capabilities are in the registry."""
        from app.registry import CAPABILITY_REGISTRY

        fci_caps = [k for k in CAPABILITY_REGISTRY if k.startswith("fci.")]
        assert len(fci_caps) == 16

        # Check key capabilities
        assert "fci.cash" in CAPABILITY_REGISTRY
        assert "fci.ar" in CAPABILITY_REGISTRY
        assert "fci.runway" in CAPABILITY_REGISTRY
        assert "fci.report.profitloss" in CAPABILITY_REGISTRY

    def test_fci_handler_callable(self):
        """FCI handlers are callable."""
        from app.registry import CAPABILITY_REGISTRY

        handler = CAPABILITY_REGISTRY["fci.cash"]["handler"]
        assert callable(handler)


class TestServiceMappings:
    """Test service mappings module."""

    def test_cash_services_defined(self):
        """Cash services are defined."""
        from app.utilities.fci.service_mappings import CASH_SERVICES

        assert "plaid" in CASH_SERVICES
        assert "mercury" in CASH_SERVICES
        assert "stripe" in CASH_SERVICES

    def test_ar_services_defined(self):
        """AR services are defined."""
        from app.utilities.fci.service_mappings import AR_SERVICES

        assert "quickbooks" in AR_SERVICES
        assert "xero" in AR_SERVICES

    def test_ap_services_defined(self):
        """AP services are defined."""
        from app.utilities.fci.service_mappings import AP_SERVICES

        assert "quickbooks" in AP_SERVICES
        assert "billcom" in AP_SERVICES

    def test_get_connector_returns_instance(self):
        """get_connector returns connector instance."""
        from app.utilities.fci.service_mappings import get_connector

        # This will import the actual connector
        connector = get_connector("quickbooks")
        assert connector is not None

    def test_cache_ttl_defined(self):
        """Cache TTL values are defined."""
        from app.utilities.fci.service_mappings import CACHE_TTL

        assert CACHE_TTL["fci.cash"] == 60
        assert CACHE_TTL["fci.burn"] == 3600
        assert CACHE_TTL["fci.runway"] == 3600


class TestDatabaseServiceDiscovery:
    """Test database service discovery."""

    @patch("app.database.SessionLocal")
    def test_get_services_for_org(self, mock_session):
        """get_services_for_org returns connected services."""
        from app.database import CredentialManager

        # Mock the query result
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_cred1 = MagicMock()
        mock_cred1.service = "quickbooks"
        mock_cred2 = MagicMock()
        mock_cred2.service = "plaid"

        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            mock_cred1, mock_cred2
        ]

        services = CredentialManager.get_services_for_org("org_123", "user_456")

        assert "quickbooks" in services
        assert "plaid" in services
