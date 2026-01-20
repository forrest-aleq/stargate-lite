"""
Asset depreciation calculations for Financial Calculator utility.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .amortization import AmortizationMixin

logger = get_logger(__name__)


class DepreciationMixin(AmortizationMixin):
    """Mixin with asset depreciation calculations."""

    def _validate_depreciation_args(
        self, args: dict[str, Any]
    ) -> tuple[Decimal, Decimal, int, str, datetime]:
        """Validate and extract depreciation arguments."""
        cost = args.get("cost")
        if not cost or cost <= 0:
            raise ValidationError("cost", "Positive asset cost is required")

        salvage_value = args.get("salvage_value", 0)
        if salvage_value < 0:
            raise ValidationError("salvage_value", "Salvage value cannot be negative")

        useful_life = args.get("useful_life_years")
        if not useful_life or useful_life <= 0:
            raise ValidationError("useful_life_years", "Positive useful life is required")

        method = args.get("method", "straight_line")
        start_date_str = args.get("start_date")
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else datetime.now()

        return (Decimal(str(cost)), Decimal(str(salvage_value)), useful_life, method, start_date)

    def _straight_line_schedule(
        self, cost: Decimal, salvage: Decimal, useful_life: int, start_year: int
    ) -> list[dict[str, Any]]:
        """Generate straight-line depreciation schedule."""
        depreciable_amount = cost - salvage
        annual_depreciation = depreciable_amount / useful_life
        book_value = cost
        accumulated = Decimal("0")
        schedule = []

        for year in range(1, useful_life + 1):
            depreciation = annual_depreciation.quantize(Decimal("0.01"))
            book_value -= depreciation
            accumulated += depreciation

            schedule.append(
                {
                    "year": year,
                    "date": f"{start_year + year - 1}",
                    "depreciation": float(depreciation),
                    "accumulated": float(accumulated),
                    "book_value": float(max(salvage, book_value)),
                }
            )

        return schedule

    def _declining_balance_schedule(
        self, cost: Decimal, salvage: Decimal, useful_life: int, start_year: int
    ) -> list[dict[str, Any]]:
        """Generate double declining balance depreciation schedule."""
        rate = Decimal(str(2 / useful_life))
        book_value = cost
        accumulated = Decimal("0")
        schedule = []

        for year in range(1, useful_life + 1):
            depreciation = (book_value * rate).quantize(Decimal("0.01"))

            if book_value - depreciation < salvage:
                depreciation = book_value - salvage

            book_value -= depreciation
            accumulated += depreciation

            schedule.append(
                {
                    "year": year,
                    "date": f"{start_year + year - 1}",
                    "depreciation": float(depreciation),
                    "accumulated": float(accumulated),
                    "book_value": float(book_value),
                }
            )

        return schedule

    def _sum_of_years_schedule(
        self, cost: Decimal, salvage: Decimal, useful_life: int, start_year: int
    ) -> list[dict[str, Any]]:
        """Generate sum-of-years digits depreciation schedule."""
        depreciable_amount = cost - salvage
        sum_of_years = sum(range(1, useful_life + 1))
        book_value = cost
        accumulated = Decimal("0")
        schedule = []

        for year in range(1, useful_life + 1):
            remaining_life = useful_life - year + 1
            depreciation = (depreciable_amount * remaining_life / sum_of_years).quantize(
                Decimal("0.01")
            )

            book_value -= depreciation
            accumulated += depreciation

            schedule.append(
                {
                    "year": year,
                    "date": f"{start_year + year - 1}",
                    "depreciation": float(depreciation),
                    "accumulated": float(accumulated),
                    "book_value": float(book_value),
                }
            )

        return schedule

    def calculate_depreciation(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculate asset depreciation schedule.

        Args:
            cost: Asset cost
            salvage_value: Salvage value at end of life
            useful_life_years: Useful life in years
            method: Depreciation method - "straight_line", "declining_balance", "sum_of_years"
            start_date: Start date (ISO format, default today)

        Returns:
            annual_depreciation: Annual depreciation (for straight-line)
            schedule: Array of depreciation per year
            total_depreciation: Total depreciation over life
        """
        self._ensure_initialized()

        cost, salvage, useful_life, method, start_date = self._validate_depreciation_args(args)

        if method == "straight_line":
            schedule = self._straight_line_schedule(cost, salvage, useful_life, start_date.year)
        elif method == "declining_balance":
            schedule = self._declining_balance_schedule(cost, salvage, useful_life, start_date.year)
        elif method == "sum_of_years":
            schedule = self._sum_of_years_schedule(cost, salvage, useful_life, start_date.year)
        else:
            raise ValidationError("method", f"Unknown depreciation method: {method}")

        total_depreciation = sum(Decimal(str(s["depreciation"])) for s in schedule)

        logger.info(
            "Depreciation schedule calculated",
            service=self.SERVICE_NAME,
            method=method,
            cost=float(cost),
            useful_life=useful_life,
            total_depreciation=float(total_depreciation),
            log_event="calc_depreciation_success",
        )

        self._track_usage()

        return {
            "method": method,
            "total_depreciation": float(total_depreciation),
            "schedule": schedule,
            "status": "success",
        }
