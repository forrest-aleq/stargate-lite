"""
NPV and IRR calculations for Financial Calculator utility.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .base import FinancialCalculatorBase

logger = get_logger(__name__)


class NpvIrrMixin(FinancialCalculatorBase):
    """Mixin with NPV and IRR calculations."""

    def calculate_npv(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate Net Present Value (NPV).

        Args:
            cash_flows: List of cash flows (first is typically negative - initial investment)
            discount_rate: Annual discount rate as decimal (e.g., 0.10 for 10%)
            periods_per_year: Number of periods per year (default 1 for annual)

        Returns:
            npv: Net Present Value
            present_values: List of present values for each cash flow
            is_profitable: Whether NPV > 0
        """
        self._ensure_initialized()

        cash_flows = args.get("cash_flows")
        if not cash_flows or not isinstance(cash_flows, list):
            raise ValidationError("cash_flows", "List of cash flows is required")

        discount_rate = args.get("discount_rate")
        if discount_rate is None:
            raise ValidationError("discount_rate", "Discount rate is required")

        periods_per_year = args.get("periods_per_year", 1)
        if periods_per_year <= 0:
            raise ValidationError("periods_per_year", "periods_per_year must be positive")
        period_rate = discount_rate / periods_per_year

        present_values = []
        npv = Decimal("0")

        for i, cf in enumerate(cash_flows):
            pv = Decimal(str(cf)) / Decimal(str((1 + period_rate) ** i))
            present_values.append(float(pv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)))
            npv += pv

        npv_rounded = float(npv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        logger.info(
            "NPV calculated",
            service=self.SERVICE_NAME,
            num_periods=len(cash_flows),
            npv=npv_rounded,
            log_event="calc_npv_success",
        )

        self._track_usage()

        return {
            "npv": npv_rounded,
            "present_values": present_values,
            "discount_rate": discount_rate,
            "is_profitable": npv_rounded > 0,
            "status": "success",
        }

    def calculate_irr(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate Internal Rate of Return (IRR) using Newton-Raphson method.

        Args:
            cash_flows: List of cash flows (first should be negative - initial investment)
            precision: Decimal precision (default 0.0001)
            max_iterations: Maximum iterations (default 1000)

        Returns:
            irr: Internal Rate of Return as decimal
            irr_percentage: IRR as percentage string
            converged: Whether calculation converged
        """
        self._ensure_initialized()

        cash_flows = args.get("cash_flows")
        if not cash_flows or not isinstance(cash_flows, list):
            raise ValidationError("cash_flows", "List of cash flows is required")

        if len(cash_flows) < 2:
            raise ValidationError("cash_flows", "At least 2 cash flows required")

        precision = args.get("precision", 0.0001)
        max_iterations = args.get("max_iterations", 1000)
        if max_iterations <= 0:
            raise ValidationError("max_iterations", "max_iterations must be positive")

        # Newton-Raphson method
        rate = 0.1  # Initial guess
        converged = False

        for iteration in range(max_iterations):  # noqa: B007 - iteration used after loop
            # Calculate NPV at current rate
            npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))

            # Calculate derivative of NPV
            npv_derivative = sum(
                -i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows)
            )

            if abs(npv_derivative) < 1e-10:
                break

            new_rate = rate - npv / npv_derivative

            if abs(new_rate - rate) < precision:
                rate = new_rate
                converged = True
                break

            rate = new_rate
        irr_rounded = round(rate, 6)

        logger.info(
            "IRR calculated",
            service=self.SERVICE_NAME,
            num_periods=len(cash_flows),
            irr=irr_rounded,
            converged=converged,
            iterations=iteration + 1,
            log_event="calc_irr_success",
        )

        self._track_usage()

        return {
            "irr": irr_rounded,
            "irr_percentage": f"{irr_rounded * 100:.2f}%",
            "converged": converged,
            "iterations": iteration + 1,
            "status": "success",
        }
