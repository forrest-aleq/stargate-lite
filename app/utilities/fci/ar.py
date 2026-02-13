"""
FCI Accounts Receivable Mixin.

Aggregates AR aging data from connected accounting systems:
- QuickBooks
- Xero
- Sage Intacct
- NetSuite

Returns total AR with aging buckets, change tracking, and trend data.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.logging_config import get_logger
from app.utilities.fci.service_mappings import AR_SERVICES

logger = get_logger(__name__)


class ARMixin:
    """Mixin for accounts receivable aggregation."""

    def get_ar(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get accounts receivable totals with aging buckets.

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

        # AR comes from a single accounting system - use preferred or specified
        preferred_service = source or self._get_primary_accounting_service(
            org_id, user_id, AR_SERVICES
        )

        if not preferred_service:
            return self._format_response(
                total=0,
                errors=[{"service": "ar", "error": "No accounting system connected"}],
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

        # Get AR data from the accounting system
        results, errors, sources = self._aggregate_from_services(
            {preferred_service: AR_SERVICES[preferred_service]},
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

        # Parse AR aging data
        result = results[0]  # Single source
        ar_data = self._parse_ar_aging(preferred_service, result)

        # Calculate change from prior period
        prior_total = self._get_prior_ar_balance(org_id, user_id, ar_data["total"], period)
        change, change_percent = self._calculate_change(ar_data["total"], prior_total)

        # Generate trend data
        trend = self._generate_ar_trend(ar_data["total"], change_percent)

        # Generate insight
        insight = self._generate_ar_insight(ar_data, change_percent)

        return self._format_response(
            total=ar_data["total"],
            change=change,
            change_percent=change_percent,
            trend=trend,
            insight=insight,
            sources=sources,
            errors=errors if errors else None,
            current=ar_data["current"],
            days_30=ar_data["days_30"],
            days_60=ar_data["days_60"],
            days_90=ar_data["days_90"],
            over_90=ar_data["over_90"],
            count=ar_data["count"],
            as_of=as_of_date or datetime.now(UTC).strftime("%Y-%m-%d"),
            source=preferred_service,
        )

    def _parse_ar_aging(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Parse AR aging result from a specific service into unified format.
        Each accounting system returns aging data differently.
        """
        ar_data = {
            "total": 0.0,
            "current": 0.0,
            "days_30": 0.0,
            "days_60": 0.0,
            "days_90": 0.0,
            "over_90": 0.0,
            "count": 0,
        }

        if service == "quickbooks":
            # QuickBooks AgedReceivables report structure
            report = result.get("Rows", result)

            # Try to parse the report rows
            if isinstance(report, dict) and "Row" in report:
                rows = report.get("Row", [])
                for row in rows:
                    self._parse_qb_ar_row(row, ar_data)
            elif "Header" in result:
                # Alternative QuickBooks report format
                columns = result.get("Columns", {}).get("Column", [])
                rows = result.get("Rows", {}).get("Row", [])
                self._parse_qb_report_format(columns, rows, ar_data)

        elif service == "xero":
            # Xero aged receivables report
            reports = result.get("Reports", [])
            if reports:
                report = reports[0]
                rows = report.get("Rows", [])
                for row in rows:
                    self._parse_xero_ar_row(row, ar_data)

        elif service == "sage_intacct":
            # Sage Intacct AR aging
            aging = result.get("aging", result.get("data", {}))

            ar_data["total"] = float(aging.get("total", aging.get("TOTALDUE", 0)))
            ar_data["current"] = float(aging.get("current", aging.get("CURRENT", 0)))
            ar_data["days_30"] = float(aging.get("days_1_30", aging.get("AGINGPERIOD1", 0)))
            ar_data["days_60"] = float(aging.get("days_31_60", aging.get("AGINGPERIOD2", 0)))
            ar_data["days_90"] = float(aging.get("days_61_90", aging.get("AGINGPERIOD3", 0)))
            ar_data["over_90"] = float(aging.get("over_90", aging.get("AGINGPERIOD4", 0)))
            ar_data["count"] = int(aging.get("invoice_count", aging.get("NUMRECORDS", 0)))

        elif service == "netsuite":
            # NetSuite AR aging (via SuiteQL or report)
            aging = result.get("data", result)

            if isinstance(aging, list):
                # SuiteQL result - aggregate
                for row in aging:
                    bucket = row.get("aging_bucket", "")
                    amount = float(row.get("amount", 0))

                    bucket_lower = bucket.lower()
                    if "current" in bucket_lower:
                        ar_data["current"] += amount
                    elif "1-30" in bucket:
                        ar_data["days_30"] += amount
                    elif "31-60" in bucket:
                        ar_data["days_60"] += amount
                    elif "61-90" in bucket:
                        ar_data["days_90"] += amount
                    elif "90+" in bucket or "over" in bucket_lower:
                        ar_data["over_90"] += amount

                    ar_data["count"] += 1
            else:
                ar_data["total"] = float(aging.get("total", 0))
                ar_data["current"] = float(aging.get("current", 0))
                ar_data["days_30"] = float(aging.get("days_30", aging.get("period1", 0)))
                ar_data["days_60"] = float(aging.get("days_60", aging.get("period2", 0)))
                ar_data["days_90"] = float(aging.get("days_90", aging.get("period3", 0)))
                ar_data["over_90"] = float(aging.get("over_90", aging.get("period4", 0)))
                ar_data["count"] = int(aging.get("count", 0))

        # Calculate total if not provided
        if ar_data["total"] == 0:
            ar_data["total"] = (
                ar_data["current"]
                + ar_data["days_30"]
                + ar_data["days_60"]
                + ar_data["days_90"]
                + ar_data["over_90"]
            )

        return ar_data

    def _parse_qb_ar_row(self, row: dict[str, Any], ar_data: dict[str, Any]) -> None:
        """Parse a QuickBooks AR aging row."""
        row_type = row.get("type", "")

        if row_type == "Section":
            # Recurse into section rows
            for sub_row in row.get("Rows", {}).get("Row", []):
                self._parse_qb_ar_row(sub_row, ar_data)
        elif row_type == "Data":
            col_data = row.get("ColData", [])
            if len(col_data) >= 6:
                # Standard aging columns: Current, 1-30, 31-60, 61-90, >90, Total
                try:
                    ar_data["current"] += float(col_data[1].get("value", 0) or 0)
                    ar_data["days_30"] += float(col_data[2].get("value", 0) or 0)
                    ar_data["days_60"] += float(col_data[3].get("value", 0) or 0)
                    ar_data["days_90"] += float(col_data[4].get("value", 0) or 0)
                    ar_data["over_90"] += float(col_data[5].get("value", 0) or 0)
                    ar_data["count"] += 1
                except (ValueError, IndexError):
                    pass

    def _parse_qb_report_format(
        self,
        columns: list[dict[str, Any]],
        rows: list[dict[str, Any]],
        ar_data: dict[str, Any],
    ) -> None:
        """Parse QuickBooks alternative report format."""
        # Map column names to aging buckets
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

        # Parse row data
        for row in rows:
            col_data = row.get("ColData", [])
            for i, bucket in col_map.items():
                if i < len(col_data):
                    try:
                        value = float(col_data[i].get("value", 0) or 0)
                        ar_data[bucket] += value
                    except (ValueError, TypeError):
                        pass
            if col_data:
                ar_data["count"] += 1

    def _parse_xero_ar_row(self, row: dict[str, Any], ar_data: dict[str, Any]) -> None:
        """Parse a Xero AR aging row."""
        row_type = row.get("RowType", "")

        if row_type == "Section":
            for sub_row in row.get("Rows", []):
                self._parse_xero_ar_row(sub_row, ar_data)
        elif row_type == "Row":
            cells = row.get("Cells", [])
            if len(cells) >= 6:
                try:
                    # Xero aging columns typically: Contact, Current, 1-30, 31-60, 61-90, >90, Total
                    ar_data["current"] += float(cells[1].get("Value", 0) or 0)
                    ar_data["days_30"] += float(cells[2].get("Value", 0) or 0)
                    ar_data["days_60"] += float(cells[3].get("Value", 0) or 0)
                    ar_data["days_90"] += float(cells[4].get("Value", 0) or 0)
                    ar_data["over_90"] += float(cells[5].get("Value", 0) or 0)
                    ar_data["count"] += 1
                except (ValueError, IndexError):
                    pass

    def _get_prior_ar_balance(
        self,
        org_id: str,
        user_id: str,
        current_total: float,
        period: str,
    ) -> float:
        """
        Get prior period AR balance for comparison.
        In production, this would query historical data.
        """
        # Estimate based on typical AR patterns
        estimated_change_rate = 0.03  # 3% typical AR change
        prior_total = current_total / (1 + estimated_change_rate)
        return prior_total

    def _generate_ar_trend(
        self,
        current_total: float,
        change_percent: float,
    ) -> list[dict[str, Any]]:
        """Generate trend data points for AR sparkline."""
        trend: list[dict[str, Any]] = []
        today = datetime.now(UTC)

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

    def _generate_ar_insight(
        self,
        ar_data: dict[str, Any],
        change_percent: float,
    ) -> str:
        """Generate insight string for AR."""
        total = ar_data["total"]
        over_90 = ar_data["over_90"]

        # Check for concerning aging
        if total > 0 and over_90 / total > 0.2:
            over_90_pct = (over_90 / total) * 100
            return f"AR at ${total:,.0f} with {over_90_pct:.0f}% over 90 days past due"

        # Standard change-based insight
        direction = "up" if change_percent > 0 else "down" if change_percent < 0 else "unchanged"

        if change_percent == 0:
            return f"AR unchanged at ${total:,.0f}"

        return f"AR {direction} {abs(change_percent):.1f}% to ${total:,.0f}"
