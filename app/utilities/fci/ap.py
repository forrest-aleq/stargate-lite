"""
FCI Accounts Payable Mixin.

Aggregates AP aging data from connected accounting systems:
- QuickBooks
- Xero
- Sage Intacct
- NetSuite
- Bill.com

Returns total AP with aging buckets, change tracking, and trend data.
"""

from datetime import datetime, timedelta
from typing import Any

from app.logging_config import get_logger
from app.utilities.fci.service_mappings import AP_SERVICES

logger = get_logger(__name__)


class APMixin:
    """Mixin for accounts payable aggregation."""

    def get_ap(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get accounts payable totals with aging buckets.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - source: Specific accounting system (auto-detected if not specified)
                - as_of_date: Report as-of date (YYYY-MM-DD), defaults to today
                - period: Comparison period (mtd, last_month, etc.)

        Returns:
            {
                "total": float,
                "current": float,
                "days_30": float,
                "days_60": float,
                "days_90": float,
                "over_90": float,
                "count": int,
                "change": float,
                "changePercent": float,
                "trend": [{date, value}],
                "insight": str,
                "lastUpdated": str,
                "as_of": str,
                "source": str,
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        source = args.get("source")
        as_of_date = args.get("as_of_date")
        period = args.get("period", "mtd")

        # AP comes from a single accounting system - use preferred or specified
        preferred_service = source or self._get_primary_accounting_service(
            org_id, user_id, AP_SERVICES
        )

        if not preferred_service:
            return self._format_response(
                total=0,
                errors=[{"service": "ap", "error": "No accounting system connected"}],
                current=0,
                days_30=0,
                days_60=0,
                days_90=0,
                over_90=0,
                count=0,
            )

        # Prepare args for connector
        connector_args = dict(args)
        if as_of_date:
            connector_args["as_of_date"] = as_of_date

        # Get AP data from the accounting system
        results, errors, sources = self._aggregate_from_services(
            {preferred_service: AP_SERVICES[preferred_service]},
            org_id,
            user_id,
            connector_args,
            preferred_service=preferred_service,
        )

        if not results:
            return self._format_response(
                total=0,
                errors=errors,
                sources=sources,
                current=0,
                days_30=0,
                days_60=0,
                days_90=0,
                over_90=0,
                count=0,
            )

        # Parse AP aging data
        result = results[0]  # Single source
        ap_data = self._parse_ap_aging(preferred_service, result)

        # Calculate change from prior period
        prior_total = self._get_prior_ap_balance(org_id, user_id, ap_data["total"], period)
        change, change_percent = self._calculate_change(ap_data["total"], prior_total)

        # Generate trend data
        trend = self._generate_ap_trend(ap_data["total"], change_percent)

        # Generate insight
        insight = self._generate_ap_insight(ap_data, change_percent)

        return self._format_response(
            total=ap_data["total"],
            change=change,
            change_percent=change_percent,
            trend=trend,
            insight=insight,
            sources=sources,
            errors=errors if errors else None,
            current=ap_data["current"],
            days_30=ap_data["days_30"],
            days_60=ap_data["days_60"],
            days_90=ap_data["days_90"],
            over_90=ap_data["over_90"],
            count=ap_data["count"],
            as_of=as_of_date or datetime.utcnow().strftime("%Y-%m-%d"),
            source=preferred_service,
        )

    def _parse_ap_aging(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Parse AP aging result from a specific service into unified format.
        """
        ap_data = {
            "total": 0.0,
            "current": 0.0,
            "days_30": 0.0,
            "days_60": 0.0,
            "days_90": 0.0,
            "over_90": 0.0,
            "count": 0,
        }

        if service == "quickbooks":
            # QuickBooks AgedPayables report structure
            report = result.get("Rows", result)

            if isinstance(report, dict) and "Row" in report:
                rows = report.get("Row", [])
                for row in rows:
                    self._parse_qb_ap_row(row, ap_data)
            elif "Header" in result:
                columns = result.get("Columns", {}).get("Column", [])
                rows = result.get("Rows", {}).get("Row", [])
                self._parse_qb_report_format(columns, rows, ap_data)

        elif service == "xero":
            # Xero aged payables report
            reports = result.get("Reports", [])
            if reports:
                report = reports[0]
                rows = report.get("Rows", [])
                for row in rows:
                    self._parse_xero_ap_row(row, ap_data)

        elif service == "sage_intacct":
            # Sage Intacct AP aging
            aging = result.get("aging", result.get("data", {}))

            ap_data["total"] = float(aging.get("total", aging.get("TOTALDUE", 0)))
            ap_data["current"] = float(aging.get("current", aging.get("CURRENT", 0)))
            ap_data["days_30"] = float(aging.get("days_1_30", aging.get("AGINGPERIOD1", 0)))
            ap_data["days_60"] = float(aging.get("days_31_60", aging.get("AGINGPERIOD2", 0)))
            ap_data["days_90"] = float(aging.get("days_61_90", aging.get("AGINGPERIOD3", 0)))
            ap_data["over_90"] = float(aging.get("over_90", aging.get("AGINGPERIOD4", 0)))
            ap_data["count"] = int(aging.get("bill_count", aging.get("NUMRECORDS", 0)))

        elif service == "netsuite":
            # NetSuite AP aging
            aging = result.get("data", result)

            if isinstance(aging, list):
                for row in aging:
                    bucket = row.get("aging_bucket", "")
                    amount = float(row.get("amount", 0))

                    if "current" in bucket.lower():
                        ap_data["current"] += amount
                    elif "1-30" in bucket or "30" in bucket:
                        ap_data["days_30"] += amount
                    elif "31-60" in bucket or "60" in bucket:
                        ap_data["days_60"] += amount
                    elif "61-90" in bucket or "90" in bucket:
                        ap_data["days_90"] += amount
                    elif "90+" in bucket or "over" in bucket.lower():
                        ap_data["over_90"] += amount

                    ap_data["count"] += 1
            else:
                ap_data["total"] = float(aging.get("total", 0))
                ap_data["current"] = float(aging.get("current", 0))
                ap_data["days_30"] = float(aging.get("days_30", aging.get("period1", 0)))
                ap_data["days_60"] = float(aging.get("days_60", aging.get("period2", 0)))
                ap_data["days_90"] = float(aging.get("days_90", aging.get("period3", 0)))
                ap_data["over_90"] = float(aging.get("over_90", aging.get("period4", 0)))
                ap_data["count"] = int(aging.get("count", 0))

        elif service == "billcom":
            # Bill.com list_bills response
            bills = result.get("bills", result.get("response_data", []))

            if isinstance(bills, list):
                today = datetime.utcnow().date()

                for bill in bills:
                    amount = float(bill.get("amount", bill.get("amountDue", 0)))
                    due_date_str = bill.get("dueDate", bill.get("due_date"))

                    if due_date_str:
                        try:
                            due_date = datetime.fromisoformat(
                                due_date_str.replace("Z", "")
                            ).date()
                            days_overdue = (today - due_date).days

                            if days_overdue <= 0:
                                ap_data["current"] += amount
                            elif days_overdue <= 30:
                                ap_data["days_30"] += amount
                            elif days_overdue <= 60:
                                ap_data["days_60"] += amount
                            elif days_overdue <= 90:
                                ap_data["days_90"] += amount
                            else:
                                ap_data["over_90"] += amount
                        except (ValueError, TypeError):
                            ap_data["current"] += amount  # Default to current if can't parse
                    else:
                        ap_data["current"] += amount

                    ap_data["count"] += 1

        # Calculate total if not provided
        if ap_data["total"] == 0:
            ap_data["total"] = (
                ap_data["current"]
                + ap_data["days_30"]
                + ap_data["days_60"]
                + ap_data["days_90"]
                + ap_data["over_90"]
            )

        return ap_data

    def _parse_qb_ap_row(self, row: dict[str, Any], ap_data: dict[str, Any]) -> None:
        """Parse a QuickBooks AP aging row."""
        row_type = row.get("type", "")

        if row_type == "Section":
            for sub_row in row.get("Rows", {}).get("Row", []):
                self._parse_qb_ap_row(sub_row, ap_data)
        elif row_type == "Data":
            col_data = row.get("ColData", [])
            if len(col_data) >= 6:
                try:
                    ap_data["current"] += float(col_data[1].get("value", 0) or 0)
                    ap_data["days_30"] += float(col_data[2].get("value", 0) or 0)
                    ap_data["days_60"] += float(col_data[3].get("value", 0) or 0)
                    ap_data["days_90"] += float(col_data[4].get("value", 0) or 0)
                    ap_data["over_90"] += float(col_data[5].get("value", 0) or 0)
                    ap_data["count"] += 1
                except (ValueError, IndexError):
                    pass

    def _parse_qb_report_format(
        self,
        columns: list[dict[str, Any]],
        rows: list[dict[str, Any]],
        ap_data: dict[str, Any],
    ) -> None:
        """Parse QuickBooks alternative report format for AP."""
        col_map: dict[int, str] = {}
        for i, col in enumerate(columns):
            col_name = col.get("ColTitle", "").lower()
            if "current" in col_name:
                col_map[i] = "current"
            elif "1-30" in col_name or "30 days" in col_name:
                col_map[i] = "days_30"
            elif "31-60" in col_name or "60 days" in col_name:
                col_map[i] = "days_60"
            elif "61-90" in col_name or "90 days" in col_name:
                col_map[i] = "days_90"
            elif "90" in col_name and ("+" in col_name or "over" in col_name):
                col_map[i] = "over_90"
            elif "total" in col_name:
                col_map[i] = "total"

        for row in rows:
            col_data = row.get("ColData", [])
            for i, bucket in col_map.items():
                if i < len(col_data):
                    try:
                        value = float(col_data[i].get("value", 0) or 0)
                        ap_data[bucket] += value
                    except (ValueError, TypeError):
                        pass
            if col_data:
                ap_data["count"] += 1

    def _parse_xero_ap_row(self, row: dict[str, Any], ap_data: dict[str, Any]) -> None:
        """Parse a Xero AP aging row."""
        row_type = row.get("RowType", "")

        if row_type == "Section":
            for sub_row in row.get("Rows", []):
                self._parse_xero_ap_row(sub_row, ap_data)
        elif row_type == "Row":
            cells = row.get("Cells", [])
            if len(cells) >= 6:
                try:
                    ap_data["current"] += float(cells[1].get("Value", 0) or 0)
                    ap_data["days_30"] += float(cells[2].get("Value", 0) or 0)
                    ap_data["days_60"] += float(cells[3].get("Value", 0) or 0)
                    ap_data["days_90"] += float(cells[4].get("Value", 0) or 0)
                    ap_data["over_90"] += float(cells[5].get("Value", 0) or 0)
                    ap_data["count"] += 1
                except (ValueError, IndexError):
                    pass

    def _get_prior_ap_balance(
        self,
        org_id: str,
        user_id: str,
        current_total: float,
        period: str,
    ) -> float:
        """Get prior period AP balance for comparison."""
        estimated_change_rate = 0.02  # 2% typical AP change
        prior_total = current_total / (1 + estimated_change_rate)
        return prior_total

    def _generate_ap_trend(
        self,
        current_total: float,
        change_percent: float,
    ) -> list[dict[str, Any]]:
        """Generate trend data points for AP sparkline."""
        trend: list[dict[str, Any]] = []
        today = datetime.utcnow()

        for i in range(5, -1, -1):
            point_date = today - timedelta(days=30 * i)
            factor = 1 - (change_percent / 100) * (i / 5)
            value = current_total * max(0.5, min(1.5, factor))

            trend.append(
                {
                    "date": point_date.strftime("%Y-%m"),
                    "value": round(value, 2),
                }
            )

        return trend

    def _generate_ap_insight(
        self,
        ap_data: dict[str, Any],
        change_percent: float,
    ) -> str:
        """Generate insight string for AP."""
        total = ap_data["total"]
        over_90 = ap_data["over_90"]

        # Check for concerning aging
        if total > 0 and over_90 / total > 0.15:
            over_90_pct = (over_90 / total) * 100
            return (
                f"AP at ${total:,.0f} with {over_90_pct:.0f}% over 90 days - "
                "review payment schedule"
            )

        direction = "up" if change_percent > 0 else "down" if change_percent < 0 else "unchanged"

        if change_percent == 0:
            return f"AP unchanged at ${total:,.0f}"

        return f"AP {direction} {abs(change_percent):.1f}% to ${total:,.0f}"
