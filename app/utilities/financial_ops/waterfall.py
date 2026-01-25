"""
Investor Waterfall Calculator for Financial Operations utility.

Calculates distribution waterfalls for real estate funds:
- Return of capital
- Preferred return (with compounding options)
- GP catch-up
- Carried interest split
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .covenants import CovenantsMixin

logger = get_logger(__name__)


@dataclass
class Investor:
    """Investor in a fund."""

    id: str
    name: str
    capital_contribution: Decimal
    ownership_percentage: Decimal
    is_gp: bool = False


class WaterfallMixin(CovenantsMixin):
    """Mixin providing waterfall distribution calculations."""

    def calculate_waterfall(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate investor distribution waterfall."""
        self._ensure_initialized()

        params = self._validate_waterfall_args(args)
        investors, gp_investor, lp_capital = self._parse_investors(params["investors_data"])

        distributions = self._init_distributions(investors)
        waterfall_tiers = self._init_waterfall_tiers()

        remaining = self._distribute_tiers(
            params, investors, gp_investor, lp_capital, distributions, waterfall_tiers
        )

        result = self._build_waterfall_result(
            params, investors, gp_investor, distributions, waterfall_tiers, remaining
        )

        logger.info(
            "Waterfall distribution calculated",
            service=self.SERVICE_NAME,
            distributable=float(params["cash"]),
            investors=len(investors),
            gp_share=result["summary"]["effective_gp_share"],
            log_event="waterfall_calculated",
        )
        self._track_usage()
        return result

    def _validate_waterfall_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate and extract waterfall arguments."""
        distributable_cash = args.get("distributable_cash")
        if distributable_cash is None:
            raise ValidationError("distributable_cash", "Distributable cash required")

        investors_data = args.get("investors")
        if not investors_data or not isinstance(investors_data, list):
            raise ValidationError("investors", "List of investors required")

        carried_interest = Decimal(str(args.get("carried_interest", 0.20)))
        if carried_interest >= 1:
            raise ValidationError(
                "carried_interest", "Carried interest must be less than 100% (1.0)"
            )
        if carried_interest < 0:
            raise ValidationError("carried_interest", "Carried interest cannot be negative")

        return {
            "cash": Decimal(str(distributable_cash)),
            "investors_data": investors_data,
            "pref_return": Decimal(str(args.get("preferred_return", 0.08))),
            "catch_up_rate": Decimal(str(args.get("catch_up_rate", 1.0))),
            "carried_interest": carried_interest,
            "compounding": args.get("compounding", "simple"),
            "holding_years": Decimal(str(args.get("holding_period_years", 1.0))),
        }

    def _parse_investors(
        self, investors_data: list[dict[str, Any]]
    ) -> tuple[list[Investor], Investor, Decimal]:
        """Parse investor data into Investor objects."""
        investors: list[Investor] = []
        gp_investor = None
        lp_capital = Decimal("0")

        for inv_data in investors_data:
            inv = Investor(
                id=inv_data.get("id", ""),
                name=inv_data.get("name", ""),
                capital_contribution=Decimal(str(inv_data.get("capital_contribution", 0))),
                ownership_percentage=Decimal(str(inv_data.get("ownership_percentage", 0))),
                is_gp=inv_data.get("is_gp", False),
            )
            investors.append(inv)
            if inv.is_gp:
                gp_investor = inv
            else:
                lp_capital += inv.capital_contribution

        if not gp_investor:
            gp_investor = Investor(
                id="gp",
                name="General Partner",
                capital_contribution=Decimal("0"),
                ownership_percentage=Decimal("0.20"),
                is_gp=True,
            )
            investors.append(gp_investor)

        return investors, gp_investor, lp_capital

    def _init_distributions(self, investors: list[Investor]) -> dict[str, dict[str, Any]]:
        """Initialize distribution tracking for all investors."""
        return {
            inv.id: {
                "id": inv.id,
                "name": inv.name,
                "capital_contribution": float(inv.capital_contribution),
                "return_of_capital": Decimal("0"),
                "preferred_return": Decimal("0"),
                "catch_up": Decimal("0"),
                "carried_interest": Decimal("0"),
                "total_distribution": Decimal("0"),
            }
            for inv in investors
        }

    def _init_waterfall_tiers(self) -> dict[str, Decimal]:
        """Initialize waterfall tier tracking."""
        return {
            "return_of_capital": Decimal("0"),
            "preferred_return": Decimal("0"),
            "gp_catch_up": Decimal("0"),
            "carried_interest_lp": Decimal("0"),
            "carried_interest_gp": Decimal("0"),
        }

    def _distribute_tiers(
        self,
        params: dict[str, Any],
        investors: list[Investor],
        gp_investor: Investor,
        lp_capital: Decimal,
        distributions: dict[str, dict[str, Any]],
        waterfall_tiers: dict[str, Decimal],
    ) -> Decimal:
        """Distribute cash through all waterfall tiers."""
        remaining = params["cash"]
        lp_investors = [inv for inv in investors if not inv.is_gp]

        # Tier 1: Return of Capital
        remaining = self._distribute_roc(
            lp_investors, gp_investor, remaining, distributions, waterfall_tiers
        )

        # Tier 2: Preferred Return
        remaining = self._distribute_preferred(
            lp_investors, remaining, distributions, waterfall_tiers, params
        )

        # Tier 3: GP Catch-up
        remaining = self._distribute_catchup(
            gp_investor, remaining, distributions, waterfall_tiers, params
        )

        # Tier 4: Carried Interest Split
        remaining = self._distribute_carry(
            lp_investors, gp_investor, lp_capital, remaining, distributions, waterfall_tiers, params
        )

        return remaining

    def _distribute_roc(
        self,
        lp_investors: list[Investor],
        gp_investor: Investor,
        remaining: Decimal,
        distributions: dict[str, dict[str, Any]],
        waterfall_tiers: dict[str, Decimal],
    ) -> Decimal:
        """Tier 1: Return of Capital."""
        for inv in lp_investors:
            if remaining <= 0:
                break
            roc_amount = min(inv.capital_contribution, remaining)
            distributions[inv.id]["return_of_capital"] = roc_amount
            distributions[inv.id]["total_distribution"] += roc_amount
            waterfall_tiers["return_of_capital"] += roc_amount
            remaining -= roc_amount

        if gp_investor.capital_contribution > 0 and remaining > 0:
            gp_roc = min(gp_investor.capital_contribution, remaining)
            distributions[gp_investor.id]["return_of_capital"] = gp_roc
            distributions[gp_investor.id]["total_distribution"] += gp_roc
            waterfall_tiers["return_of_capital"] += gp_roc
            remaining -= gp_roc

        return remaining

    def _distribute_preferred(
        self,
        lp_investors: list[Investor],
        remaining: Decimal,
        distributions: dict[str, dict[str, Any]],
        waterfall_tiers: dict[str, Decimal],
        params: dict[str, Any],
    ) -> Decimal:
        """Tier 2: Preferred Return."""
        for inv in lp_investors:
            if remaining <= 0:
                break
            pref_owed = self._calc_preferred_owed(inv, params)
            pref_amount = min(pref_owed, remaining)
            distributions[inv.id]["preferred_return"] = pref_amount
            distributions[inv.id]["total_distribution"] += pref_amount
            waterfall_tiers["preferred_return"] += pref_amount
            remaining -= pref_amount
        return remaining

    def _calc_preferred_owed(self, inv: Investor, params: dict[str, Any]) -> Decimal:
        """Calculate preferred return owed to an investor."""
        if params["compounding"] == "compound":
            return Decimal(
                inv.capital_contribution
                * ((1 + params["pref_return"]) ** params["holding_years"] - 1)
            )
        # Default to simple interest for "simple" or any other value
        return Decimal(inv.capital_contribution * params["pref_return"] * params["holding_years"])

    def _distribute_catchup(
        self,
        gp_investor: Investor,
        remaining: Decimal,
        distributions: dict[str, dict[str, Any]],
        waterfall_tiers: dict[str, Decimal],
        params: dict[str, Any],
    ) -> Decimal:
        """Tier 3: GP Catch-up."""
        if remaining <= 0:
            return remaining

        total_lp_profit = waterfall_tiers["preferred_return"]
        carried = params["carried_interest"]
        target_gp_profit = total_lp_profit * carried / (1 - carried)
        catch_up_amount = min(target_gp_profit * params["catch_up_rate"], remaining)

        distributions[gp_investor.id]["catch_up"] = catch_up_amount
        distributions[gp_investor.id]["total_distribution"] += catch_up_amount
        waterfall_tiers["gp_catch_up"] = catch_up_amount
        return Decimal(remaining - catch_up_amount)

    def _distribute_carry(
        self,
        lp_investors: list[Investor],
        gp_investor: Investor,
        lp_capital: Decimal,
        remaining: Decimal,
        distributions: dict[str, dict[str, Any]],
        waterfall_tiers: dict[str, Decimal],
        params: dict[str, Any],
    ) -> Decimal:
        """Tier 4: Carried Interest Split."""
        if remaining <= 0:
            return remaining

        carried = params["carried_interest"]
        lp_share = remaining * (1 - carried)
        gp_share = remaining * carried

        for inv in lp_investors:
            if lp_capital > 0:
                inv_share = lp_share * (inv.capital_contribution / lp_capital)
                distributions[inv.id]["carried_interest"] = inv_share
                distributions[inv.id]["total_distribution"] += inv_share
                waterfall_tiers["carried_interest_lp"] += inv_share

        distributions[gp_investor.id]["carried_interest"] = gp_share
        distributions[gp_investor.id]["total_distribution"] += gp_share
        waterfall_tiers["carried_interest_gp"] = gp_share

        return Decimal("0")

    def _build_waterfall_result(
        self,
        params: dict[str, Any],
        investors: list[Investor],
        gp_investor: Investor,
        distributions: dict[str, dict[str, Any]],
        waterfall_tiers: dict[str, Decimal],
        remaining: Decimal,
    ) -> dict[str, Any]:
        """Build the final waterfall result."""
        distribution_list = []
        total_lp = Decimal("0")
        total_gp = Decimal("0")

        for inv in investors:
            dist = distributions[inv.id]
            dist_output = self._format_distribution(dist, inv)
            distribution_list.append(dist_output)
            if inv.is_gp:
                total_gp += dist["total_distribution"]
            else:
                total_lp += dist["total_distribution"]

        cash = params["cash"]
        distributed = cash - remaining
        summary = {
            "distributable_cash": float(cash),
            "total_distributed": float(distributed.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "remaining_cash": float(remaining.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "total_lp_distributions": float(total_lp.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "total_gp_distributions": float(total_gp.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "effective_gp_share": (
                float((total_gp / distributed * 100).quantize(Decimal("0.1"), ROUND_HALF_UP))
                if distributed > 0
                else 0
            ),
            "investor_count": len(investors),
            "lp_count": len([i for i in investors if not i.is_gp]),
        }

        tiers_output = {
            k: float(v.quantize(Decimal("0.01"), ROUND_HALF_UP)) for k, v in waterfall_tiers.items()
        }

        return {
            "distributions": distribution_list,
            "waterfall_tiers": tiers_output,
            "gp_carry": float(total_gp.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "lp_returns": float(total_lp.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "summary": summary,
            "parameters": {
                "preferred_return": float(params["pref_return"]),
                "catch_up_rate": float(params["catch_up_rate"]),
                "carried_interest": float(params["carried_interest"]),
                "compounding": params["compounding"],
                "holding_period_years": float(params["holding_years"]),
            },
            "status": "success",
        }

    def _format_distribution(self, dist: dict[str, Any], inv: Investor) -> dict[str, Any]:
        """Format a single investor's distribution for output."""
        output = {
            "id": dist["id"],
            "name": dist["name"],
            "capital_contribution": dist["capital_contribution"],
            "return_of_capital": float(
                dist["return_of_capital"].quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
            "preferred_return": float(
                dist["preferred_return"].quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
            "catch_up": float(dist["catch_up"].quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "carried_interest": float(
                dist["carried_interest"].quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
            "total_distribution": float(
                dist["total_distribution"].quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
            "is_gp": inv.is_gp,
        }
        if inv.capital_contribution > 0:
            moic = dist["total_distribution"] / inv.capital_contribution
            output["moic"] = float(moic.quantize(Decimal("0.01"), ROUND_HALF_UP))
        else:
            output["moic"] = None
        return output
