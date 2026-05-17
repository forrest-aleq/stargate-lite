"""
FCI Base Utility Class.

Provides the foundation for all FCI primitives with:
- Service discovery (which connectors are available)
- Connector factory (get/cache connector instances)
- Aggregation helpers (call multiple services, handle errors)
- Common response formatting
- Trend and change calculation helpers
"""

from abc import ABC
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar, TypedDict

from app.database import CredentialManager
from app.logging_config import get_logger
from app.utilities.base import BaseUtility
from app.utilities.fci.service_mappings import get_connector

logger = get_logger(__name__)


class TrendPoint(TypedDict):
    """Single point in trend data."""

    date: str
    value: float


class FCIResponse(TypedDict, total=False):
    """Standard FCI response shape for frontend compatibility."""

    total: float
    change: float
    changePercent: float
    trend: list[TrendPoint]
    insight: str | None
    lastUpdated: str
    status: str
    errors: list[dict[str, Any]]
    sources: list[str]


class FCIBase(BaseUtility, ABC):
    """
    Base class for FCI utilities.

    Unlike regular utilities that use their own API keys, FCI utilities
    aggregate data from customer-connected services via their connectors.
    """

    SERVICE_NAME = "fci"
    REQUIRED_ENV_VARS: ClassVar[list[str]] = []  # FCI uses connector credentials, not its own

    def _initialize_client(self) -> None:
        """FCI doesn't need its own client - uses connectors."""
        pass

    @staticmethod
    def _coerce_amount(value: Any) -> float | None:
        """Convert connector amount strings to floats, returning None for labels."""
        if value is None:
            return None
        if isinstance(value, int | float):
            return float(value)

        text = str(value).strip()
        if not text:
            return None

        is_negative = text.startswith("(") and text.endswith(")")
        normalized = text.strip("()").replace(",", "").replace("$", "").strip()
        if normalized in {"", "-"}:
            return None

        try:
            amount = float(normalized)
        except ValueError:
            return None

        return -abs(amount) if is_negative else amount

    def _last_numeric_col_value(self, col_data: list[dict[str, Any]]) -> float | None:
        """Return the right-most numeric ColData value, skipping label columns."""
        for col in reversed(col_data):
            amount = self._coerce_amount(col.get("value"))
            if amount is not None:
                return amount
        return None

    @staticmethod
    def _normalize_accounting_key(value: Any) -> str:
        """Normalize accounting section labels like 'Net Income' or 'COGS'."""
        return "".join(ch for ch in str(value or "").lower() if ch.isalnum())

    def _quickbooks_section_key(self, row: dict[str, Any]) -> str:
        """Return a stable key for QuickBooks report sections."""
        group_key = self._normalize_accounting_key(row.get("group"))
        if group_key:
            return group_key

        for container in ("Summary", "Header"):
            col_data = row.get(container, {}).get("ColData", [])
            if col_data:
                label_key = self._normalize_accounting_key(col_data[0].get("value"))
                if label_key:
                    return label_key.removeprefix("total")

        col_data = row.get("ColData", [])
        if col_data:
            return self._normalize_accounting_key(col_data[0].get("value")).removeprefix("total")

        return ""

    def _get_connected_services(
        self,
        org_id: str,
        user_id: str,
        service_map: dict[str, str],
    ) -> list[str]:
        """
        Get list of services from service_map that the org has credentials for.

        Args:
            org_id: Organization ID
            user_id: User ID
            service_map: Dict mapping service names to method names

        Returns:
            List of available service names
        """
        available_services = CredentialManager.get_services_for_org(org_id, user_id)
        connected = [s for s in service_map if s in available_services]

        logger.debug(
            "FCI connected services",
            org_id=org_id,
            user_id=user_id,
            requested=list(service_map.keys()),
            available=available_services,
            connected=connected,
            log_event="fci_service_discovery",
        )

        return connected

    def _get_connector(self, service: str) -> Any:
        """Get connector instance for a service."""
        return get_connector(service)

    def _call_service_method(
        self,
        service: str,
        method_name: str,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Call a method on a connector.

        Args:
            service: Service name (e.g., "quickbooks")
            method_name: Method to call (e.g., "get_ar_aging")
            org_id: Organization ID
            user_id: User ID
            args: Arguments to pass to the method

        Returns:
            Result from the connector method
        """
        connector = self._get_connector(service)
        method = getattr(connector, method_name, None)

        if not method:
            raise AttributeError(f"Connector {service} has no method {method_name}")

        logger.debug(
            "Calling connector method",
            service=service,
            method=method_name,
            org_id=org_id,
            user_id=user_id,
            log_event="fci_connector_call",
        )

        return method(org_id, user_id, args)

    def _aggregate_from_services(
        self,
        service_map: dict[str, str],
        org_id: str,
        user_id: str,
        args: dict[str, Any],
        preferred_service: str | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
        """
        Call multiple services and aggregate results with error handling.

        Args:
            service_map: Dict mapping service name to method name
            org_id: Organization ID
            user_id: User ID
            args: Arguments to pass to methods
            preferred_service: If set, only use this service (for single-source queries)

        Returns:
            Tuple of (results, errors, sources)
            - results: List of successful results
            - errors: List of error dicts {service, error, error_type}
            - sources: List of service names that returned data
        """
        results: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        sources: list[str] = []

        # Get available services
        available = self._get_connected_services(org_id, user_id, service_map)

        if not available:
            logger.warning(
                "No services available for FCI aggregation",
                org_id=org_id,
                user_id=user_id,
                requested_services=list(service_map.keys()),
                log_event="fci_no_services",
            )
            return results, errors, sources

        # Filter to preferred service if specified
        if preferred_service:
            if preferred_service in available:
                available = [preferred_service]
            else:
                errors.append(
                    {
                        "service": preferred_service,
                        "error": f"Service {preferred_service} not connected",
                        "error_type": "ServiceNotConnected",
                    }
                )
                return results, errors, sources

        # Call each available service
        for service in available:
            method_name = service_map[service]
            try:
                result = self._call_service_method(service, method_name, org_id, user_id, args)
                result["_source"] = service  # Tag with source
                results.append(result)
                sources.append(service)
            except Exception as e:
                logger.warning(
                    "FCI service call failed",
                    service=service,
                    method=method_name,
                    error_type=type(e).__name__,
                    error=str(e),
                    log_event="fci_service_error",
                )
                errors.append(
                    {
                        "service": service,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )

        return results, errors, sources

    def _get_primary_accounting_service(
        self,
        org_id: str,
        user_id: str,
        service_map: dict[str, str],
    ) -> str | None:
        """
        Get the primary accounting system for an org.

        Checks in priority order: quickbooks, xero, sage_intacct, netsuite
        Returns the first one that's connected.
        """
        from app.utilities.fci.service_mappings import ACCOUNTING_PRIORITY

        available = self._get_connected_services(org_id, user_id, service_map)

        for service in ACCOUNTING_PRIORITY:
            if service in available:
                return service

        return available[0] if available else None

    # =========================================================================
    # Response formatting helpers
    # =========================================================================

    def _format_response(
        self,
        total: float,
        change: float | None = None,
        change_percent: float | None = None,
        trend: list[TrendPoint] | None = None,
        insight: str | None = None,
        sources: list[str] | None = None,
        errors: list[dict[str, Any]] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """
        Format a standard FCI response with frontend-compatible fields.

        Args:
            total: Primary value
            change: Absolute change from prior period
            change_percent: Percentage change
            trend: List of {date, value} points for sparkline
            insight: Auto-generated insight string
            sources: List of data sources used
            errors: List of error dicts
            **extra: Additional fields to include

        Returns:
            Formatted response dict
        """
        response: dict[str, Any] = {
            "total": total,
            "lastUpdated": datetime.now(UTC).isoformat() + "Z",
            "status": "partial" if errors else "success",
        }

        if change is not None:
            response["change"] = change
        if change_percent is not None:
            response["changePercent"] = change_percent
        if trend is not None:
            response["trend"] = trend
        if insight is not None:
            response["insight"] = insight
        if sources:
            response["sources"] = sources
        if errors:
            response["errors"] = errors

        # Add any extra fields
        response.update(extra)

        return response

    def _calculate_change(
        self,
        current: float,
        prior: float,
    ) -> tuple[float, float]:
        """
        Calculate absolute and percentage change.

        Returns:
            Tuple of (absolute_change, percent_change)
        """
        change = current - prior
        if prior != 0:
            change_percent = (change / abs(prior)) * 100
        else:
            change_percent = 100.0 if current > 0 else 0.0

        return round(change, 2), round(change_percent, 2)

    def _generate_insight(
        self,
        metric_name: str,
        current: float,
        change_percent: float,
        period: str = "last month",
    ) -> str:
        """
        Generate a basic insight string for a metric.

        Args:
            metric_name: Human name of the metric (e.g., "Cash", "AR")
            current: Current value
            change_percent: Percentage change
            period: Comparison period description

        Returns:
            Insight string like "Cash up 7.2% from last month"
        """
        direction = "up" if change_percent > 0 else "down" if change_percent < 0 else "unchanged"

        if change_percent == 0:
            return f"{metric_name} unchanged from {period}"

        return f"{metric_name} {direction} {abs(change_percent):.1f}% from {period}"

    def _determine_trend_direction(
        self,
        values: list[float],
    ) -> str:
        """
        Determine trend direction from a series of values.

        Returns: "increasing", "decreasing", or "stable"
        """
        if len(values) < 2:
            return "stable"

        # Simple linear trend: compare first half avg to second half avg
        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(values[mid:]) / (len(values) - mid) if (len(values) - mid) > 0 else 0

        threshold = 0.05  # 5% threshold for "stable"

        if second_half_avg == 0 and first_half_avg == 0:
            return "stable"

        if first_half_avg == 0:
            return "increasing" if second_half_avg > 0 else "stable"

        change_ratio = (second_half_avg - first_half_avg) / abs(first_half_avg)

        if change_ratio > threshold:
            return "increasing"
        elif change_ratio < -threshold:
            return "decreasing"
        else:
            return "stable"

    # =========================================================================
    # Date/period helpers
    # =========================================================================

    def _parse_period(
        self,
        period: str | None,
        as_of: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> tuple[datetime, datetime]:
        """
        Parse period parameters into start and end dates.

        Args:
            period: One of "mtd", "ytd", "qtd", "last_month", "last_quarter", "trailing_12m"
            as_of: Point-in-time date (for "as of" queries)
            from_date: Explicit start date (ISO format)
            to_date: Explicit end date (ISO format)

        Returns:
            Tuple of (start_date, end_date) as datetime objects
        """
        # If explicit dates provided, use them
        if from_date and to_date:
            return (
                datetime.fromisoformat(from_date.replace("Z", "")),
                datetime.fromisoformat(to_date.replace("Z", "")),
            )

        # Parse as_of or use today
        if as_of:
            end_date = datetime.fromisoformat(as_of.replace("Z", ""))
        else:
            end_date = datetime.now(UTC)

        # Calculate start date based on period
        period = period or "mtd"

        if period == "mtd":
            start_date = end_date.replace(day=1)
        elif period == "ytd":
            start_date = end_date.replace(month=1, day=1)
        elif period == "qtd":
            quarter_start_month = ((end_date.month - 1) // 3) * 3 + 1
            start_date = end_date.replace(month=quarter_start_month, day=1)
        elif period == "last_month":
            # First day of last month to last day of last month
            first_of_this_month = end_date.replace(day=1)
            end_date = first_of_this_month - timedelta(days=1)
            start_date = end_date.replace(day=1)
        elif period == "last_quarter":
            # Previous quarter
            current_quarter = (end_date.month - 1) // 3
            if current_quarter == 0:
                start_month = 10
                start_year = end_date.year - 1
            else:
                start_month = (current_quarter - 1) * 3 + 1
                start_year = end_date.year
            start_date = datetime(start_year, start_month, 1)
            # End of quarter: last day of start_month + 2
            end_month = start_month + 2
            if end_month == 12:
                # December: go to Jan 1 next year - 1 day
                end_date = datetime(start_year + 1, 1, 1) - timedelta(days=1)
            else:
                # Other months: go to first of next month - 1 day
                end_date = datetime(start_year, end_month + 1, 1) - timedelta(days=1)
        elif period == "trailing_12m":
            start_date = end_date - timedelta(days=365)
        else:
            # Default to MTD
            start_date = end_date.replace(day=1)

        return start_date, end_date

    def _get_prior_period(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> tuple[datetime, datetime]:
        """
        Get the equivalent prior period for comparison.

        For MTD, returns previous month same days.
        For other periods, returns same duration immediately prior.
        """
        duration = end_date - start_date

        # Check if it's a full month (MTD-like)
        if start_date.day == 1:
            # Go back one month
            if start_date.month == 1:
                prior_start = start_date.replace(year=start_date.year - 1, month=12)
            else:
                prior_start = start_date.replace(month=start_date.month - 1)

            # Same number of days into the month
            days_into_month = (end_date - start_date).days
            prior_end = prior_start + timedelta(days=days_into_month)
        else:
            # Same duration, immediately prior
            prior_end = start_date - timedelta(days=1)
            prior_start = prior_end - duration

        return prior_start, prior_end
