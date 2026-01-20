"""
Cash Flow Forecasting for Financial Operations utility.

Provides 13-week cash flow forecasting:
- Rolling projection from historical data
- Seasonal adjustment
- Confidence intervals
- Scenario analysis (optimistic/pessimistic)
"""

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .tiered_fees import TieredFeesMixin

logger = get_logger(__name__)


class ForecastingMixin(TieredFeesMixin):
    """Mixin providing cash flow forecasting capabilities."""

    def forecast_cashflow(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Generate 13-week rolling cash flow forecast."""
        self._ensure_initialized()

        params = self._validate_forecast_args(args)
        parsed_history = self._parse_historical_data(params["historical_data"])
        stats = self._calculate_historical_stats(parsed_history)
        seasonal = self._calculate_seasonal_factors(parsed_history, stats, params)
        known_by_week = self._parse_known_items(params, parsed_history)

        forecast, alerts, tracking = self._generate_forecast(
            params, parsed_history, stats, seasonal, known_by_week
        )

        summary = self._build_forecast_summary(params, tracking)
        summary["alert_count"] = len(alerts)

        logger.info(
            "Cash flow forecast generated",
            service=self.SERVICE_NAME,
            forecast_weeks=params["forecast_weeks"],
            starting_balance=float(params["balance"]),
            ending_balance=summary["ending_balance_base"],
            alerts=len(alerts),
            log_event="forecast_generated",
        )
        self._track_usage()

        return {
            "forecast": forecast,
            "summary": summary,
            "alerts": alerts,
            "parameters": {
                "forecast_weeks": params["forecast_weeks"],
                "seasonal_adjustment": params["seasonal_adjustment"],
                "known_items_count": len(params["known_items"]),
            },
            "status": "success",
        }

    def _validate_forecast_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate and extract forecast arguments."""
        historical_data = args.get("historical_data")
        if not historical_data or not isinstance(historical_data, list):
            raise ValidationError("historical_data", "Historical cash flow data required")

        starting_balance = args.get("starting_balance")
        if starting_balance is None:
            raise ValidationError("starting_balance", "Starting balance required")

        return {
            "historical_data": historical_data,
            "balance": Decimal(str(starting_balance)),
            "forecast_weeks": int(args.get("forecast_weeks", 13)),
            "seasonal_adjustment": args.get("seasonal_adjustment", True),
            "known_items": args.get("known_items", []),
        }

    def _parse_historical_data(
        self, historical_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Parse and sort historical data."""
        parsed: list[dict[str, Any]] = []
        for item in historical_data:
            week_date = item.get("week_ending")
            if isinstance(week_date, str):
                week_date = datetime.fromisoformat(week_date.replace("Z", "+00:00"))
            parsed.append(
                {
                    "week_ending": week_date,
                    "inflows": Decimal(str(item.get("inflows", 0))),
                    "outflows": Decimal(str(item.get("outflows", 0))),
                    "net": Decimal(str(item.get("inflows", 0)))
                    - Decimal(str(item.get("outflows", 0))),
                }
            )
        parsed.sort(key=lambda x: x["week_ending"])

        if len(parsed) < 4:
            raise ValidationError("historical_data", "At least 4 weeks of historical data required")
        return parsed

    def _calculate_historical_stats(self, parsed_history: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate averages and standard deviations from history."""
        inflows = [float(h["inflows"]) for h in parsed_history]
        outflows = [float(h["outflows"]) for h in parsed_history]

        avg_in = Decimal(str(sum(inflows) / len(inflows)))
        avg_out = Decimal(str(sum(outflows) / len(outflows)))

        in_var = sum((x - float(avg_in)) ** 2 for x in inflows) / len(inflows)
        out_var = sum((x - float(avg_out)) ** 2 for x in outflows) / len(outflows)

        return {
            "avg_inflow": avg_in,
            "avg_outflow": avg_out,
            "inflow_std": Decimal(str(in_var**0.5)),
            "outflow_std": Decimal(str(out_var**0.5)),
        }

    def _calculate_seasonal_factors(
        self,
        parsed_history: list[dict[str, Any]],
        stats: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[int, dict[str, Decimal]]:
        """Calculate seasonal adjustment factors by week of month."""
        if not params["seasonal_adjustment"] or len(parsed_history) < 8:
            return {}

        week_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for h in parsed_history:
            week_of_month = (h["week_ending"].day - 1) // 7 + 1
            week_groups[week_of_month].append(h)

        factors = {}
        for week_num, items in week_groups.items():
            if items:
                week_avg_in = sum(i["inflows"] for i in items) / len(items)
                week_avg_out = sum(i["outflows"] for i in items) / len(items)
                factors[week_num] = {
                    "inflow_factor": week_avg_in / stats["avg_inflow"]
                    if stats["avg_inflow"] > 0
                    else Decimal("1"),
                    "outflow_factor": week_avg_out / stats["avg_outflow"]
                    if stats["avg_outflow"] > 0
                    else Decimal("1"),
                }
        return factors

    def _parse_known_items(
        self, params: dict[str, Any], parsed_history: list[dict[str, Any]]
    ) -> dict[int, Decimal]:
        """Parse known future items into weekly buckets."""
        known_by_week: dict[int, Decimal] = defaultdict(Decimal)
        if not params["known_items"]:
            return known_by_week

        last_historical = parsed_history[-1]["week_ending"]
        for item in params["known_items"]:
            item_date = item.get("date")
            if isinstance(item_date, str):
                item_date = datetime.fromisoformat(item_date.replace("Z", "+00:00"))
            amount = Decimal(str(item.get("amount", 0)))

            days_ahead = (item_date - last_historical).days
            week_num = max(1, (days_ahead // 7) + 1)

            if week_num <= params["forecast_weeks"]:
                known_by_week[week_num] += amount
                if item.get("recurring"):
                    for future_week in range(week_num + 1, params["forecast_weeks"] + 1):
                        known_by_week[future_week] += amount

        return known_by_week

    def _generate_forecast(
        self,
        params: dict[str, Any],
        parsed_history: list[dict[str, Any]],
        stats: dict[str, Any],
        seasonal: dict[int, dict[str, Decimal]],
        known_by_week: dict[int, Decimal],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """Generate the week-by-week forecast."""
        forecast: list[dict[str, Any]] = []
        alerts: list[dict[str, Any]] = []
        tracking = {
            "running_balance": params["balance"],
            "min_balance": params["balance"],
            "min_balance_week": 0,
            "cumulative_inflows": Decimal("0"),
            "cumulative_outflows": Decimal("0"),
        }

        last_date = parsed_history[-1]["week_ending"]

        for week in range(1, params["forecast_weeks"] + 1):
            week_data = self._forecast_single_week(
                week, last_date, stats, seasonal, known_by_week, tracking, params["balance"]
            )
            forecast.append(week_data["forecast"])
            alerts.extend(week_data["alerts"])

            tracking["running_balance"] = Decimal(
                str(week_data["forecast"]["ending_balance"]["base"])
            )
            tracking["cumulative_inflows"] += Decimal(
                str(week_data["forecast"]["projected_inflows"])
            )
            tracking["cumulative_outflows"] += Decimal(
                str(week_data["forecast"]["projected_outflows"])
            )

            if tracking["running_balance"] < tracking["min_balance"]:
                tracking["min_balance"] = tracking["running_balance"]
                tracking["min_balance_week"] = week

        return forecast, alerts, tracking

    def _forecast_single_week(
        self,
        week: int,
        last_date: datetime,
        stats: dict[str, Any],
        seasonal: dict[int, dict[str, Decimal]],
        known_by_week: dict[int, Decimal],
        tracking: dict[str, Any],
        starting_balance: Decimal,
    ) -> dict[str, Any]:
        """Generate forecast for a single week."""
        week_ending = last_date + timedelta(weeks=week)
        week_of_month = (week_ending.day - 1) // 7 + 1

        proj_in = stats["avg_inflow"]
        proj_out = stats["avg_outflow"]

        if week_of_month in seasonal:
            proj_in = stats["avg_inflow"] * seasonal[week_of_month]["inflow_factor"]
            proj_out = stats["avg_outflow"] * seasonal[week_of_month]["outflow_factor"]

        known = known_by_week.get(week, Decimal("0"))

        in_low = max(Decimal("0"), proj_in - stats["inflow_std"])
        in_high = proj_in + stats["inflow_std"]
        out_low = max(Decimal("0"), proj_out - stats["outflow_std"])
        out_high = proj_out + stats["outflow_std"]

        net_base = proj_in - proj_out + known
        net_opt = in_high - out_low + known
        net_pess = in_low - out_high + known

        running = tracking["running_balance"]
        end_base = running + net_base
        end_opt = running + net_opt
        end_pess = running + net_pess

        alerts = self._generate_week_alerts(week, week_ending, end_base, end_pess, starting_balance)

        return {
            "forecast": {
                "week": week,
                "week_ending": week_ending.strftime("%Y-%m-%d"),
                "projected_inflows": float(proj_in.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "projected_outflows": float(proj_out.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "known_items": float(known.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                "net_cash_flow": {
                    "base": float(net_base.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                    "optimistic": float(net_opt.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                    "pessimistic": float(net_pess.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                },
                "ending_balance": {
                    "base": float(end_base.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                    "optimistic": float(end_opt.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                    "pessimistic": float(end_pess.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                },
            },
            "alerts": alerts,
        }

    def _generate_week_alerts(
        self,
        week: int,
        week_ending: datetime,
        end_base: Decimal,
        end_pess: Decimal,
        starting_balance: Decimal,
    ) -> list[dict[str, Any]]:
        """Generate alerts for a forecast week."""
        alerts: list[dict[str, Any]] = []
        if end_pess < 0:
            alerts.append(
                {
                    "type": "negative_balance_risk",
                    "week": week,
                    "week_ending": week_ending.strftime("%Y-%m-%d"),
                    "pessimistic_balance": float(end_pess.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                    "severity": "high",
                }
            )
        elif end_base < starting_balance * Decimal("0.2"):
            alerts.append(
                {
                    "type": "low_balance_warning",
                    "week": week,
                    "week_ending": week_ending.strftime("%Y-%m-%d"),
                    "projected_balance": float(end_base.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                    "severity": "medium",
                }
            )
        return alerts

    def _build_forecast_summary(
        self, params: dict[str, Any], tracking: dict[str, Any]
    ) -> dict[str, Any]:
        """Build forecast summary statistics."""
        return {
            "starting_balance": float(params["balance"]),
            "ending_balance_base": float(
                tracking["running_balance"].quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
            "total_projected_inflows": float(
                tracking["cumulative_inflows"].quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
            "total_projected_outflows": float(
                tracking["cumulative_outflows"].quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
            "net_change": float(
                (tracking["running_balance"] - params["balance"]).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
            ),
            "minimum_balance": float(
                tracking["min_balance"].quantize(Decimal("0.01"), ROUND_HALF_UP)
            ),
            "minimum_balance_week": tracking["min_balance_week"],
            "forecast_weeks": params["forecast_weeks"],
            "historical_weeks_used": len(params["historical_data"]),
            "alert_count": 0,  # Will be updated by caller
        }

    def aggregate_bank_balances(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Aggregate balances across multiple bank accounts."""
        self._ensure_initialized()

        accounts = args.get("accounts")
        if not accounts or not isinstance(accounts, list):
            raise ValidationError("accounts", "List of accounts required")

        total_balance = Decimal("0")
        by_type: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
        by_currency: dict[str, Decimal] = defaultdict(Decimal)
        processed = []

        for acct in accounts:
            balance = Decimal(str(acct.get("balance", 0)))
            currency = acct.get("currency", "USD")
            acct_type = acct.get("type", "checking")

            processed.append(
                {
                    "id": acct.get("id", ""),
                    "name": acct.get("name", ""),
                    "balance": float(balance.quantize(Decimal("0.01"), ROUND_HALF_UP)),
                    "currency": currency,
                    "type": acct_type,
                }
            )

            if currency == "USD":
                total_balance += balance
            by_type[acct_type][currency] += balance
            by_currency[currency] += balance

        # Convert by_type to serializable format with per-currency totals
        by_type_output = {
            acct_type: {
                curr: float(amt.quantize(Decimal("0.01"), ROUND_HALF_UP))
                for curr, amt in currencies.items()
            }
            for acct_type, currencies in by_type.items()
        }

        summary = {
            "total_balance_usd": float(total_balance.quantize(Decimal("0.01"), ROUND_HALF_UP)),
            "account_count": len(accounts),
            "by_type": by_type_output,
            "by_currency": {
                k: float(v.quantize(Decimal("0.01"), ROUND_HALF_UP)) for k, v in by_currency.items()
            },
        }

        logger.info(
            "Bank balances aggregated",
            service=self.SERVICE_NAME,
            account_count=len(accounts),
            total_balance=summary["total_balance_usd"],
            log_event="balances_aggregated",
        )
        self._track_usage()

        return {
            "total_balance": summary["total_balance_usd"],
            "accounts": processed,
            "summary": summary,
            "status": "success",
        }
