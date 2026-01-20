"""
Covenant Calculator for Financial Operations utility.

Calculates and monitors loan covenant compliance:
- DSCR (Debt Service Coverage Ratio)
- LTV (Loan-to-Value)
- Net Worth requirements
- Occupancy requirements
- Custom covenant thresholds
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .matching import MatchingMixin

logger = get_logger(__name__)


class CovenantsMixin(MatchingMixin):
    """Mixin providing covenant calculation capabilities."""

    def calculate_dscr(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate Debt Service Coverage Ratio (DSCR).

        DSCR = Net Operating Income / Total Debt Service

        Args:
            net_operating_income: NOI for the period
            total_debt_service: Total debt payments for the period
            required_minimum: Optional minimum DSCR requirement (default 1.25)

        Returns:
            dscr: Calculated DSCR ratio
            is_compliant: Whether DSCR meets minimum requirement
            headroom: Amount of additional debt service that could be covered
            headroom_percentage: Headroom as percentage of current debt service
        """
        self._ensure_initialized()

        noi = args.get("net_operating_income")
        if noi is None:
            raise ValidationError("net_operating_income", "Net operating income required")

        debt_service = args.get("total_debt_service")
        if debt_service is None:
            raise ValidationError("total_debt_service", "Total debt service required")

        required_minimum = Decimal(str(args.get("required_minimum", 1.25)))

        noi_decimal = Decimal(str(noi))
        debt_service_decimal = Decimal(str(debt_service))

        if debt_service_decimal == 0:
            raise ValidationError("total_debt_service", "Debt service cannot be zero")

        dscr = noi_decimal / debt_service_decimal
        dscr_rounded = float(dscr.quantize(Decimal("0.01"), ROUND_HALF_UP))

        is_compliant = dscr >= required_minimum

        # Headroom calculation: how much more debt service could be covered
        # At minimum DSCR, debt_service_max = NOI / required_minimum
        max_debt_service = noi_decimal / required_minimum
        headroom = max_debt_service - debt_service_decimal
        headroom_pct = (headroom / debt_service_decimal * 100) if debt_service_decimal > 0 else 0

        result = {
            "dscr": dscr_rounded,
            "required_minimum": float(required_minimum),
            "is_compliant": is_compliant,
            "headroom": float(headroom.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "headroom_percentage": float(
                Decimal(str(headroom_pct)).quantize(Decimal("0.1"), ROUND_HALF_UP)
            ),
            "net_operating_income": float(noi_decimal),
            "total_debt_service": float(debt_service_decimal),
            "status": "success",
        }

        if not is_compliant:
            # Calculate how much NOI increase needed
            required_noi = required_minimum * debt_service_decimal
            noi_shortfall = required_noi - noi_decimal
            result["noi_shortfall"] = float(noi_shortfall.quantize(Decimal("0.01"), ROUND_HALF_UP))
            result["compliance_gap"] = float(
                (required_minimum - dscr).quantize(Decimal("0.01"), ROUND_HALF_UP)
            )

        logger.info(
            "DSCR calculated",
            service=self.SERVICE_NAME,
            dscr=dscr_rounded,
            is_compliant=is_compliant,
            log_event="dscr_calculated",
        )

        self._track_usage()
        return result

    def calculate_ltv(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate Loan-to-Value Ratio (LTV).

        LTV = Loan Balance / Property Value

        Args:
            loan_balance: Current loan balance
            property_value: Current property value (or appraised value)
            required_maximum: Maximum LTV allowed (default 0.75 = 75%)

        Returns:
            ltv: Calculated LTV ratio
            ltv_percentage: LTV as percentage
            is_compliant: Whether LTV is within maximum
            equity: Property value minus loan balance
            equity_percentage: Equity as percentage of property value
        """
        self._ensure_initialized()

        loan_balance = args.get("loan_balance")
        if loan_balance is None:
            raise ValidationError("loan_balance", "Loan balance required")

        property_value = args.get("property_value")
        if property_value is None:
            raise ValidationError("property_value", "Property value required")

        required_maximum = Decimal(str(args.get("required_maximum", 0.75)))

        loan_decimal = Decimal(str(loan_balance))
        value_decimal = Decimal(str(property_value))

        if value_decimal == 0:
            raise ValidationError("property_value", "Property value cannot be zero")

        ltv = loan_decimal / value_decimal
        ltv_rounded = float(ltv.quantize(Decimal("0.0001"), ROUND_HALF_UP))

        is_compliant = ltv <= required_maximum

        equity = value_decimal - loan_decimal
        equity_pct = equity / value_decimal * 100

        result = {
            "ltv": ltv_rounded,
            "ltv_percentage": round(ltv_rounded * 100, 2),
            "required_maximum": float(required_maximum),
            "required_maximum_percentage": float(required_maximum * 100),
            "is_compliant": is_compliant,
            "equity": float(equity.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "equity_percentage": float(equity_pct.quantize(Decimal("0.1"), ROUND_HALF_UP)),
            "loan_balance": float(loan_decimal),
            "property_value": float(value_decimal),
            "status": "success",
        }

        if not is_compliant:
            # Calculate required paydown or value increase
            max_loan = required_maximum * value_decimal
            required_paydown = loan_decimal - max_loan
            result["required_paydown"] = float(
                required_paydown.quantize(Decimal("0.01"), ROUND_HALF_UP)
            )

            # Or required value increase
            required_value = loan_decimal / required_maximum
            value_gap = required_value - value_decimal
            result["required_value_increase"] = float(
                value_gap.quantize(Decimal("0.01"), ROUND_HALF_UP)
            )

        logger.info(
            "LTV calculated",
            service=self.SERVICE_NAME,
            ltv=ltv_rounded,
            is_compliant=is_compliant,
            log_event="ltv_calculated",
        )

        self._track_usage()
        return result

    def check_covenant_compliance(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Check compliance against a custom covenant threshold.

        Args:
            covenant_type: Type of covenant (e.g., "dscr", "ltv", "net_worth")
            actual_value: Current calculated value
            required_threshold: Required threshold value
            comparison: Comparison operator (">=" | "<=" | ">" | "<" | "==")
            cure_period_days: Optional days allowed to cure violation

        Returns:
            is_compliant: Whether covenant is met
            variance: Difference from threshold
            variance_percentage: Variance as percentage
            cure_deadline: If violated and cure period set
        """
        self._ensure_initialized()

        covenant_type = args.get("covenant_type")
        if not covenant_type:
            raise ValidationError("covenant_type", "Covenant type required")

        actual_value = args.get("actual_value")
        if actual_value is None:
            raise ValidationError("actual_value", "Actual value required")

        required_threshold = args.get("required_threshold")
        if required_threshold is None:
            raise ValidationError("required_threshold", "Required threshold required")

        comparison = args.get("comparison", ">=")
        cure_period_days = args.get("cure_period_days")

        actual = Decimal(str(actual_value))
        threshold = Decimal(str(required_threshold))

        # Determine compliance based on comparison operator
        comparison_ops = {
            ">=": actual >= threshold,
            "<=": actual <= threshold,
            ">": actual > threshold,
            "<": actual < threshold,
            "==": actual == threshold,
        }

        if comparison not in comparison_ops:
            raise ValidationError("comparison", f"Invalid comparison operator: {comparison}")

        is_compliant = comparison_ops[comparison]

        variance = actual - threshold
        variance_pct = (variance / threshold * 100) if threshold != 0 else Decimal("0")

        result = {
            "covenant_type": covenant_type,
            "actual_value": float(actual),
            "required_threshold": float(threshold),
            "comparison": comparison,
            "is_compliant": is_compliant,
            "variance": float(variance.quantize(Decimal("0.0001"), ROUND_HALF_UP)),
            "variance_percentage": float(variance_pct.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "status": "success",
        }

        if not is_compliant and cure_period_days:
            from datetime import timedelta

            cure_deadline = datetime.now() + timedelta(days=cure_period_days)
            result["cure_period_days"] = cure_period_days
            result["cure_deadline"] = cure_deadline.isoformat()
            result["days_to_cure"] = cure_period_days

        logger.info(
            "Covenant compliance checked",
            service=self.SERVICE_NAME,
            covenant_type=covenant_type,
            is_compliant=is_compliant,
            log_event="covenant_check",
        )

        self._track_usage()
        return result

    def covenant_summary(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Generate summary of multiple covenant checks.

        Args:
            covenants: List of covenant checks to perform, each with:
                - covenant_type: Type name
                - actual_value: Current value
                - required_threshold: Required threshold
                - comparison: Comparison operator
                - cure_period_days: Optional cure period

        Returns:
            results: Individual covenant results
            summary: Overall compliance summary
            violations: List of violated covenants
        """
        self._ensure_initialized()

        covenants = args.get("covenants")
        if not covenants or not isinstance(covenants, list):
            raise ValidationError("covenants", "List of covenants required")

        results = []
        violations = []

        for covenant in covenants:
            result = self.check_covenant_compliance(org_id, user_id, covenant)
            results.append(result)
            if not result["is_compliant"]:
                violations.append(
                    {
                        "covenant_type": result["covenant_type"],
                        "actual_value": result["actual_value"],
                        "required_threshold": result["required_threshold"],
                        "variance": result["variance"],
                    }
                )

        summary = {
            "total_covenants": len(covenants),
            "compliant_count": len(covenants) - len(violations),
            "violation_count": len(violations),
            "compliance_rate": round(
                (len(covenants) - len(violations)) / max(len(covenants), 1) * 100, 1
            ),
            "overall_compliant": len(violations) == 0,
        }

        logger.info(
            "Covenant summary generated",
            service=self.SERVICE_NAME,
            total=len(covenants),
            violations=len(violations),
            log_event="covenant_summary",
        )

        self._track_usage()

        return {
            "results": results,
            "violations": violations,
            "summary": summary,
            "status": "success",
        }
