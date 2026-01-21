"""
FCI Burn Rate Mixin.

Calculates monthly burn rate from P&L expense data:
- Average monthly burn over configurable period (3-6 months)
- Last month's burn
- Trend direction and percentage
- Category breakdown

This is a derived primitive - it uses expense data to calculate burn.
"""

from datetime import datetime, timedelta
from typing import Any

from app.logging_config import get_logger
from app.utilities.fci.service_mappings import PL_REPORT_SERVICES

logger = get_logger(__name__)


class BurnMixin:
    """Mixin for burn rate calculation."""

    def get_burn(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get monthly burn rate from P&L expenses.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - months: Number of months to average (default: 3)
                - exclude_categories: Expense categories to exclude (e.g., one-time costs)

        Returns:
            {
                "monthly_avg": float,
                "last_month": float,
                "trend": str ("increasing", "decreasing", "stable"),
                "trend_pct": float,
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
        months = args.get("months", 3)
        exclude_categories = args.get("exclude_categories", [])

        # Get primary accounting system
        primary_service = self._get_primary_accounting_service(
            org_id, user_id, PL_REPORT_SERVICES
        )

        if not primary_service:
            return self._format_response(
                total=0,
                errors=[{"service": "burn", "error": "No accounting system connected"}],
                monthly_avg=0,
                last_month=0,
                trend="stable",
                trend_pct=0,
                by_category=[],
            )

        # Calculate date ranges for multi-month data
        today = datetime.utcnow()
        periods = self._get_monthly_periods(today, months)

        monthly_burns: list[float] = []
        categories_total: dict[str, float] = {}
        all_errors: list[dict[str, Any]] = []
        all_sources: list[str] = []

        # Get expense data for each month
        for period in periods:
            pl_args = {
                "start_date": period["start"],
                "end_date": period["end"],
            }

            results, errors, sources = self._aggregate_from_services(
                {primary_service: PL_REPORT_SERVICES[primary_service]},
                org_id,
                user_id,
                pl_args,
                preferred_service=primary_service,
            )

            all_errors.extend(errors)
            if sources and sources[0] not in all_sources:
                all_sources.extend(sources)

            if results:
                exp_data = self._parse_burn_from_pl(
                    primary_service, results[0], exclude_categories
                )
                monthly_burns.append(exp_data["expenses"])

                # Accumulate categories
                for cat in exp_data.get("categories", []):
                    cat_name = cat["category"]
                    categories_total[cat_name] = categories_total.get(cat_name, 0) + cat["amount"]

        # Calculate burn metrics
        if not monthly_burns:
            return self._format_response(
                total=0,
                errors=all_errors,
                sources=all_sources,
                monthly_avg=0,
                last_month=0,
                trend="stable",
                trend_pct=0,
                by_category=[],
            )

        monthly_avg = sum(monthly_burns) / len(monthly_burns)
        last_month = monthly_burns[-1] if monthly_burns else 0

        # Calculate trend
        trend_direction = self._determine_trend_direction(monthly_burns)

        # Calculate trend percentage (last month vs average)
        if monthly_avg > 0:
            trend_pct = ((last_month - monthly_avg) / monthly_avg) * 100
        else:
            trend_pct = 0

        # Average out categories
        by_category = [
            {"category": cat, "amount": round(amt / len(monthly_burns), 2)}
            for cat, amt in sorted(categories_total.items(), key=lambda x: -x[1])
        ]

        # Calculate change (this month vs prior month)
        prior_month = monthly_burns[-2] if len(monthly_burns) >= 2 else monthly_avg
        change, change_percent = self._calculate_change(last_month, prior_month)

        # Generate trend data
        trend_data = self._generate_burn_trend(monthly_burns, today)

        # Generate insight
        insight = self._generate_burn_insight(monthly_avg, last_month, trend_direction, trend_pct)

        return self._format_response(
            total=monthly_avg,  # Use monthly_avg as the primary "total" for consistency
            change=change,
            change_percent=change_percent,
            trend=trend_data,
            insight=insight,
            sources=all_sources,
            errors=all_errors if all_errors else None,
            monthly_avg=round(monthly_avg, 2),
            last_month=round(last_month, 2),
            trend_direction=trend_direction,
            trend_pct=round(trend_pct, 2),
            by_category=by_category[:10],  # Top 10 categories
            months_analyzed=len(monthly_burns),
        )

    def _get_monthly_periods(
        self,
        end_date: datetime,
        num_months: int,
    ) -> list[dict[str, str]]:
        """Generate date ranges for each month to analyze."""
        periods: list[dict[str, str]] = []

        # Start from the current/last complete month
        current = end_date.replace(day=1)

        for _ in range(num_months):
            # Go back one month
            if current.month == 1:
                prev_month = current.replace(year=current.year - 1, month=12)
            else:
                prev_month = current.replace(month=current.month - 1)

            # Period is from prev_month start to current start - 1 day
            period_end = current - timedelta(days=1)

            periods.insert(0, {
                "start": prev_month.strftime("%Y-%m-%d"),
                "end": period_end.strftime("%Y-%m-%d"),
            })

            current = prev_month

        return periods

    def _parse_burn_from_pl(
        self,
        service: str,
        result: dict[str, Any],
        exclude_categories: list[str],
    ) -> dict[str, Any]:
        """
        Parse P&L result to extract expense/burn data.
        Similar to expenses parsing but with exclusion support.
        """
        data = {
            "expenses": 0.0,
            "categories": [],
        }

        exclude_lower = [c.lower() for c in exclude_categories]

        if service == "quickbooks":
            rows = result.get("Rows", {}).get("Row", [])

            for row in rows:
                group = row.get("group", "")

                if "expense" in group.lower() or "cost" in group.lower():
                    section_rows = row.get("Rows", {}).get("Row", [])
                    for sub_row in section_rows:
                        sub_col_data = sub_row.get("ColData", [])
                        if len(sub_col_data) >= 2:
                            try:
                                category = sub_col_data[0].get("value", "Other")
                                amount = float(sub_col_data[-1].get("value", 0) or 0)

                                # Skip excluded categories
                                if category.lower() in exclude_lower:
                                    continue

                                if amount != 0:
                                    data["expenses"] += abs(amount)
                                    data["categories"].append(
                                        {"category": category, "amount": abs(amount)}
                                    )
                            except (ValueError, TypeError):
                                pass

        elif service == "xero":
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

                                    if category.lower() in exclude_lower:
                                        continue

                                    amount = float(cells[-1].get("Value", 0) or 0)
                                    data["expenses"] += abs(amount)
                                    if amount != 0:
                                        data["categories"].append(
                                            {"category": category, "amount": abs(amount)}
                                        )
                                except (ValueError, TypeError):
                                    pass

        elif service in ["sage_intacct", "netsuite"]:
            expenses = result.get(
                "total_expenses",
                result.get("TOTALEXPENSES", result.get("totalExpenses", 0))
            )
            data["expenses"] = abs(float(expenses))

            categories = result.get(
                "expense_breakdown",
                result.get("categories", result.get("expenseCategories", []))
            )
            for cat in categories:
                cat_name = cat.get("name", cat.get("NAME", "Other"))
                if cat_name.lower() in exclude_lower:
                    continue

                data["categories"].append(
                    {
                        "category": cat_name,
                        "amount": abs(float(cat.get("amount", cat.get("AMOUNT", 0)))),
                    }
                )

        return data

    def _generate_burn_trend(
        self,
        monthly_burns: list[float],
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Generate trend data from actual monthly burn values."""
        trend: list[dict[str, Any]] = []

        for i, burn in enumerate(monthly_burns):
            # Calculate the month for each burn value
            months_back = len(monthly_burns) - 1 - i
            point_date = end_date - timedelta(days=30 * months_back)

            trend.append(
                {
                    "date": point_date.strftime("%Y-%m"),
                    "value": round(burn, 2),
                }
            )

        return trend

    def _generate_burn_insight(
        self,
        monthly_avg: float,
        last_month: float,
        trend: str,
        trend_pct: float,
    ) -> str:
        """Generate insight string for burn rate."""
        if trend == "increasing" and trend_pct > 10:
            return f"Burn rate ${monthly_avg:,.0f}/mo, up {abs(trend_pct):.0f}% - monitor"
        elif trend == "decreasing" and trend_pct < -10:
            return f"Burn rate ${monthly_avg:,.0f}/mo, down {abs(trend_pct):.0f}%"
        elif trend == "stable":
            return f"Burn rate stable at ${monthly_avg:,.0f}/mo"
        else:
            direction = "trending up" if trend == "increasing" else "trending down"
            return f"Burn rate ${monthly_avg:,.0f}/mo, {direction}"
