"""
FCI Expenses Mixin.

Aggregates expense data from connected systems:
- QuickBooks/Xero/Sage P&L expense section
- Brex expenses
- Ramp transactions

Returns total expenses with period breakdowns, category breakdown,
change tracking, and trend data.
"""

import contextlib
from datetime import UTC, datetime
from typing import Any

from app.logging_config import get_logger
from app.utilities.fci.service_mappings import PL_REPORT_SERVICES

logger = get_logger(__name__)


class ExpensesMixin:
    """Mixin for expense aggregation."""

    def get_expenses(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get expense totals from P&L and expense management systems.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - period: mtd, ytd, last_month, trailing_12m (default: mtd)
                - from_date: Explicit start date (YYYY-MM-DD)
                - to_date: Explicit end date (YYYY-MM-DD)
                - by_category: Include category breakdown (default: True)

        Returns:
            {
                "total": float,
                "mtd": float,
                "ytd": float,
                "last_month": float,
                "trend": str ("increasing", "decreasing", "stable"),
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
        include_categories = args.get("by_category", True)

        # Parse period into dates
        start_date, end_date = self._parse_period(period, None, from_date, to_date)

        # Get primary accounting system for P&L-based expenses
        primary_service = self._get_primary_accounting_service(org_id, user_id, PL_REPORT_SERVICES)

        expense_data: dict[str, Any] = {
            "total": 0.0,
            "mtd": None,
            "ytd": None,
            "last_month": None,
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
                exp_data = self._parse_pl_expenses(primary_service, results[0])
                expense_data["total"] = exp_data.get("expenses", 0)
                if include_categories:
                    expense_data["by_category"] = exp_data.get("categories", [])

        # Populate only the period value explicitly requested.
        expense_data = self._calculate_expense_period_values(
            org_id, user_id, expense_data, primary_service, period
        )

        # Calculate change
        current_value = expense_data["total"]
        prior_total = self._get_prior_expenses(org_id, user_id, current_value, period)
        change, change_percent = self._calculate_change(current_value, prior_total)

        # Historical trend direction unavailable until snapshots are wired.
        trend_direction = "stable"

        # Generate trend data points
        trend_data = self._generate_expense_trend(current_value, change_percent)

        # Generate insight
        insight = self._generate_expense_insight(expense_data, change_percent)

        return self._format_response(
            total=expense_data["total"],
            change=change,
            change_percent=change_percent,
            trend=trend_data,
            insight=insight,
            sources=all_sources,
            errors=all_errors if all_errors else None,
            mtd=expense_data["mtd"],
            ytd=expense_data["ytd"],
            last_month=expense_data["last_month"],
            trend_direction=trend_direction,
            by_category=expense_data["by_category"] if include_categories else None,
            period=period,
            period_start=start_date.strftime("%Y-%m-%d"),
            period_end=end_date.strftime("%Y-%m-%d"),
            data_quality={
                "historical_comparison": "unavailable",
                "trend_mode": "snapshot_only",
                "period_values": "only_requested_period_populated",
            },
        )

    def _parse_pl_expenses(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse P&L result to extract expense data."""
        data = {
            "expenses": 0.0,
            "categories": [],
        }

        if service == "quickbooks":
            # QuickBooks P&L report structure
            rows = result.get("Rows", {}).get("Row", [])

            for row in rows:
                group = row.get("group", "")
                summary = row.get("Summary", {})

                if "expense" in group.lower() or "cost" in group.lower():
                    col_data = summary.get("ColData", [])
                    if col_data:
                        with contextlib.suppress(ValueError, IndexError):
                            data["expenses"] += float(col_data[-1].get("value", 0) or 0)

                    # Extract category breakdown
                    section_rows = row.get("Rows", {}).get("Row", [])
                    for sub_row in section_rows:
                        sub_col_data = sub_row.get("ColData", [])
                        if len(sub_col_data) >= 2:
                            try:
                                category = sub_col_data[0].get("value", "Other")
                                amount = float(sub_col_data[-1].get("value", 0) or 0)
                                if amount != 0:
                                    data["categories"].append(
                                        {"category": category, "amount": abs(amount)}
                                    )
                            except (ValueError, TypeError):
                                pass

        elif service == "xero":
            # Xero P&L report
            reports = result.get("Reports", [])
            if reports:
                report = reports[0]
                rows = report.get("Rows", [])

                for row in rows:
                    title = row.get("Title", "").lower()

                    if "expense" in title or "cost" in title:
                        for sub_row in row.get("Rows", []):
                            cells = sub_row.get("Cells", [])
                            if len(cells) >= 2:
                                try:
                                    category = cells[0].get("Value", "Other")
                                    amount = float(cells[-1].get("Value", 0) or 0)
                                    data["expenses"] += abs(amount)
                                    if amount != 0:
                                        data["categories"].append(
                                            {"category": category, "amount": abs(amount)}
                                        )
                                except (ValueError, TypeError):
                                    pass

        elif service == "sage_intacct":
            # Sage Intacct P&L
            expenses = result.get("total_expenses", result.get("TOTALEXPENSES", 0))
            data["expenses"] = abs(float(expenses))

            categories = result.get("expense_breakdown", result.get("categories", []))
            for cat in categories:
                data["categories"].append(
                    {
                        "category": cat.get("name", cat.get("NAME", "Other")),
                        "amount": abs(float(cat.get("amount", cat.get("AMOUNT", 0)))),
                    }
                )

        elif service == "netsuite":
            # NetSuite P&L
            expenses = result.get("totalExpenses", result.get("total_expenses", 0))
            data["expenses"] = abs(float(expenses))

            categories = result.get("expenseCategories", result.get("categories", []))
            for cat in categories:
                data["categories"].append(
                    {
                        "category": cat.get("name", "Other"),
                        "amount": abs(float(cat.get("amount", 0))),
                    }
                )

        return data

    def _calculate_expense_period_values(
        self,
        org_id: str,
        user_id: str,
        expense_data: dict[str, Any],
        primary_service: str | None,
        period: str,
    ) -> dict[str, Any]:
        """Populate only period values explicitly requested by caller."""
        _ = (org_id, user_id, primary_service)
        current = expense_data["total"]
        expense_data["mtd"] = current if period == "mtd" else None
        expense_data["ytd"] = current if period == "ytd" else None
        expense_data["last_month"] = current if period == "last_month" else None

        return expense_data

    def _get_prior_expenses(
        self,
        org_id: str,
        user_id: str,
        current_total: float,
        period: str,
    ) -> float:
        """Get prior period expenses for comparison.

        Historical expense snapshots are not yet wired. Return current value so
        delta metrics remain truthful instead of inferred.
        """
        _ = (org_id, user_id, period)
        return current_total

    def _generate_expense_trend(
        self,
        current_total: float,
        change_percent: float,
    ) -> list[dict[str, Any]]:
        """Generate trend data points for expense sparkline."""
        _ = change_percent  # reserved for future historical mode
        today = datetime.now(UTC)
        return [{"date": today.strftime("%Y-%m"), "value": round(current_total, 2)}]

    def _generate_expense_insight(
        self,
        expense_data: dict[str, Any],
        change_percent: float,
    ) -> str:
        """Generate insight string for expenses."""
        total = expense_data["total"]
        categories = expense_data.get("by_category", [])

        # Find largest expense category
        if categories:
            largest = max(categories, key=lambda x: x.get("amount", 0))
            largest_pct = (largest["amount"] / total * 100) if total > 0 else 0
            if largest_pct > 30:
                cat_name = largest["category"]
                return f"Expenses ${total:,.0f}; {cat_name} is {largest_pct:.0f}% of total"

        direction = "up" if change_percent > 0 else "down" if change_percent < 0 else "unchanged"

        if change_percent == 0:
            return f"Expenses unchanged at ${total:,.0f}"

        return f"Expenses {direction} {abs(change_percent):.1f}% to ${total:,.0f}"
