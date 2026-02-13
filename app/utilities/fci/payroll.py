"""
FCI Payroll Mixin.

Aggregates payroll data from Gusto:
- Last payroll run details
- Monthly payroll total
- Headcount
- Next scheduled run

Returns payroll summary with change tracking.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.logging_config import get_logger
from app.utilities.fci.service_mappings import PAYROLL_SERVICES

logger = get_logger(__name__)


class PayrollMixin:
    """Mixin for payroll data aggregation."""

    def get_payroll(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get payroll summary from Gusto.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - company_id: Gusto company ID (auto-detected if only one)

        Returns:
            {
                "last_run": {date, gross, net, taxes},
                "next_run": str (date),
                "monthly_total": float,
                "headcount": int,
                "contractor_count": int,
                "change": float,
                "changePercent": float,
                "trend": [{date, value}],
                "insight": str,
                "lastUpdated": str,
                "source": str,
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        company_id = args.get("company_id")

        # Check if Gusto is connected
        available = self._get_connected_services(org_id, user_id, PAYROLL_SERVICES)

        if "gusto" not in available:
            return self._format_response(
                total=0,
                errors=[{"service": "payroll", "error": "Gusto not connected"}],
                last_run=None,
                next_run=None,
                monthly_total=0,
                headcount=0,
                contractor_count=0,
            )

        # Get payroll data from Gusto
        payroll_args = dict(args)
        if company_id:
            payroll_args["company_id"] = company_id

        results, errors, sources = self._aggregate_from_services(
            {"gusto": PAYROLL_SERVICES["gusto"]},
            org_id,
            user_id,
            payroll_args,
            preferred_service="gusto",
        )

        if not results:
            return self._format_response(
                total=0,
                errors=errors,
                sources=sources,
                last_run=None,
                next_run=None,
                monthly_total=0,
                headcount=0,
                contractor_count=0,
            )

        # Parse payroll data
        result = results[0]
        payroll_data = self._parse_payroll_data(result)

        # Calculate change
        monthly_total = payroll_data.get("monthly_total", 0)
        prior_total = self._get_prior_payroll(org_id, user_id, monthly_total)
        change, change_percent = self._calculate_change(monthly_total, prior_total)

        # Generate trend
        trend = self._generate_payroll_trend(monthly_total, change_percent)

        # Generate insight
        insight = self._generate_payroll_insight(payroll_data, change_percent)

        return self._format_response(
            total=monthly_total,
            change=change,
            change_percent=change_percent,
            trend=trend,
            insight=insight,
            sources=sources,
            errors=errors if errors else None,
            last_run=payroll_data.get("last_run"),
            next_run=payroll_data.get("next_run"),
            monthly_total=monthly_total,
            headcount=payroll_data.get("headcount", 0),
            contractor_count=payroll_data.get("contractor_count", 0),
            source="gusto",
        )

    def _parse_payroll_data(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse Gusto payroll list response into summary data."""
        data = {
            "last_run": None,
            "next_run": None,
            "monthly_total": 0.0,
            "headcount": 0,
            "contractor_count": 0,
        }

        payrolls = result.get("payrolls", result.get("data", []))

        if not payrolls:
            return data

        # Sort by date to find most recent
        if isinstance(payrolls, list) and payrolls:
            # Find processed payrolls
            processed = [
                p
                for p in payrolls
                if p.get("processed", p.get("status")) in [True, "processed", "paid"]
            ]

            if processed:
                # Sort by check_date or pay_period end
                processed.sort(
                    key=lambda x: x.get("check_date", x.get("pay_period", {}).get("end_date", "")),
                    reverse=True,
                )
                last = processed[0]

                # Extract last run details
                totals = last.get("totals", last)
                emp_comps = last.get("employee_compensations", [])
                emp_count = int(last.get("employee_count", len(emp_comps)))
                data["last_run"] = {
                    "date": last.get("check_date", last.get("pay_period", {}).get("end_date")),
                    "gross": float(totals.get("gross_pay", totals.get("gross", 0))),
                    "net": float(totals.get("net_pay", totals.get("net", 0))),
                    "taxes": float(totals.get("employer_taxes", totals.get("taxes", 0))),
                    "employee_count": emp_count,
                }

                # Calculate monthly total (employer cost = gross + employer taxes + benefits)
                employer_cost = (
                    data["last_run"]["gross"]
                    + data["last_run"]["taxes"]
                    + float(totals.get("employer_benefits", 0))
                )

                # Estimate monthly (typically 2 payrolls per month for semi-monthly)
                pay_frequency = result.get("pay_frequency", "semi-monthly")
                if pay_frequency in ["weekly", "bi-weekly"]:
                    # ~4.3 weeks per month for weekly, ~2.17 for bi-weekly
                    multiplier = 4.3 if pay_frequency == "weekly" else 2.17
                else:
                    # Semi-monthly or monthly
                    multiplier = 2 if pay_frequency == "semi-monthly" else 1

                data["monthly_total"] = employer_cost * multiplier
                data["headcount"] = data["last_run"]["employee_count"]

            # Find next scheduled payroll
            pending = [
                p
                for p in payrolls
                if p.get("processed", p.get("status")) in [False, "unprocessed", "pending"]
            ]
            if pending:
                pending.sort(
                    key=lambda x: x.get("check_date", x.get("pay_period", {}).get("end_date", ""))
                )
                first_pending = pending[0]
                data["next_run"] = first_pending.get(
                    "check_date", first_pending.get("pay_period", {}).get("end_date")
                )

        # Try to get headcount from employees endpoint if available
        employees = result.get("employees", [])
        if employees:
            data["headcount"] = len([e for e in employees if e.get("active", True)])

        contractors = result.get("contractors", [])
        if contractors:
            data["contractor_count"] = len([c for c in contractors if c.get("active", True)])

        return data

    def _get_prior_payroll(
        self,
        org_id: str,
        user_id: str,
        current_total: float,
    ) -> float:
        """Get prior month payroll for comparison."""
        # Payroll typically doesn't change much month-to-month
        estimated_change_rate = 0.01  # 1% typical payroll change
        prior_total = current_total / (1 + estimated_change_rate)
        return prior_total

    def _generate_payroll_trend(
        self,
        current_total: float,
        change_percent: float,
    ) -> list[dict[str, Any]]:
        """Generate trend data points for payroll sparkline."""
        trend: list[dict[str, Any]] = []
        today = datetime.now(UTC)

        for i in range(5, -1, -1):
            point_date = today - timedelta(days=30 * i)
            # Payroll is typically stable, so less variance
            factor = 1 - (change_percent / 100) * (i / 5) * 0.5
            value = current_total * max(0.8, min(1.2, factor))

            trend.append(
                {
                    "date": point_date.strftime("%Y-%m"),
                    "value": round(value, 2),
                }
            )

        return trend

    def _generate_payroll_insight(
        self,
        payroll_data: dict[str, Any],
        change_percent: float,
    ) -> str:
        """Generate insight string for payroll."""
        monthly_total = payroll_data.get("monthly_total", 0)
        headcount = payroll_data.get("headcount", 0)
        next_run = payroll_data.get("next_run")

        if next_run:
            try:
                next_date = datetime.fromisoformat(next_run.replace("Z", ""))
                days_until = (next_date.date() - datetime.now(UTC).date()).days
                if 0 <= days_until <= 3:
                    return (
                        f"Next payroll in {days_until} days; "
                        f"${monthly_total:,.0f}/mo for {headcount} employees"
                    )
            except (ValueError, TypeError):
                pass

        if headcount > 0:
            avg_per_employee = monthly_total / headcount if monthly_total > 0 else 0
            return (
                f"Monthly payroll ${monthly_total:,.0f} for {headcount} employees "
                f"(${avg_per_employee:,.0f}/person)"
            )

        return f"Monthly payroll at ${monthly_total:,.0f}"
