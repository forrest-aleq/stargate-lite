"""
Tiered Fee Calculator for Financial Operations utility.

Calculates AUM-based management fees with tiered structures:
- Multiple tiers with breakpoints
- Period proration (annual, quarterly, monthly)
- Minimum fee floors
- Blended effective rate calculation
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .waterfall import WaterfallMixin

logger = get_logger(__name__)

PERIOD_MULTIPLIERS = {
    "annual": Decimal("1"),
    "quarterly": Decimal("0.25"),
    "monthly": Decimal("1") / Decimal("12"),
}

PERIOD_DAYS = {"annual": 365, "quarterly": 91, "monthly": 30}


class TieredFeesMixin(WaterfallMixin):
    """Mixin providing tiered fee calculation capabilities."""

    def calculate_tiered_fee(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate management fee using tiered AUM-based structure."""
        self._ensure_initialized()

        aum, tiers, period, proration_days, minimum_fee = self._validate_fee_args(args)
        aum_decimal = Decimal(str(aum))

        tier_breakdown, total_fee = self._calculate_tiers(aum_decimal, tiers)

        total_fee, prorated = self._apply_period_proration(total_fee, period, proration_days)

        min_applied = False
        if minimum_fee is not None:
            min_fee_decimal = Decimal(str(minimum_fee))
            if total_fee < min_fee_decimal:
                total_fee = min_fee_decimal
                min_applied = True

        result = self._build_fee_result(
            aum_decimal,
            total_fee,
            tier_breakdown,
            period,
            prorated,
            proration_days,
            min_applied,
            minimum_fee,
        )

        logger.info(
            "Tiered fee calculated",
            service=self.SERVICE_NAME,
            aum=float(aum_decimal),
            total_fee=result["total_fee"],
            effective_rate=result["effective_rate_percentage"],
            log_event="tiered_fee_calculated",
        )
        self._track_usage()
        return result

    def _validate_fee_args(
        self, args: dict[str, Any]
    ) -> tuple[Any, list[dict[str, Any]], str, int | None, float | None]:
        """Validate and extract fee calculation arguments."""
        aum = args.get("aum")
        if aum is None:
            raise ValidationError("aum", "Assets under management required")

        tiers = args.get("tiers")
        if not tiers or not isinstance(tiers, list):
            raise ValidationError("tiers", "Fee tiers required")

        period = args.get("period", "annual")
        proration_days = args.get("proration_days")
        minimum_fee = args.get("minimum_fee")

        return aum, tiers, period, proration_days, minimum_fee

    def _calculate_tiers(
        self, aum_decimal: Decimal, tiers: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], Decimal]:
        """Calculate fee for each tier."""
        sorted_tiers = sorted(
            tiers,
            key=lambda t: (
                Decimal("999999999999999")
                if t.get("threshold") is None
                else Decimal(str(t.get("threshold", 0)))
            ),
        )

        tier_breakdown = []
        total_fee = Decimal("0")
        remaining_aum = aum_decimal
        prev_threshold = Decimal("0")

        for tier in sorted_tiers:
            threshold = tier.get("threshold")
            rate = Decimal(str(tier.get("rate", 0)))

            # Capture tier_start before updating prev_threshold
            tier_start = prev_threshold

            if threshold is None:
                tier_aum = remaining_aum
            else:
                threshold_decimal = Decimal(str(threshold))
                tier_aum = min(remaining_aum, threshold_decimal - prev_threshold)
                prev_threshold = threshold_decimal

            if tier_aum <= 0:
                continue

            tier_fee = tier_aum * rate
            total_fee += tier_fee

            tier_breakdown.append(
                {
                    "tier_start": float(tier_start),
                    "tier_end": float(threshold) if threshold else None,
                    "tier_aum": float(tier_aum.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                    "rate": float(rate),
                    "rate_percentage": float(rate * 100),
                    "tier_fee": float(tier_fee.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                }
            )

            remaining_aum -= tier_aum
            if remaining_aum <= 0:
                break

        return tier_breakdown, total_fee

    def _apply_period_proration(
        self, total_fee: Decimal, period: str, proration_days: int | None
    ) -> tuple[Decimal, bool]:
        """Apply period and proration adjustments to fee."""
        period_multiplier = PERIOD_MULTIPLIERS.get(period, Decimal("1"))
        total_fee = total_fee * period_multiplier

        prorated = False
        if proration_days is not None:
            period_day_count = PERIOD_DAYS.get(period, 365)
            proration_factor = Decimal(str(proration_days)) / Decimal(str(period_day_count))
            total_fee = total_fee * proration_factor
            prorated = True

        return total_fee, prorated

    def _build_fee_result(
        self,
        aum_decimal: Decimal,
        total_fee: Decimal,
        tier_breakdown: list[dict[str, Any]],
        period: str,
        prorated: bool,
        proration_days: int | None,
        min_applied: bool,
        minimum_fee: float | None,
    ) -> dict[str, Any]:
        """Build the fee calculation result."""
        effective_rate = total_fee / aum_decimal if aum_decimal > 0 else Decimal("0")
        period_multiplier = PERIOD_MULTIPLIERS.get(period, Decimal("1"))
        annualized = effective_rate / period_multiplier

        if prorated and proration_days:
            period_day_count = PERIOD_DAYS.get(period, 365)
            annualized = annualized * Decimal(str(period_day_count)) / Decimal(str(proration_days))

        return {
            "total_fee": float(total_fee.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "tier_breakdown": tier_breakdown,
            "effective_rate": float(effective_rate.quantize(Decimal("0.000001"), ROUND_HALF_UP)),
            "effective_rate_percentage": float(
                (effective_rate * 100).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            ),
            "annualized_effective_rate": float(
                annualized.quantize(Decimal("0.000001"), ROUND_HALF_UP)
            ),
            "annualized_effective_rate_percentage": float(
                (annualized * 100).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            ),
            "aum": float(aum_decimal),
            "period": period,
            "prorated": prorated,
            "proration_days": proration_days,
            "minimum_fee_applied": min_applied,
            "status": "success",
        }

    def calculate_client_fees(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate fees for multiple clients with optional proration."""
        self._ensure_initialized()

        clients = args.get("clients")
        if not clients or not isinstance(clients, list):
            raise ValidationError("clients", "List of clients required")

        tiers = args.get("tiers")
        if not tiers:
            raise ValidationError("tiers", "Fee tiers required")

        period = args.get("period", "annual")
        as_of_date_str = args.get("as_of_date")
        as_of_date = datetime.fromisoformat(as_of_date_str) if as_of_date_str else datetime.now()

        client_fees, total_aum, total_fees = self._calculate_all_client_fees(
            org_id, user_id, clients, tiers, period, as_of_date
        )

        summary = self._build_client_fees_summary(client_fees, total_aum, total_fees)

        logger.info(
            "Client fees calculated",
            service=self.SERVICE_NAME,
            client_count=len(clients),
            total_fees=summary["total_fees"],
            log_event="client_fees_calculated",
        )
        self._track_usage()

        return {
            "client_fees": client_fees,
            "summary": summary,
            "period": period,
            "as_of_date": as_of_date.isoformat(),
            "status": "success",
        }

    def _calculate_all_client_fees(
        self,
        org_id: str,
        user_id: str,
        clients: list[dict[str, Any]],
        tiers: list[dict[str, Any]],
        period: str,
        as_of_date: datetime,
    ) -> tuple[list[dict[str, Any]], Decimal, Decimal]:
        """Calculate fees for all clients."""
        client_fees: list[dict[str, Any]] = []
        total_aum = Decimal("0")
        total_fees = Decimal("0")

        for client in clients:
            fee_data = self._calculate_single_client_fee(
                org_id, user_id, client, tiers, period, as_of_date
            )
            client_fees.append(fee_data)
            total_aum += Decimal(str(fee_data["aum"]))
            total_fees += Decimal(str(fee_data["fee"]))

        return client_fees, total_aum, total_fees

    def _calculate_single_client_fee(
        self,
        org_id: str,
        user_id: str,
        client: dict[str, Any],
        tiers: list[dict[str, Any]],
        period: str,
        as_of_date: datetime,
    ) -> dict[str, Any]:
        """Calculate fee for a single client."""
        client_id = client.get("id", "")
        client_name = client.get("name", "")
        client_aum = client.get("aum", 0)
        inception_str = client.get("inception_date")

        proration_days = None
        if inception_str:
            inception_date = datetime.fromisoformat(inception_str)
            days_in_period = (as_of_date - inception_date).days
            period_day_count = PERIOD_DAYS.get(period, 365)
            if 0 < days_in_period < period_day_count:
                proration_days = days_in_period

        fee_result = self.calculate_tiered_fee(
            org_id,
            user_id,
            {"aum": client_aum, "tiers": tiers, "period": period, "proration_days": proration_days},
        )

        return {
            "id": client_id,
            "name": client_name,
            "aum": client_aum,
            "fee": fee_result["total_fee"],
            "effective_rate_percentage": fee_result["effective_rate_percentage"],
            "prorated": fee_result["prorated"],
            "proration_days": proration_days,
        }

    def _build_client_fees_summary(
        self, client_fees: list[dict[str, Any]], total_aum: Decimal, total_fees: Decimal
    ) -> dict[str, Any]:
        """Build summary for client fees calculation."""
        aggregate_rate = total_fees / total_aum if total_aum > 0 else Decimal("0")

        return {
            "client_count": len(client_fees),
            "total_aum": float(total_aum.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "total_fees": float(total_fees.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "aggregate_effective_rate_percentage": float(
                (aggregate_rate * 100).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            ),
            "prorated_client_count": sum(1 for c in client_fees if c.get("prorated", False)),
        }
