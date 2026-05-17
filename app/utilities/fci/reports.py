"""
FCI Reports Mixin.

Provides standard financial reports:
- Profit & Loss (P&L)
- Balance Sheet
- AR Aging (detailed)
- AP Aging (detailed)
- Cash Flow Statement

These wrap existing connector methods with FCI-consistent response formatting.
"""

from datetime import UTC, datetime
from typing import Any

from app.logging_config import get_logger
from app.utilities.fci.service_mappings import (
    AP_SERVICES,
    AR_SERVICES,
    BALANCE_SHEET_SERVICES,
    CASHFLOW_SERVICES,
    PL_REPORT_SERVICES,
)

logger = get_logger(__name__)


class ReportsMixin:
    """Mixin for financial reports."""

    def get_profit_loss(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get Profit & Loss report.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - start_date: Start date (YYYY-MM-DD)
                - end_date: End date (YYYY-MM-DD)
                - summarize_by: "total", "month", "quarter", "year"
                - class_id: Filter by class/department
                - source: Accounting system (auto-detected if not specified)

        Returns:
            {
                "total_income": float,
                "total_expenses": float,
                "net_income": float,
                "gross_profit": float,
                "income_breakdown": [{category, amount}],
                "expense_breakdown": [{category, amount}],
                "period": {start, end},
                "source": str,
                "lastUpdated": str,
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        source = args.get("source")
        start_date = args.get("start_date")
        end_date = args.get("end_date")

        # Default dates if not provided
        if not start_date:
            today = datetime.now(UTC)
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now(UTC).strftime("%Y-%m-%d")

        # Get primary accounting system
        preferred_service = source or self._get_primary_accounting_service(
            org_id, user_id, PL_REPORT_SERVICES
        )

        if not preferred_service:
            return self._format_response(
                total=0,
                errors=[{"service": "profitloss", "error": "No accounting system connected"}],
                total_income=0,
                total_expenses=0,
                net_income=0,
            )

        # Call connector
        connector_args = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if args.get("class_id"):
            connector_args["class_id"] = args["class_id"]
        if args.get("summarize_by"):
            connector_args["summarize_by"] = args["summarize_by"]

        results, errors, sources = self._aggregate_from_services(
            {preferred_service: PL_REPORT_SERVICES[preferred_service]},
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
                total_income=0,
                total_expenses=0,
                net_income=0,
            )

        # Parse P&L data
        pl_data = self._parse_full_pl_report(preferred_service, results[0])

        return self._format_response(
            total=pl_data["net_income"],
            sources=sources,
            errors=errors if errors else None,
            total_income=pl_data["total_income"],
            total_expenses=pl_data["total_expenses"],
            net_income=pl_data["net_income"],
            gross_profit=pl_data.get("gross_profit", 0),
            income_breakdown=pl_data.get("income_breakdown", []),
            expense_breakdown=pl_data.get("expense_breakdown", []),
            period={"start": start_date, "end": end_date},
            source=preferred_service,
        )

    def get_balance_sheet(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get Balance Sheet report.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - as_of_date: Report date (YYYY-MM-DD)
                - source: Accounting system (auto-detected if not specified)

        Returns:
            {
                "total_assets": float,
                "total_liabilities": float,
                "total_equity": float,
                "current_assets": float,
                "fixed_assets": float,
                "current_liabilities": float,
                "long_term_liabilities": float,
                "asset_breakdown": [{account, balance}],
                "liability_breakdown": [{account, balance}],
                "as_of": str,
                "source": str,
                "lastUpdated": str,
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        source = args.get("source")
        as_of_date = args.get("as_of_date", datetime.now(UTC).strftime("%Y-%m-%d"))

        preferred_service = source or self._get_primary_accounting_service(
            org_id, user_id, BALANCE_SHEET_SERVICES
        )

        if not preferred_service:
            return self._format_response(
                total=0,
                errors=[{"service": "balancesheet", "error": "No accounting system connected"}],
                total_assets=0,
                total_liabilities=0,
                total_equity=0,
            )

        connector_args = {"as_of_date": as_of_date}

        results, errors, sources = self._aggregate_from_services(
            {preferred_service: BALANCE_SHEET_SERVICES[preferred_service]},
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
                total_assets=0,
                total_liabilities=0,
                total_equity=0,
            )

        bs_data = self._parse_balance_sheet(preferred_service, results[0])

        return self._format_response(
            total=bs_data["total_assets"],
            sources=sources,
            errors=errors if errors else None,
            total_assets=bs_data["total_assets"],
            total_liabilities=bs_data["total_liabilities"],
            total_equity=bs_data["total_equity"],
            current_assets=bs_data.get("current_assets", 0),
            fixed_assets=bs_data.get("fixed_assets", 0),
            current_liabilities=bs_data.get("current_liabilities", 0),
            long_term_liabilities=bs_data.get("long_term_liabilities", 0),
            asset_breakdown=bs_data.get("asset_breakdown", []),
            liability_breakdown=bs_data.get("liability_breakdown", []),
            as_of=as_of_date,
            source=preferred_service,
        )

    def get_ar_aging_report(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get detailed AR Aging report with customer breakdown.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - as_of_date: Report date (YYYY-MM-DD)
                - aging_periods: "standard", "weekly", "custom"
                - source: Accounting system (auto-detected if not specified)

        Returns:
            {
                "total": float,
                "current": float,
                "days_1_30": float,
                "days_31_60": float,
                "days_61_90": float,
                "days_over_90": float,
                "customers": [{name, total, current, 30, 60, 90, over_90, invoices}],
                "as_of": str,
                "source": str,
                "lastUpdated": str,
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        source = args.get("source")
        as_of_date = args.get("as_of_date", datetime.now(UTC).strftime("%Y-%m-%d"))

        preferred_service = source or self._get_primary_accounting_service(
            org_id, user_id, AR_SERVICES
        )

        if not preferred_service:
            return self._format_response(
                total=0,
                errors=[{"service": "ar_aging", "error": "No accounting system connected"}],
                current=0,
                days_1_30=0,
                days_31_60=0,
                days_61_90=0,
                days_over_90=0,
                customers=[],
            )

        connector_args = {"as_of_date": as_of_date}

        # For detailed report, try to use detail method if available
        method = AR_SERVICES[preferred_service]
        if preferred_service == "quickbooks":
            method = "get_ar_aging_detail"

        results, errors, sources = self._aggregate_from_services(
            {preferred_service: method},
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
                days_1_30=0,
                days_31_60=0,
                days_61_90=0,
                days_over_90=0,
                customers=[],
            )

        ar_data = self._parse_detailed_ar_aging(preferred_service, results[0])

        return self._format_response(
            total=ar_data["total"],
            sources=sources,
            errors=errors if errors else None,
            current=ar_data["current"],
            days_1_30=ar_data["days_30"],
            days_31_60=ar_data["days_60"],
            days_61_90=ar_data["days_90"],
            days_over_90=ar_data["over_90"],
            customers=ar_data.get("customers", []),
            as_of=as_of_date,
            source=preferred_service,
        )

    def get_ap_aging_report(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get detailed AP Aging report with vendor breakdown.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - as_of_date: Report date (YYYY-MM-DD)
                - aging_periods: "standard", "weekly", "custom"
                - source: Accounting system (auto-detected if not specified)

        Returns:
            {
                "total": float,
                "current": float,
                "days_1_30": float,
                "days_31_60": float,
                "days_61_90": float,
                "days_over_90": float,
                "vendors": [{name, total, current, 30, 60, 90, over_90, bills}],
                "as_of": str,
                "source": str,
                "lastUpdated": str,
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        source = args.get("source")
        as_of_date = args.get("as_of_date", datetime.now(UTC).strftime("%Y-%m-%d"))

        preferred_service = source or self._get_primary_accounting_service(
            org_id, user_id, AP_SERVICES
        )

        if not preferred_service:
            return self._format_response(
                total=0,
                errors=[{"service": "ap_aging", "error": "No accounting system connected"}],
                current=0,
                days_1_30=0,
                days_31_60=0,
                days_61_90=0,
                days_over_90=0,
                vendors=[],
            )

        connector_args = {"as_of_date": as_of_date}

        method = AP_SERVICES[preferred_service]
        if preferred_service == "quickbooks":
            method = "get_ap_aging_detail"

        results, errors, sources = self._aggregate_from_services(
            {preferred_service: method},
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
                days_1_30=0,
                days_31_60=0,
                days_61_90=0,
                days_over_90=0,
                vendors=[],
            )

        ap_data = self._parse_detailed_ap_aging(preferred_service, results[0])

        return self._format_response(
            total=ap_data["total"],
            sources=sources,
            errors=errors if errors else None,
            current=ap_data["current"],
            days_1_30=ap_data["days_30"],
            days_31_60=ap_data["days_60"],
            days_61_90=ap_data["days_90"],
            days_over_90=ap_data["over_90"],
            vendors=ap_data.get("vendors", []),
            as_of=as_of_date,
            source=preferred_service,
        )

    def get_cashflow_report(
        self,
        org_id: str,
        user_id: str,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Get Cash Flow Statement.

        Args:
            org_id: Organization ID
            user_id: User ID
            args:
                - start_date: Start date (YYYY-MM-DD)
                - end_date: End date (YYYY-MM-DD)
                - source: Accounting system (auto-detected if not specified)

        Returns:
            {
                "operating_activities": float,
                "investing_activities": float,
                "financing_activities": float,
                "net_change": float,
                "beginning_cash": float,
                "ending_cash": float,
                "details": object,
                "period": {start, end},
                "source": str,
                "lastUpdated": str,
                "errors": [{service, error}],
                "status": "success" | "partial"
            }
        """
        source = args.get("source")
        start_date = args.get("start_date")
        end_date = args.get("end_date")

        if not start_date:
            today = datetime.now(UTC)
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now(UTC).strftime("%Y-%m-%d")

        preferred_service = source or self._get_primary_accounting_service(
            org_id, user_id, CASHFLOW_SERVICES
        )

        if not preferred_service:
            return self._format_response(
                total=0,
                errors=[{"service": "cashflow", "error": "No accounting system connected"}],
                operating_activities=0,
                investing_activities=0,
                financing_activities=0,
                net_change=0,
            )

        connector_args = {
            "start_date": start_date,
            "end_date": end_date,
        }

        results, errors, sources = self._aggregate_from_services(
            {preferred_service: CASHFLOW_SERVICES[preferred_service]},
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
                operating_activities=0,
                investing_activities=0,
                financing_activities=0,
                net_change=0,
            )

        cf_data = self._parse_cashflow_report(preferred_service, results[0])

        return self._format_response(
            total=cf_data["net_change"],
            sources=sources,
            errors=errors if errors else None,
            operating_activities=cf_data["operating"],
            investing_activities=cf_data["investing"],
            financing_activities=cf_data["financing"],
            net_change=cf_data["net_change"],
            beginning_cash=cf_data.get("beginning_cash", 0),
            ending_cash=cf_data.get("ending_cash", 0),
            details=cf_data.get("details"),
            period={"start": start_date, "end": end_date},
            source=preferred_service,
        )

    # =========================================================================
    # Report Parsing Helpers
    # =========================================================================

    def _parse_full_pl_report(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse full P&L report with all sections."""
        data = {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_income": 0.0,
            "gross_profit": 0.0,
            "income_breakdown": [],
            "expense_breakdown": [],
        }
        net_income_fallback: float | None = None
        net_income_seen = False

        if service == "quickbooks":
            rows = result.get("Rows", {}).get("Row", [])
            income_section_keys = {"income", "revenue", "salesrevenue", "operatingrevenue"}
            expense_section_keys = {
                "cogs",
                "costofgoodssold",
                "costofsales",
                "expenses",
                "expense",
                "otherexpenses",
            }

            for row in rows:
                section_key = self._quickbooks_section_key(row)
                summary = row.get("Summary", {})
                col_data = summary.get("ColData", [])

                if section_key in income_section_keys:
                    amount = self._last_numeric_col_value(col_data)
                    if amount is not None:
                        data["total_income"] = amount
                    # Get breakdown
                    for sub_row in row.get("Rows", {}).get("Row", []):
                        sub_cols = sub_row.get("ColData", [])
                        if len(sub_cols) >= 2:
                            amount = self._last_numeric_col_value(sub_cols)
                            if amount is not None:
                                data["income_breakdown"].append(
                                    {
                                        "category": sub_cols[0].get("value", "Other"),
                                        "amount": amount,
                                    }
                                )

                elif section_key in expense_section_keys:
                    amount = self._last_numeric_col_value(col_data)
                    if amount is not None:
                        data["total_expenses"] += abs(amount)
                    for sub_row in row.get("Rows", {}).get("Row", []):
                        sub_cols = sub_row.get("ColData", [])
                        if len(sub_cols) >= 2:
                            amount = self._last_numeric_col_value(sub_cols)
                            if amount is not None:
                                data["expense_breakdown"].append(
                                    {
                                        "category": sub_cols[0].get("value", "Other"),
                                        "amount": abs(amount),
                                    }
                                )

                elif section_key == "grossprofit":
                    amount = self._last_numeric_col_value(col_data)
                    if amount is not None:
                        data["gross_profit"] = amount

                elif section_key == "netincome":
                    amount = self._last_numeric_col_value(col_data)
                    if amount is not None:
                        data["net_income"] = amount
                        net_income_seen = True

                elif section_key == "netoperatingincome":
                    amount = self._last_numeric_col_value(col_data)
                    if amount is not None:
                        net_income_fallback = amount

        # Calculate net if not in report
        if not net_income_seen:
            data["net_income"] = (
                net_income_fallback
                if service == "quickbooks" and net_income_fallback is not None
                else data["total_income"] - data["total_expenses"]
            )

        return data

    def _parse_balance_sheet(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse balance sheet report."""
        data = {
            "total_assets": 0.0,
            "total_liabilities": 0.0,
            "total_equity": 0.0,
            "current_assets": 0.0,
            "fixed_assets": 0.0,
            "current_liabilities": 0.0,
            "long_term_liabilities": 0.0,
            "asset_breakdown": [],
            "liability_breakdown": [],
        }

        if service == "quickbooks":
            rows = result.get("Rows", {}).get("Row", [])

            for row in rows:
                group = row.get("group", "").lower()
                summary = row.get("Summary", {})
                col_data = summary.get("ColData", [])

                if "asset" in group:
                    if col_data:
                        amount = float(col_data[-1].get("value", 0) or 0)
                        if "current" in group:
                            data["current_assets"] = amount
                        elif "fixed" in group or "long" in group:
                            data["fixed_assets"] = amount
                        else:
                            data["total_assets"] = amount

                elif "liabilit" in group:
                    if col_data:
                        amount = float(col_data[-1].get("value", 0) or 0)
                        if "current" in group:
                            data["current_liabilities"] = amount
                        elif "long" in group:
                            data["long_term_liabilities"] = amount
                        else:
                            data["total_liabilities"] = amount

                elif "equity" in group:
                    if col_data:
                        data["total_equity"] = float(col_data[-1].get("value", 0) or 0)

        # Calculate totals if not present
        if data["total_assets"] == 0:
            data["total_assets"] = data["current_assets"] + data["fixed_assets"]
        if data["total_liabilities"] == 0:
            data["total_liabilities"] = data["current_liabilities"] + data["long_term_liabilities"]

        return data

    def _parse_detailed_ar_aging(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse detailed AR aging with customer breakdown."""
        data = {
            "total": 0.0,
            "current": 0.0,
            "days_30": 0.0,
            "days_60": 0.0,
            "days_90": 0.0,
            "over_90": 0.0,
            "customers": [],
        }

        # Use the basic AR aging parser first
        ar_basic = self._parse_ar_aging(service, result)
        data.update(
            {
                "total": ar_basic["total"],
                "current": ar_basic["current"],
                "days_30": ar_basic["days_30"],
                "days_60": ar_basic["days_60"],
                "days_90": ar_basic["days_90"],
                "over_90": ar_basic["over_90"],
            }
        )

        # Extract customer details if available
        if service == "quickbooks":
            rows = result.get("Rows", {}).get("Row", [])
            for row in rows:
                if row.get("type") == "Section":
                    header = row.get("Header", {})
                    col_data = header.get("ColData", [])
                    if col_data:
                        customer_name = col_data[0].get("value", "Unknown")
                        summary = row.get("Summary", {}).get("ColData", [])
                        if len(summary) >= 6:
                            data["customers"].append(
                                {
                                    "name": customer_name,
                                    "current": float(summary[1].get("value", 0) or 0),
                                    "days_30": float(summary[2].get("value", 0) or 0),
                                    "days_60": float(summary[3].get("value", 0) or 0),
                                    "days_90": float(summary[4].get("value", 0) or 0),
                                    "over_90": float(summary[5].get("value", 0) or 0),
                                    "total": float(summary[-1].get("value", 0) or 0),
                                }
                            )

        return data

    def _parse_detailed_ap_aging(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse detailed AP aging with vendor breakdown."""
        data = {
            "total": 0.0,
            "current": 0.0,
            "days_30": 0.0,
            "days_60": 0.0,
            "days_90": 0.0,
            "over_90": 0.0,
            "vendors": [],
        }

        # Use the basic AP aging parser first
        ap_basic = self._parse_ap_aging(service, result)
        data.update(
            {
                "total": ap_basic["total"],
                "current": ap_basic["current"],
                "days_30": ap_basic["days_30"],
                "days_60": ap_basic["days_60"],
                "days_90": ap_basic["days_90"],
                "over_90": ap_basic["over_90"],
            }
        )

        # Extract vendor details if available
        if service == "quickbooks":
            rows = result.get("Rows", {}).get("Row", [])
            for row in rows:
                if row.get("type") == "Section":
                    header = row.get("Header", {})
                    col_data = header.get("ColData", [])
                    if col_data:
                        vendor_name = col_data[0].get("value", "Unknown")
                        summary = row.get("Summary", {}).get("ColData", [])
                        if len(summary) >= 6:
                            data["vendors"].append(
                                {
                                    "name": vendor_name,
                                    "current": float(summary[1].get("value", 0) or 0),
                                    "days_30": float(summary[2].get("value", 0) or 0),
                                    "days_60": float(summary[3].get("value", 0) or 0),
                                    "days_90": float(summary[4].get("value", 0) or 0),
                                    "over_90": float(summary[5].get("value", 0) or 0),
                                    "total": float(summary[-1].get("value", 0) or 0),
                                }
                            )

        return data

    def _parse_cashflow_report(
        self,
        service: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse cash flow statement."""
        data = {
            "operating": 0.0,
            "investing": 0.0,
            "financing": 0.0,
            "net_change": 0.0,
            "beginning_cash": 0.0,
            "ending_cash": 0.0,
            "details": {},
        }

        if service == "quickbooks":
            rows = result.get("Rows", {}).get("Row", [])

            for row in rows:
                group = row.get("group", "").lower()
                summary = row.get("Summary", {})
                col_data = summary.get("ColData", [])

                if col_data:
                    amount = float(col_data[-1].get("value", 0) or 0)

                    if "operating" in group:
                        data["operating"] = amount
                    elif "investing" in group:
                        data["investing"] = amount
                    elif "financing" in group:
                        data["financing"] = amount
                    elif "net change" in group or "change in cash" in group:
                        data["net_change"] = amount
                    elif "beginning" in group:
                        data["beginning_cash"] = amount
                    elif "ending" in group:
                        data["ending_cash"] = amount

        # Calculate net if not in report
        if data["net_change"] == 0:
            data["net_change"] = data["operating"] + data["investing"] + data["financing"]

        return data
