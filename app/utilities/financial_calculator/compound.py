"""
Compound interest and payback period calculations for Financial Calculator utility.
"""

from decimal import Decimal
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .depreciation import DepreciationMixin

logger = get_logger(__name__)


class CompoundMixin(DepreciationMixin):
    """Mixin with compound interest and payback period calculations."""

    def calculate_compound_interest(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculate compound interest growth.

        Args:
            principal: Initial investment
            annual_rate: Annual interest rate as decimal
            years: Number of years
            compounds_per_year: Compounding frequency (default 12 for monthly)
            monthly_contribution: Optional regular contribution

        Returns:
            final_value: Final investment value
            total_interest: Total interest earned
            total_contributions: Total contributions made
            growth_schedule: Year-by-year breakdown
        """
        self._ensure_initialized()

        principal = args.get("principal")
        if principal is None or principal < 0:
            raise ValidationError("principal", "Non-negative principal is required")

        annual_rate = args.get("annual_rate")
        if annual_rate is None:
            raise ValidationError("annual_rate", "Annual rate is required")

        years = args.get("years")
        if not years or years <= 0:
            raise ValidationError("years", "Positive number of years is required")

        compounds_per_year = args.get("compounds_per_year", 12)
        monthly_contribution = Decimal(str(args.get("monthly_contribution", 0)))

        principal = Decimal(str(principal))
        rate = Decimal(str(annual_rate))
        period_rate = rate / compounds_per_year

        schedule = []
        balance = principal
        total_contributions = principal

        for year in range(1, years + 1):
            year_start_balance = balance

            # Compound interest for each period
            for _period in range(compounds_per_year):
                balance *= 1 + period_rate
                balance += monthly_contribution
                total_contributions += monthly_contribution

            interest_this_year = (
                balance - year_start_balance - (monthly_contribution * compounds_per_year)
            )

            contributions_val = (monthly_contribution * compounds_per_year).quantize(
                Decimal("0.01")
            )
            schedule.append(
                {
                    "year": year,
                    "start_balance": float(year_start_balance.quantize(Decimal("0.01"))),
                    "contributions": float(contributions_val),
                    "interest_earned": float(interest_this_year.quantize(Decimal("0.01"))),
                    "end_balance": float(balance.quantize(Decimal("0.01"))),
                }
            )

        final_value = float(balance.quantize(Decimal("0.01")))
        total_interest = float((balance - total_contributions).quantize(Decimal("0.01")))

        logger.info(
            "Compound interest calculated",
            service=self.SERVICE_NAME,
            principal=float(principal),
            years=years,
            final_value=final_value,
            log_event="calc_compound_interest_success",
        )

        self._track_usage()

        return {
            "final_value": final_value,
            "total_interest": total_interest,
            "total_contributions": float(total_contributions.quantize(Decimal("0.01"))),
            "growth_schedule": schedule,
            "status": "success",
        }

    def calculate_payback_period(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculate investment payback period.

        Args:
            initial_investment: Initial investment (positive number)
            cash_flows: List of expected cash flows per period
            discounted: Whether to use discounted payback (default False)
            discount_rate: Discount rate if using discounted payback

        Returns:
            payback_period: Number of periods to recover investment
            payback_months: Payback period in months (if periods are years)
            cumulative_cash_flows: Running total of cash flows
            recovers_investment: Whether investment is recovered
        """
        self._ensure_initialized()

        initial_investment = args.get("initial_investment")
        if not initial_investment or initial_investment <= 0:
            raise ValidationError("initial_investment", "Positive initial investment is required")

        cash_flows = args.get("cash_flows")
        if not cash_flows or not isinstance(cash_flows, list):
            raise ValidationError("cash_flows", "List of cash flows is required")

        discounted = args.get("discounted", False)
        discount_rate = args.get("discount_rate", 0.10)

        investment = Decimal(str(initial_investment))
        cumulative = []
        running_total = Decimal("0")
        payback_period = None

        for i, cf in enumerate(cash_flows):
            cf_decimal = Decimal(str(cf))

            if discounted:
                cf_decimal = cf_decimal / Decimal(str((1 + discount_rate) ** (i + 1)))

            running_total += cf_decimal
            cumulative.append(
                {
                    "period": i + 1,
                    "cash_flow": float(Decimal(str(cf)).quantize(Decimal("0.01"))),
                    "discounted_cash_flow": (
                        float(cf_decimal.quantize(Decimal("0.01"))) if discounted else None
                    ),
                    "cumulative": float(running_total.quantize(Decimal("0.01"))),
                    "remaining": float((investment - running_total).quantize(Decimal("0.01"))),
                }
            )

            if payback_period is None and running_total >= investment:
                # Interpolate for fractional period
                previous_cumulative = running_total - cf_decimal
                if cf_decimal == 0:
                    fraction = 0.0
                else:
                    fraction = float((investment - previous_cumulative) / cf_decimal)
                payback_period = i + fraction

        recovers = running_total >= investment

        logger.info(
            "Payback period calculated",
            service=self.SERVICE_NAME,
            initial_investment=float(investment),
            num_periods=len(cash_flows),
            payback_period=payback_period,
            recovers=recovers,
            log_event="calc_payback_period_success",
        )

        self._track_usage()

        return {
            "payback_period": round(payback_period, 2) if payback_period else None,
            "payback_months": round(payback_period * 12, 1) if payback_period else None,
            "cumulative_cash_flows": cumulative,
            "recovers_investment": recovers,
            "discounted": discounted,
            "status": "success",
        }
