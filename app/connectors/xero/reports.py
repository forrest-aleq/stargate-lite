"""
Xero Reports connector - Financial reports and journal entries.

Reference:
- Reports: https://developer.xero.com/documentation/api/accounting/reports
- Journals: https://developer.xero.com/documentation/api/accounting/journals
- Manual Journals: https://developer.xero.com/documentation/api/accounting/manualjournals

Available Reports:
- BalanceSheet
- BankStatement
- BankSummary
- ProfitAndLoss
- TrialBalance
- AgedReceivablesByContact
- AgedPayablesByContact
- BudgetSummary
- ExecutiveSummary
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .bank import BankMixin

logger = get_logger(__name__)


class ReportsMixin(BankMixin):
    """Mixin providing financial reports and journal entry capabilities."""

    def get_profit_and_loss(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get Profit and Loss report.

        Args:
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            periods: Number of periods (1-11)
            timeframe: MONTH, QUARTER, or YEAR
            tracking_category_id: Filter by tracking category
            tracking_option_id: Filter by tracking option
            standard_layout: Use standard layout (default True)
            payments_only: Cash basis (default False - accrual)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}

        if args.get("from_date"):
            params["fromDate"] = args["from_date"]
        if args.get("to_date"):
            params["toDate"] = args["to_date"]
        if args.get("periods"):
            params["periods"] = min(args["periods"], 11)
        if args.get("timeframe"):
            params["timeframe"] = args["timeframe"]
        if args.get("tracking_category_id"):
            params["trackingCategoryID"] = args["tracking_category_id"]
        if args.get("tracking_option_id"):
            params["trackingOptionID"] = args["tracking_option_id"]
        if args.get("standard_layout") is not None:
            params["standardLayout"] = args["standard_layout"]
        if args.get("payments_only"):
            params["paymentsOnly"] = args["payments_only"]

        result = self._make_api_call("GET", "Reports/ProfitAndLoss", cred, tenant_id, params=params)
        reports = result.get("Reports", [])

        if not reports:
            return {"report": None, "status": "no_data"}

        report = reports[0]
        logger.info(
            "Xero P&L report retrieved",
            service="xero",
            from_date=args.get("from_date"),
            to_date=args.get("to_date"),
            log_event="profit_and_loss_retrieved",
        )

        return {"report": self._format_report(report), "status": "success"}

    def get_balance_sheet(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get Balance Sheet report.

        Args:
            date: Report date (YYYY-MM-DD, default today)
            periods: Number of periods (1-11)
            timeframe: MONTH, QUARTER, or YEAR
            tracking_category_id: Filter by tracking category
            standard_layout: Use standard layout (default True)
            payments_only: Cash basis (default False)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}

        if args.get("date"):
            params["date"] = args["date"]
        if args.get("periods"):
            params["periods"] = min(args["periods"], 11)
        if args.get("timeframe"):
            params["timeframe"] = args["timeframe"]
        if args.get("tracking_category_id"):
            params["trackingCategoryID"] = args["tracking_category_id"]
        if args.get("standard_layout") is not None:
            params["standardLayout"] = args["standard_layout"]
        if args.get("payments_only"):
            params["paymentsOnly"] = args["payments_only"]

        result = self._make_api_call("GET", "Reports/BalanceSheet", cred, tenant_id, params=params)
        reports = result.get("Reports", [])

        if not reports:
            return {"report": None, "status": "no_data"}

        report = reports[0]
        logger.info(
            "Xero balance sheet retrieved",
            service="xero",
            date=args.get("date"),
            log_event="balance_sheet_retrieved",
        )

        return {"report": self._format_report(report), "status": "success"}

    def get_trial_balance(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get Trial Balance report.

        Args:
            date: Report date (YYYY-MM-DD)
            payments_only: Cash basis (default False)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}

        if args.get("date"):
            params["date"] = args["date"]
        if args.get("payments_only"):
            params["paymentsOnly"] = args["payments_only"]

        result = self._make_api_call("GET", "Reports/TrialBalance", cred, tenant_id, params=params)
        reports = result.get("Reports", [])

        if not reports:
            return {"report": None, "status": "no_data"}

        report = reports[0]
        logger.info(
            "Xero trial balance retrieved",
            service="xero",
            date=args.get("date"),
            log_event="trial_balance_retrieved",
        )

        return {"report": self._format_report(report), "status": "success"}

    def get_aged_receivables(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get Aged Receivables by Contact report.

        Args:
            date: Report date (YYYY-MM-DD)
            from_date: Include invoices from this date
            to_date: Include invoices to this date
            contact_id: Filter by specific contact
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}

        if args.get("date"):
            params["date"] = args["date"]
        if args.get("from_date"):
            params["fromDate"] = args["from_date"]
        if args.get("to_date"):
            params["toDate"] = args["to_date"]
        if args.get("contact_id"):
            params["contactID"] = args["contact_id"]

        result = self._make_api_call(
            "GET", "Reports/AgedReceivablesByContact", cred, tenant_id, params=params
        )
        reports = result.get("Reports", [])

        if not reports:
            return {"report": None, "status": "no_data"}

        report = reports[0]
        logger.info(
            "Xero aged receivables retrieved",
            service="xero",
            date=args.get("date"),
            log_event="aged_receivables_retrieved",
        )

        return {"report": self._format_report(report), "status": "success"}

    def get_aged_payables(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get Aged Payables by Contact report.

        Args:
            date: Report date (YYYY-MM-DD)
            from_date: Include bills from this date
            to_date: Include bills to this date
            contact_id: Filter by specific contact
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}

        if args.get("date"):
            params["date"] = args["date"]
        if args.get("from_date"):
            params["fromDate"] = args["from_date"]
        if args.get("to_date"):
            params["toDate"] = args["to_date"]
        if args.get("contact_id"):
            params["contactID"] = args["contact_id"]

        result = self._make_api_call(
            "GET", "Reports/AgedPayablesByContact", cred, tenant_id, params=params
        )
        reports = result.get("Reports", [])

        if not reports:
            return {"report": None, "status": "no_data"}

        report = reports[0]
        logger.info(
            "Xero aged payables retrieved",
            service="xero",
            date=args.get("date"),
            log_event="aged_payables_retrieved",
        )

        return {"report": self._format_report(report), "status": "success"}

    def get_budget_summary(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get Budget Summary report.

        Args:
            date: Report date (YYYY-MM-DD)
            periods: Number of periods (default 12)
            timeframe: MONTH, QUARTER, or YEAR
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}

        if args.get("date"):
            params["date"] = args["date"]
        if args.get("periods"):
            params["periods"] = args["periods"]
        if args.get("timeframe"):
            params["timeframe"] = args["timeframe"]

        result = self._make_api_call(
            "GET", "Reports/BudgetSummary", cred, tenant_id, params=params
        )
        reports = result.get("Reports", [])

        if not reports:
            return {"report": None, "status": "no_data"}

        report = reports[0]
        logger.info(
            "Xero budget summary retrieved",
            service="xero",
            date=args.get("date"),
            log_event="budget_summary_retrieved",
        )

        return {"report": self._format_report(report), "status": "success"}

    def list_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List chart of accounts.

        Args:
            where: Filter expression
            order: Sort field
            class_type: Filter by class - ASSET, EQUITY, EXPENSE, LIABILITY, REVENUE
            account_type: Filter by type - BANK, CURRENT, CURRLIAB, etc.
            include_archived: Include archived accounts
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}
        where_clauses: list[str] = []

        if args.get("where"):
            where_clauses.append(args["where"])

        if args.get("class_type"):
            where_clauses.append(f'Class=="{args["class_type"]}"')

        if args.get("account_type"):
            where_clauses.append(f'Type=="{args["account_type"]}"')

        if not args.get("include_archived", False):
            where_clauses.append('Status!="ARCHIVED"')

        if where_clauses:
            params["where"] = " AND ".join(where_clauses)

        if args.get("order"):
            params["order"] = args["order"]

        result = self._make_api_call("GET", "Accounts", cred, tenant_id, params=params)
        accounts = result.get("Accounts", [])

        logger.info(
            "Xero accounts listed",
            service="xero",
            count=len(accounts),
            log_event="accounts_listed",
        )

        return {
            "accounts": [self._format_account(acct) for acct in accounts],
            "count": len(accounts),
            "status": "success",
        }

    def list_manual_journals(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List manual journal entries.

        Args:
            where: Filter expression
            order: Sort field
            page: Page number
            date_from: Filter from this date
            date_to: Filter to this date
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}
        where_clauses: list[str] = []

        if args.get("where"):
            where_clauses.append(args["where"])

        if args.get("date_from"):
            where_clauses.append(f'Date>=DateTime({args["date_from"].replace("-", ",")})')

        if args.get("date_to"):
            where_clauses.append(f'Date<=DateTime({args["date_to"].replace("-", ",")})')

        if where_clauses:
            params["where"] = " AND ".join(where_clauses)

        if args.get("order"):
            params["order"] = args["order"]
        else:
            params["order"] = "Date DESC"

        page = args.get("page", 1)
        params["page"] = page

        result = self._make_api_call("GET", "ManualJournals", cred, tenant_id, params=params)
        journals = result.get("ManualJournals", [])

        logger.info(
            "Xero manual journals listed",
            service="xero",
            count=len(journals),
            log_event="manual_journals_listed",
        )

        return {
            "journals": [self._format_manual_journal(j) for j in journals],
            "count": len(journals),
            "page": page,
            "status": "success",
        }

    def get_manual_journal(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get a specific manual journal entry.

        Args:
            journal_id: ManualJournalID (UUID)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        journal_id = args.get("journal_id")
        if not journal_id:
            raise ValidationError("journal_id", "journal_id is required")

        result = self._make_api_call("GET", f"ManualJournals/{journal_id}", cred, tenant_id)
        journals = result.get("ManualJournals", [])

        if not journals:
            return {"journal": None, "status": "not_found"}

        return {"journal": self._format_manual_journal(journals[0]), "status": "success"}

    def create_manual_journal(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a manual journal entry.

        Args:
            narration: Journal description (required)
            journal_lines: List of journal lines (required, must balance)
                - account_code: GL account code
                - description: Line description
                - debit_amount: Debit amount (mutually exclusive with credit)
                - credit_amount: Credit amount (mutually exclusive with debit)
                - tax_type: Tax type code
                - tracking: Tracking categories
            date: Journal date (YYYY-MM-DD)
            status: DRAFT or POSTED (default DRAFT)
            show_on_cash_basis_reports: Include in cash reports
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("narration"):
            raise ValidationError("narration", "narration (description) is required")
        if not args.get("journal_lines"):
            raise ValidationError("journal_lines", "At least two journal lines required")

        # Validate that journal balances
        total_debit = sum(line.get("debit_amount", 0) or 0 for line in args["journal_lines"])
        total_credit = sum(line.get("credit_amount", 0) or 0 for line in args["journal_lines"])

        if abs(total_debit - total_credit) > 0.01:
            raise ValidationError(
                "journal_lines",
                f"Journal does not balance: debits={total_debit}, credits={total_credit}",
            )

        journal_data: dict[str, Any] = {
            "Narration": args["narration"],
            "JournalLines": self._format_journal_lines_for_api(args["journal_lines"]),
        }

        if args.get("date"):
            journal_data["Date"] = args["date"]
        if args.get("status"):
            journal_data["Status"] = args["status"]
        if args.get("show_on_cash_basis_reports") is not None:
            journal_data["ShowOnCashBasisReports"] = args["show_on_cash_basis_reports"]

        result = self._make_api_call(
            "POST",
            "ManualJournals",
            cred,
            tenant_id,
            data={"ManualJournals": [journal_data]},
        )

        created = result.get("ManualJournals", [])[0] if result.get("ManualJournals") else {}

        logger.info(
            "Xero manual journal created",
            service="xero",
            journal_id=created.get("ManualJournalID"),
            narration=args["narration"][:50],
            log_event="manual_journal_created",
        )

        return {"journal": self._format_manual_journal(created), "status": "success"}

    def void_manual_journal(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Void a manual journal entry.

        Args:
            journal_id: ManualJournalID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        journal_id = args.get("journal_id")
        if not journal_id:
            raise ValidationError("journal_id", "journal_id is required")

        journal_data = {"ManualJournalID": journal_id, "Status": "VOIDED"}

        self._make_api_call(
            "POST",
            f"ManualJournals/{journal_id}",
            cred,
            tenant_id,
            data={"ManualJournals": [journal_data]},
        )

        logger.info(
            "Xero manual journal voided",
            service="xero",
            journal_id=journal_id,
            log_event="manual_journal_voided",
        )

        return {"journal_id": journal_id, "status": "voided"}

    def list_journals(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List system journals (all journal entries including auto-generated).

        Args:
            offset: Start from this journal number
            payments_only: Cash basis filter
            modified_since: Only return journals modified since this datetime
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}

        if args.get("offset"):
            params["offset"] = args["offset"]
        if args.get("payments_only"):
            params["paymentsOnly"] = args["payments_only"]

        result = self._make_api_call("GET", "Journals", cred, tenant_id, params=params)
        journals = result.get("Journals", [])

        logger.info(
            "Xero journals listed",
            service="xero",
            count=len(journals),
            log_event="journals_listed",
        )

        return {
            "journals": [self._format_system_journal(j) for j in journals],
            "count": len(journals),
            "status": "success",
        }

    def _format_report(self, report: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero report for API response."""
        rows = report.get("Rows", [])
        formatted_rows: list[dict[str, Any]] = []

        for row in rows:
            row_type = row.get("RowType")
            cells = row.get("Cells", [])

            if row_type == "Header":
                formatted_rows.append(
                    {
                        "type": "header",
                        "values": [c.get("Value") for c in cells],
                    }
                )
            elif row_type == "Section":
                section_rows = self._format_section_rows(row.get("Rows", []))
                formatted_rows.append(
                    {
                        "type": "section",
                        "title": row.get("Title"),
                        "rows": section_rows,
                    }
                )
            elif row_type == "Row":
                formatted_rows.append(
                    {
                        "type": "row",
                        "values": [
                            {
                                "value": c.get("Value"),
                                "account_id": c.get("Attributes", [{}])[0].get("Value")
                                if c.get("Attributes")
                                else None,
                            }
                            for c in cells
                        ],
                    }
                )
            elif row_type == "SummaryRow":
                formatted_rows.append(
                    {
                        "type": "summary",
                        "values": [c.get("Value") for c in cells],
                    }
                )

        return {
            "report_id": report.get("ReportID"),
            "report_name": report.get("ReportName"),
            "report_type": report.get("ReportType"),
            "report_titles": report.get("ReportTitles", []),
            "report_date": report.get("ReportDate"),
            "updated_date": report.get("UpdatedDateUTC"),
            "rows": formatted_rows,
        }

    def _format_section_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format section rows within a report."""
        formatted: list[dict[str, Any]] = []
        for row in rows:
            cells = row.get("Cells", [])
            formatted.append(
                {
                    "type": row.get("RowType", "Row").lower(),
                    "values": [
                        {
                            "value": c.get("Value"),
                            "account_id": c.get("Attributes", [{}])[0].get("Value")
                            if c.get("Attributes")
                            else None,
                        }
                        for c in cells
                    ],
                }
            )
        return formatted

    def _format_account(self, account: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero account for API response."""
        return {
            "account_id": account.get("AccountID"),
            "code": account.get("Code"),
            "name": account.get("Name"),
            "type": account.get("Type"),
            "class": account.get("Class"),
            "status": account.get("Status"),
            "description": account.get("Description"),
            "tax_type": account.get("TaxType"),
            "enable_payments_to_account": account.get("EnablePaymentsToAccount"),
            "show_in_expense_claims": account.get("ShowInExpenseClaims"),
            "bank_account_number": account.get("BankAccountNumber"),
            "bank_account_type": account.get("BankAccountType"),
            "currency_code": account.get("CurrencyCode"),
            "reporting_code": account.get("ReportingCode"),
            "reporting_code_name": account.get("ReportingCodeName"),
            "updated_date": account.get("UpdatedDateUTC"),
        }

    def _format_manual_journal(self, journal: dict[str, Any]) -> dict[str, Any]:
        """Format a manual journal for API response."""
        lines = journal.get("JournalLines", [])

        return {
            "journal_id": journal.get("ManualJournalID"),
            "narration": journal.get("Narration"),
            "date": journal.get("Date"),
            "status": journal.get("Status"),
            "line_amount_types": journal.get("LineAmountTypes"),
            "show_on_cash_basis_reports": journal.get("ShowOnCashBasisReports"),
            "has_attachments": journal.get("HasAttachments", False),
            "journal_lines": [
                {
                    "line_id": jl.get("JournalLineID"),
                    "account_code": jl.get("AccountCode"),
                    "account_id": jl.get("AccountID"),
                    "account_name": jl.get("AccountName"),
                    "description": jl.get("Description"),
                    "net_amount": jl.get("NetAmount"),
                    "gross_amount": jl.get("GrossAmount"),
                    "tax_amount": jl.get("TaxAmount"),
                    "tax_type": jl.get("TaxType"),
                    "tracking": jl.get("Tracking", []),
                }
                for jl in lines
            ],
            "updated_date": journal.get("UpdatedDateUTC"),
        }

    def _format_system_journal(self, journal: dict[str, Any]) -> dict[str, Any]:
        """Format a system journal for API response."""
        lines = journal.get("JournalLines", [])

        return {
            "journal_id": journal.get("JournalID"),
            "journal_number": journal.get("JournalNumber"),
            "journal_date": journal.get("JournalDate"),
            "created_date": journal.get("CreatedDateUTC"),
            "reference": journal.get("Reference"),
            "source_id": journal.get("SourceID"),
            "source_type": journal.get("SourceType"),
            "journal_lines": [
                {
                    "account_id": jl.get("AccountID"),
                    "account_code": jl.get("AccountCode"),
                    "account_name": jl.get("AccountName"),
                    "account_type": jl.get("AccountType"),
                    "description": jl.get("Description"),
                    "net_amount": jl.get("NetAmount"),
                    "gross_amount": jl.get("GrossAmount"),
                    "tax_amount": jl.get("TaxAmount"),
                    "tax_type": jl.get("TaxType"),
                    "tax_name": jl.get("TaxName"),
                }
                for jl in lines
            ],
        }

    def _format_journal_lines_for_api(
        self, journal_lines: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Format journal lines for manual journal API request."""
        formatted: list[dict[str, Any]] = []
        for line in journal_lines:
            xero_line: dict[str, Any] = {"AccountCode": line["account_code"]}

            if line.get("description"):
                xero_line["Description"] = line["description"]

            # Handle debit/credit - Xero uses LineAmount
            if line.get("debit_amount"):
                xero_line["LineAmount"] = line["debit_amount"]
            elif line.get("credit_amount"):
                xero_line["LineAmount"] = -line["credit_amount"]

            if line.get("tax_type"):
                xero_line["TaxType"] = line["tax_type"]

            if line.get("tracking"):
                xero_line["Tracking"] = [
                    {"Name": t.get("name"), "Option": t.get("option")} for t in line["tracking"]
                ]

            formatted.append(xero_line)
        return formatted
