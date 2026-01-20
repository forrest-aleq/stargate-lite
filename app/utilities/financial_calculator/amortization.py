"""
Loan amortization calculations for Financial Calculator utility.
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from dateutil.relativedelta import relativedelta

from app.errors import ValidationError
from app.logging_config import get_logger

from .npv_irr import NpvIrrMixin

logger = get_logger(__name__)


class AmortizationMixin(NpvIrrMixin):
    """Mixin with loan amortization calculations."""

    def _validate_amortization_args(
        self, args: dict[str, Any]
    ) -> tuple[Decimal, Decimal, int, datetime, Decimal]:
        """Validate and extract amortization arguments."""
        principal = args.get("principal")
        if not principal or principal <= 0:
            raise ValidationError("principal", "Positive principal amount is required")

        annual_rate = args.get("annual_rate")
        if annual_rate is None or annual_rate < 0:
            raise ValidationError("annual_rate", "Non-negative annual rate is required")

        term_months = args.get("term_months")
        if not term_months or term_months <= 0:
            raise ValidationError("term_months", "Positive term in months is required")

        start_date_str = args.get("start_date")
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else datetime.now()

        extra_payment = Decimal(str(args.get("extra_payment", 0)))

        return (
            Decimal(str(principal)),
            Decimal(str(annual_rate)) / 12,
            term_months,
            start_date,
            extra_payment,
        )

    def _calculate_monthly_payment(
        self, principal: Decimal, monthly_rate: Decimal, term_months: int
    ) -> Decimal:
        """Calculate monthly payment using amortization formula."""
        if monthly_rate > 0:
            monthly_payment = (
                principal
                * (monthly_rate * (1 + monthly_rate) ** term_months)
                / ((1 + monthly_rate) ** term_months - 1)
            )
        else:
            monthly_payment = principal / term_months

        return monthly_payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _generate_amortization_schedule(
        self,
        principal: Decimal,
        monthly_rate: Decimal,
        monthly_payment: Decimal,
        extra_payment: Decimal,
        term_months: int,
        start_date: datetime,
    ) -> tuple[list[dict[str, Any]], Decimal]:
        """Generate amortization schedule. Returns (schedule, total_interest)."""
        schedule = []
        balance = principal
        total_interest = Decimal("0")
        payment_date = start_date

        month = 0
        while balance > 0 and month < term_months + 120:
            month += 1
            interest_payment = (balance * monthly_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            total_payment = monthly_payment + extra_payment
            if balance + interest_payment <= total_payment:
                principal_payment = balance
                total_payment = balance + interest_payment
            else:
                principal_payment = total_payment - interest_payment

            balance -= principal_payment
            total_interest += interest_payment

            schedule.append(
                {
                    "month": month,
                    "date": payment_date.strftime("%Y-%m-%d"),
                    "payment": float(total_payment),
                    "principal": float(principal_payment),
                    "interest": float(interest_payment),
                    "balance": float(max(Decimal("0"), balance)),
                }
            )

            payment_date = payment_date + relativedelta(months=1)

            if balance <= 0:
                break

        return schedule, total_interest

    def calculate_amortization(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculate loan amortization schedule.

        Args:
            principal: Loan principal amount
            annual_rate: Annual interest rate as decimal (e.g., 0.05 for 5%)
            term_months: Loan term in months
            start_date: Start date (ISO format, default today)
            extra_payment: Optional extra monthly payment

        Returns:
            monthly_payment: Regular monthly payment
            total_interest: Total interest over loan term
            total_paid: Total amount paid
            schedule: Array of payment details per month
        """
        self._ensure_initialized()

        principal, monthly_rate, term_months, start_date, extra_payment = (
            self._validate_amortization_args(args)
        )

        monthly_payment = self._calculate_monthly_payment(principal, monthly_rate, term_months)

        schedule, total_interest = self._generate_amortization_schedule(
            principal, monthly_rate, monthly_payment, extra_payment, term_months, start_date
        )

        total_paid = float(sum(Decimal(str(p["payment"])) for p in schedule))

        logger.info(
            "Amortization schedule calculated",
            service=self.SERVICE_NAME,
            principal=float(principal),
            term_months=term_months,
            actual_months=len(schedule),
            total_interest=float(total_interest),
            log_event="calc_amortization_success",
        )

        self._track_usage()

        return {
            "monthly_payment": float(monthly_payment),
            "total_interest": float(total_interest.quantize(Decimal("0.01"))),
            "total_paid": total_paid,
            "actual_term_months": len(schedule),
            "schedule": schedule,
            "status": "success",
        }
