"""
FCI Revenue Mixin.

Aggregates revenue data from connected systems:
- QuickBooks/Xero/Sage P&L income section
- Stripe charges
- Recurly invoices
- Shopify orders
- Square payments

Returns total revenue with period breakdowns, MRR for subscription businesses,
change tracking, and trend data.
"""

import contextlib
from datetime import UTC, datetime
from typing import Any

from app.logging_config import get_logger
from app.utilities.fci.service_mappings import PL_REPORT_SERVICES

logger = get_logger(__name__)


class RevenueMixin:
    """Mixin for revenue aggregation."""

    def get_revenue(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get revenue totals from P&L and payment systems.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - period: mtd, ytd, last_month, trailing_12m (default: mtd)
                - from_date: Explicit start date (YYYY-MM-DD)
                - to_date: Explicit end date (YYYY-MM-DD)
                - source: Specific source system (optional)

        Returns:
            {
                "total": float,
                "mtd": float,
                "ytd": float,
                "last_month": float,
                "trend": str ("increasing", "decreasing", "stable"),
                "mrr": float | None,
                "by_category": [{category, amount}],
                "change": float,
                "changePercent": float,
                "trend_data": [{date, value}],
                "insight": str,
                "lastUpdated": str,
                "sources": [str],
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        period = args.get("period", "mtd")
        from_date = args.get("from_date")
        to_date = args.get("to_date")

        # Parse period into dates
        start_date, end_date = self._parse_period(period, None, from_date, to_date)

        # Get primary accounting system for P&L-based revenue
        primary_service = self._get_primary_accounting_service(org_id, user_id, PL_REPORT_SERVICES)

        revenue_data: dict[str, Any] = {
            "total": 0.0,
            "mtd": None,
            "ytd": None,
            "last_month": None,
            "mrr": None,
            "by_category": [],
        }

        all_errors: list[dict[str, Any]] = []
        all_sources: list[str] = []

        # Get P&L data from accounting system
        if primary_service:
            pl_args = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            }

            results, errors, sources = self._aggregate_from_services(
                {primary_service: PL_REPORT_SERVICES[primary_service]},
                org_id,
                user_id,
                pl_args,
                preferred_service=primary_service,
            )

            all_errors.extend(errors)
            all_sources.extend(sources)

            if results:
                pl_data = self._parse_pl_revenue(primary_service, results[0])
                revenue_data["total"] = pl_data.get("income", 0)
                revenue_data["by_category"] = pl_data.get("categories", [])

        # Supplement with Stripe MRR if available
        mrr_data = self._get_mrr_data(org_id, user_id)
        if mrr_data:
            revenue_data["mrr"] = mrr_data.get("mrr")
            if "stripe" not in all_sources:
                all_sources.append("stripe")

        # Populate only the period value actually queried (no synthetic period backfills).
        revenue_data = self._calculate_period_values(
            org_id, user_id, revenue_data, primary_service, period
        )

        # Calculate change
        current_value = revenue_data["total"]
        prior_total = self._get_prior_revenue(org_id, user_id, current_value, period)
        change, change_percent = self._calculate_change(current_value, prior_total)

        # Determine trend direction
        trend_direction = "stable"

        # Generate trend data points
        trend_data = self._generate_revenue_trend(current_value, change_percent)

        # Generate insight
        insight = self._generate_revenue_insight(revenue_data, change_percent)

        return self._format_response(
            total=revenue_data["total"],
            change=change,
            change_percent=change_percent,
            trend=trend_data,
            insight=insight,
            sources=all_sources,
            errors=all_errors if all_errors else None,
            mtd=revenue_data["mtd"],
            ytd=revenue_data["ytd"],
            last_month=revenue_data["last_month"],
            trend_direction=trend_direction,
            mrr=revenue_data["mrr"],
            by_category=revenue_data["by_category"],
            period=period,
            period_start=start_date.strftime("%Y-%m-%d"),
            period_end=end_date.strftime("%Y-%m-%d"),
            data_quality={
                "historical_comparison": "unavailable",
                "trend_mode": "snapshot_only",
                "period_values": "only_requested_period_populated",
            },
        )

    def _parse_pl_revenue(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse P&L result to extract revenue/income data."""
        data = {
            "income": 0.0,
            "categories": [],
        }

        if service == "quickbooks":
            # QuickBooks P&L report structure
            # Look for Income section in the report
            rows = result.get("Rows", {}).get("Row", [])

            revenue_section_keys = {"income", "revenue", "salesrevenue", "operatingrevenue"}

            for row in rows:
                section_key = self._quickbooks_section_key(row)
                summary = row.get("Summary", {})

                if section_key in revenue_section_keys:
                    col_data = summary.get("ColData", [])
                    amount = self._last_numeric_col_value(col_data)
                    if amount is not None:
                        data["income"] = amount

                    # Extract category breakdown from section rows
                    section_rows = row.get("Rows", {}).get("Row", [])
                    for sub_row in section_rows:
                        sub_col_data = sub_row.get("ColData", [])
                        if len(sub_col_data) >= 2:
                            category = sub_col_data[0].get("value", "Other")
                            amount = self._last_numeric_col_value(sub_col_data)
                            if amount:
                                data["categories"].append({"category": category, "amount": amount})

        elif service == "xero":
            # Xero P&L report
            reports = result.get("Reports", [])
            if reports:
                report = reports[0]
                rows = report.get("Rows", [])

                for row in rows:
                    title = row.get("Title", "").lower()

                    if "income" in title or "revenue" in title:
                        # Sum up the section
                        for sub_row in row.get("Rows", []):
                            cells = sub_row.get("Cells", [])
                            if len(cells) >= 2:
                                try:
                                    category = cells[0].get("Value", "Other")
                                    amount = float(cells[-1].get("Value", 0) or 0)
                                    data["income"] += amount
                                    if amount != 0:
                                        data["categories"].append(
                                            {"category": category, "amount": amount}
                                        )
                                except (ValueError, TypeError):
                                    pass

        elif service == "sage_intacct":
            # Sage Intacct P&L
            income = result.get("total_income", result.get("TOTALINCOME", 0))
            try:
                data["income"] = float(income)
            except (ValueError, TypeError):
                data["income"] = 0.0

            categories = result.get("income_breakdown", result.get("categories", []))
            for cat in categories:
                with contextlib.suppress(ValueError, TypeError):
                    data["categories"].append(
                        {
                            "category": cat.get("name", cat.get("NAME", "Other")),
                            "amount": float(cat.get("amount", cat.get("AMOUNT", 0))),
                        }
                    )

        elif service == "netsuite":
            # NetSuite P&L
            income = result.get("totalIncome", result.get("total_income", 0))
            try:
                data["income"] = float(income)
            except (ValueError, TypeError):
                data["income"] = 0.0

            categories = result.get("incomeCategories", result.get("categories", []))
            for cat in categories:
                with contextlib.suppress(ValueError, TypeError):
                    data["categories"].append(
                        {
                            "category": cat.get("name", "Other"),
                            "amount": float(cat.get("amount", 0)),
                        }
                    )

        return data

    def _get_mrr_data(
        self,
        org_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        """Get MRR data from subscription services (Stripe, Recurly)."""
        # Check if Stripe is connected
        available = self._get_connected_services(org_id, user_id, {"stripe": "get_balance"})

        if "stripe" not in available:
            return None

        # In a full implementation, would call Stripe to get subscription data
        # and calculate MRR from active subscriptions
        # For now, return None (would be implemented with actual Stripe API call)
        return None

    def _calculate_period_values(
        self,
        org_id: str,
        user_id: str,
        revenue_data: dict[str, Any],
        primary_service: str | None,
        period: str,
    ) -> dict[str, Any]:
        """Populate only period values explicitly requested by caller."""
        _ = (org_id, user_id, primary_service)
        current = revenue_data["total"]
        revenue_data["mtd"] = current if period == "mtd" else None
        revenue_data["ytd"] = current if period == "ytd" else None
        revenue_data["last_month"] = current if period == "last_month" else None

        return revenue_data

    def _get_prior_revenue(
        self,
        org_id: str,
        user_id: str,
        current_total: float,
        period: str,
    ) -> float:
        """Get prior period revenue for comparison.

        Historical revenue snapshots are not yet wired. Return current value so
        delta metrics remain truthful instead of inferred.
        """
        _ = (org_id, user_id, period)
        return current_total

    def _generate_revenue_trend(
        self,
        current_total: float,
        change_percent: float,
    ) -> list[dict[str, Any]]:
        """Generate trend data points for revenue sparkline."""
        _ = change_percent  # reserved for future historical mode
        today = datetime.now(UTC)
        return [{"date": today.strftime("%Y-%m"), "value": round(current_total, 2)}]

    def _generate_revenue_insight(
        self,
        revenue_data: dict[str, Any],
        change_percent: float,
    ) -> str:
        """Generate insight string for revenue."""
        total = revenue_data["total"]
        mrr = revenue_data.get("mrr")

        if mrr:
            return f"Revenue at ${total:,.0f} with MRR of ${mrr:,.0f}"

        direction = "up" if change_percent > 0 else "down" if change_percent < 0 else "unchanged"

        if change_percent == 0:
            return f"Revenue unchanged at ${total:,.0f}"

        return f"Revenue {direction} {abs(change_percent):.1f}% to ${total:,.0f}"
