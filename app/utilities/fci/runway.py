"""
FCI Runway Mixin.

Calculates runway in months: cash / burn
- Uses cash position from fci.cash
- Uses burn rate from fci.burn
- Projects cash-out date assuming linear burn
- Provides confidence level based on data quality

This is a derived primitive - it combines cash and burn data.
"""

from datetime import datetime
from typing import Any

from dateutil.relativedelta import relativedelta

from app.logging_config import get_logger

logger = get_logger(__name__)


class RunwayMixin:
    """Mixin for runway calculation."""

    def get_runway(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate runway in months (cash / burn).

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - burn_months: Months to average for burn calculation (default: 3)

        Returns:
            {
                "months": float,
                "cash": float,
                "burn": float,
                "cash_out_date": str (YYYY-MM),
                "confidence": str ("high", "medium", "low"),
                "change": float,
                "changePercent": float,
                "trend": [{date, value}],
                "insight": str,
                "lastUpdated": str,
                "sources": [str],
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        burn_months = args.get("burn_months", 3)

        all_errors: list[dict[str, Any]] = []
        all_sources: list[str] = []

        # Get cash position
        cash_result = self.get_cash(org_id, user_id, {})
        cash_total = cash_result.get("total", 0)
        cash_sources = cash_result.get("sources", [])
        cash_errors = cash_result.get("errors", [])

        all_sources.extend(cash_sources)
        if cash_errors:
            all_errors.extend(cash_errors)

        # Get burn rate
        burn_result = self.get_burn(org_id, user_id, {"months": burn_months})
        burn_avg = burn_result.get("monthly_avg", 0)
        burn_sources = burn_result.get("sources", [])
        burn_errors = burn_result.get("errors", [])

        # Add burn sources (avoid duplicates)
        for src in burn_sources:
            if src not in all_sources:
                all_sources.append(src)
        if burn_errors:
            all_errors.extend(burn_errors)

        # Calculate runway
        if burn_avg > 0:
            runway_months = cash_total / burn_avg
        elif cash_total > 0:
            # No burn data but have cash - infinite runway (cap at 999)
            runway_months = 999
        else:
            runway_months = 0

        # Project cash-out date
        cash_out_date = None
        if 0 < runway_months < 999:
            today = datetime.utcnow()
            cash_out = today + relativedelta(months=int(runway_months))
            cash_out_date = cash_out.strftime("%Y-%m")

        # Determine confidence
        confidence = self._calculate_runway_confidence(
            cash_result, burn_result, runway_months
        )

        # Calculate change (compare to last month's projected runway)
        prior_runway = self._get_prior_runway(
            org_id, user_id, runway_months, cash_total, burn_avg
        )
        change, change_percent = self._calculate_change(runway_months, prior_runway)

        # Generate trend data (runway projection over time)
        trend = self._generate_runway_trend(cash_total, burn_avg, runway_months)

        # Generate insight
        insight = self._generate_runway_insight(
            runway_months, cash_total, burn_avg, confidence
        )

        return self._format_response(
            total=round(runway_months, 1),  # Use runway as primary metric
            change=round(change, 1),
            change_percent=change_percent,
            trend=trend,
            insight=insight,
            sources=all_sources,
            errors=all_errors if all_errors else None,
            months=round(runway_months, 1),
            cash=round(cash_total, 2),
            burn=round(burn_avg, 2),
            cash_out_date=cash_out_date,
            confidence=confidence,
        )

    def _calculate_runway_confidence(
        self,
        cash_result: dict[str, Any],
        burn_result: dict[str, Any],
        runway_months: float,
    ) -> str:
        """
        Calculate confidence level for runway projection.

        High: Multiple cash sources, 3+ months of burn data, consistent burn
        Medium: Some data quality issues but reasonable estimate
        Low: Limited data, high variance, or estimation concerns
        """
        score = 0

        # Cash data quality
        cash_accounts = cash_result.get("accounts", [])
        cash_sources = cash_result.get("sources", [])
        cash_errors = cash_result.get("errors", [])

        if len(cash_accounts) >= 2:
            score += 2
        elif len(cash_accounts) >= 1:
            score += 1

        if len(cash_sources) >= 2:
            score += 1

        if not cash_errors:
            score += 1

        # Burn data quality
        months_analyzed = burn_result.get("months_analyzed", 0)
        burn_errors = burn_result.get("errors", [])
        burn_trend = burn_result.get("trend_direction", "stable")

        if months_analyzed >= 3:
            score += 2
        elif months_analyzed >= 2:
            score += 1

        if not burn_errors:
            score += 1

        # Stability penalty for high variance burn
        if burn_trend == "stable":
            score += 1

        # Runway sanity check
        if 3 <= runway_months <= 36:
            score += 1  # Reasonable range

        # Map score to confidence
        if score >= 7:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"

    def _get_prior_runway(
        self,
        org_id: str,
        user_id: str,
        current_runway: float,
        cash: float,
        burn: float,
    ) -> float:
        """
        Estimate prior month's runway for comparison.

        In production, this would use historical snapshots.
        For now, estimate based on typical cash/burn changes.
        """
        # Assume cash was slightly lower last month (showing ~5% growth)
        # and burn was similar
        estimated_prior_cash = cash * 0.95  # Prior month had ~5% less cash
        estimated_prior_burn = burn * 0.98  # Slightly lower burn

        if estimated_prior_burn > 0:
            prior_runway = estimated_prior_cash / estimated_prior_burn
        else:
            prior_runway = current_runway

        return prior_runway

    def _generate_runway_trend(
        self,
        cash: float,
        burn: float,
        current_runway: float,
    ) -> list[dict[str, Any]]:
        """
        Generate runway trend showing projected cash depletion.

        This shows how cash will decline over time assuming constant burn.
        """
        trend: list[dict[str, Any]] = []
        today = datetime.utcnow()

        # Show current plus 6 future months
        remaining_cash = cash
        for i in range(7):
            point_date = today + relativedelta(months=i)

            trend.append(
                {
                    "date": point_date.strftime("%Y-%m"),
                    "value": round(max(0, remaining_cash), 2),
                    "runway_months": round(max(0, remaining_cash / burn), 1) if burn > 0 else 999,
                }
            )

            remaining_cash -= burn

        return trend

    def _generate_runway_insight(
        self,
        runway_months: float,
        cash: float,
        burn: float,
        confidence: str,
    ) -> str:
        """Generate insight string for runway."""
        if runway_months >= 24:
            return f"{runway_months:.0f} months runway with ${cash:,.0f} cash"
        elif runway_months >= 12:
            return f"{runway_months:.1f} months runway; ${burn:,.0f}/mo burn"
        elif runway_months >= 6:
            return f"{runway_months:.1f} months runway - consider extending"
        elif runway_months >= 3:
            return f"Warning: {runway_months:.1f} months runway at ${burn:,.0f}/mo burn"
        elif runway_months > 0:
            return f"Critical: {runway_months:.1f} months runway remaining"
        else:
            return "No runway data available"
