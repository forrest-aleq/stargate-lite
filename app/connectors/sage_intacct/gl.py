"""
Sage Intacct General Ledger connector.

Reference: https://developer.sage.com/intacct/docs/

Provides:
- Chart of Accounts management
- Journal entries
- Budgets
- Trial balance
- Statistical journals
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .base import SageIntacctBase

logger = get_logger(__name__)


class GLMixin(SageIntacctBase):
    """Mixin providing General Ledger capabilities."""

    def list_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List chart of accounts.

        Args:
            account_type: Filter by type - "balancesheet", "incomestatement", "statistical"
            status: Filter by status - "active", "inactive"
            page_size: Results per page (default 100)
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("account_type"):
            filters.append(f'accountType eq "{args["account_type"]}"')
        if args.get("status"):
            filters.append(f'status eq "{args["status"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        accounts = self._paginate("objects/gl-account", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct accounts listed",
            service="sage_intacct",
            count=len(accounts),
            log_event="accounts_listed",
        )

        return {
            "accounts": [self._format_account(a) for a in accounts],
            "count": len(accounts),
            "status": "success",
        }

    def get_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific GL account.

        Args:
            account_no: Account number (required)
        """
        cred = self._get_access_token(org_id, user_id)

        account_no = args.get("account_no")
        if not account_no:
            raise ValidationError("account_no", "account_no is required")

        result = self._make_api_call("GET", f"objects/gl-account/{account_no}", cred)
        account = result.get("ia::result", {})

        if not account:
            return {"account": None, "status": "not_found"}

        return {"account": self._format_account(account), "status": "success"}

    def create_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new GL account.

        Args:
            account_no: Account number (required)
            title: Account title (required)
            account_type: Type - "balancesheet" or "incomestatement" (required)
            normal_balance: "debit" or "credit" (required)
            status: "active" or "inactive" (default "active")
            category: Category name
            close_into_account_no: For income statement accounts
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("account_no"):
            raise ValidationError("account_no", "account_no is required")
        if not args.get("title"):
            raise ValidationError("title", "title is required")
        if not args.get("account_type"):
            raise ValidationError("account_type", "account_type is required")
        if not args.get("normal_balance"):
            raise ValidationError("normal_balance", "normal_balance is required")

        account_data: dict[str, Any] = {
            "accountNo": args["account_no"],
            "title": args["title"],
            "accountType": args["account_type"],
            "normalBalance": args["normal_balance"],
        }

        if args.get("status"):
            account_data["status"] = args["status"]
        if args.get("category"):
            account_data["category"] = args["category"]
        if args.get("close_into_account_no"):
            account_data["closeIntoGLAccountNo"] = args["close_into_account_no"]

        result = self._make_api_call("POST", "objects/gl-account", cred, data=account_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct account created",
            service="sage_intacct",
            account_no=args["account_no"],
            log_event="account_created",
        )

        return {"account": self._format_account(created), "status": "success"}

    def update_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an existing GL account.

        Args:
            account_no: Account number (required)
            title: Updated title
            status: Updated status
            category: Updated category
        """
        cred = self._get_access_token(org_id, user_id)

        account_no = args.get("account_no")
        if not account_no:
            raise ValidationError("account_no", "account_no is required")

        account_data: dict[str, Any] = {}
        if args.get("title"):
            account_data["title"] = args["title"]
        if args.get("status"):
            account_data["status"] = args["status"]
        if args.get("category"):
            account_data["category"] = args["category"]

        result = self._make_api_call(
            "PATCH", f"objects/gl-account/{account_no}", cred, data=account_data
        )
        updated = result.get("ia::result", {})

        logger.info(
            "Sage Intacct account updated",
            service="sage_intacct",
            account_no=account_no,
            log_event="account_updated",
        )

        return {"account": self._format_account(updated), "status": "success"}

    def list_journal_entries(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List journal entries.

        Args:
            date_from: Filter from this date (YYYY-MM-DD)
            date_to: Filter to this date (YYYY-MM-DD)
            state: Filter by state - "draft", "submitted", "approved", "declined", "posted"
            page_size: Results per page
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("date_from"):
            filters.append(f'glPostingDate ge "{args["date_from"]}"')
        if args.get("date_to"):
            filters.append(f'glPostingDate le "{args["date_to"]}"')
        if args.get("state"):
            filters.append(f'state eq "{args["state"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        journals = self._paginate("objects/gl-batch", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct journal entries listed",
            service="sage_intacct",
            count=len(journals),
            log_event="journal_entries_listed",
        )

        return {
            "journals": [self._format_journal_entry(j) for j in journals],
            "count": len(journals),
            "status": "success",
        }

    def get_journal_entry(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific journal entry.

        Args:
            journal_key: Journal entry key (required)
        """
        cred = self._get_access_token(org_id, user_id)

        journal_key = args.get("journal_key")
        if not journal_key:
            raise ValidationError("journal_key", "journal_key is required")

        result = self._make_api_call("GET", f"objects/gl-batch/{journal_key}", cred)
        journal = result.get("ia::result", {})

        if not journal:
            return {"journal": None, "status": "not_found"}

        return {"journal": self._format_journal_entry(journal), "status": "success"}

    def create_journal_entry(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a journal entry.

        Args:
            journal_symbol: Journal symbol/code (required)
            posting_date: Posting date YYYY-MM-DD (required)
            lines: Journal lines (required)
                - account_no: GL account number
                - amount: Amount (positive for debit, negative for credit)
                - memo: Line memo
                - department_id: Department ID
                - location_id: Location ID
            description: Journal description
            reference_number: Reference number
            state: Initial state - "draft" or "posted" (default "draft")
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("journal_symbol"):
            raise ValidationError("journal_symbol", "journal_symbol is required")
        if not args.get("posting_date"):
            raise ValidationError("posting_date", "posting_date is required")
        if not args.get("lines"):
            raise ValidationError("lines", "At least two journal lines required")

        # Validate that lines balance
        lines = args["lines"]
        total = sum(line.get("amount", 0) for line in lines)
        if abs(total) > 0.01:
            raise ValidationError("lines", f"Journal does not balance: total={total}")

        journal_data: dict[str, Any] = {
            "journal": {"key": args["journal_symbol"]},
            "glPostingDate": args["posting_date"],
            "glEntry": [self._format_journal_line_for_api(line) for line in lines],
        }

        if args.get("description"):
            journal_data["description"] = args["description"]
        if args.get("reference_number"):
            journal_data["referenceNumber"] = args["reference_number"]
        if args.get("state"):
            journal_data["state"] = args["state"]

        result = self._make_api_call("POST", "objects/gl-batch", cred, data=journal_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct journal entry created",
            service="sage_intacct",
            journal_key=created.get("key"),
            log_event="journal_entry_created",
        )

        return {"journal": self._format_journal_entry(created), "status": "success"}

    def post_journal_entry(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Post a draft journal entry.

        Args:
            journal_key: Journal entry key (required)
        """
        cred = self._get_access_token(org_id, user_id)

        journal_key = args.get("journal_key")
        if not journal_key:
            raise ValidationError("journal_key", "journal_key is required")

        self._make_api_call(
            "PATCH", f"objects/gl-batch/{journal_key}", cred, data={"state": "posted"}
        )

        logger.info(
            "Sage Intacct journal entry posted",
            service="sage_intacct",
            journal_key=journal_key,
            log_event="journal_entry_posted",
        )

        return {"journal_key": journal_key, "status": "posted"}

    def reverse_journal_entry(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a reversing journal entry.

        Args:
            journal_key: Journal entry key to reverse (required)
            reversal_date: Date for the reversing entry (required)
        """
        cred = self._get_access_token(org_id, user_id)

        journal_key = args.get("journal_key")
        if not journal_key:
            raise ValidationError("journal_key", "journal_key is required")
        if not args.get("reversal_date"):
            raise ValidationError("reversal_date", "reversal_date is required")

        # Get original journal
        original = self._make_api_call("GET", f"objects/gl-batch/{journal_key}", cred)
        original_data = original.get("ia::result", {})

        if not original_data:
            raise ValidationError("journal_key", f"Journal {journal_key} not found")

        # Create reversed lines (negate amounts)
        reversed_lines = [
            {
                "account_no": line.get("glAccount", {}).get("accountNo"),
                "amount": -float(line.get("amount", 0)),
                "memo": f"Reversal of {journal_key}: {line.get('memo', '')}",
            }
            for line in original_data.get("glEntry", [])
        ]

        # Create reversing entry
        reversal_args = {
            "journal_symbol": original_data.get("journal", {}).get("key"),
            "posting_date": args["reversal_date"],
            "lines": reversed_lines,
            "description": f"Reversal of {journal_key}",
            "reference_number": f"REV-{journal_key}",
        }

        return self.create_journal_entry(org_id, user_id, reversal_args)

    def get_trial_balance(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get trial balance report.

        Args:
            as_of_date: Report date (YYYY-MM-DD, default current date)
            department_id: Filter by department
            location_id: Filter by location
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        if args.get("as_of_date"):
            params["asOfDate"] = args["as_of_date"]
        if args.get("department_id"):
            params["departmentId"] = args["department_id"]
        if args.get("location_id"):
            params["locationId"] = args["location_id"]

        result = self._make_api_call("GET", "services/gl/trial-balance", cred, params=params)
        data = result.get("ia::result", {})

        accounts = data.get("accounts", [])
        totals = data.get("totals", {})

        logger.info(
            "Sage Intacct trial balance retrieved",
            service="sage_intacct",
            account_count=len(accounts),
            log_event="trial_balance_retrieved",
        )

        return {
            "as_of_date": args.get("as_of_date"),
            "accounts": [
                {
                    "account_no": a.get("accountNo"),
                    "title": a.get("title"),
                    "debit": a.get("debit"),
                    "credit": a.get("credit"),
                }
                for a in accounts
            ],
            "totals": {
                "total_debit": totals.get("debit"),
                "total_credit": totals.get("credit"),
            },
            "account_count": len(accounts),
            "status": "success",
        }

    def _format_account(self, account: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct GL account for API response."""
        return {
            "key": account.get("key"),
            "account_no": account.get("accountNo"),
            "title": account.get("title"),
            "account_type": account.get("accountType"),
            "normal_balance": account.get("normalBalance"),
            "status": account.get("status"),
            "category": account.get("category"),
            "close_into_account_no": account.get("closeIntoGLAccountNo"),
            "href": account.get("href"),
        }

    def _format_journal_entry(self, journal: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct journal entry for API response."""
        lines = journal.get("glEntry", [])

        return {
            "key": journal.get("key"),
            "record_no": journal.get("recordNo"),
            "journal_symbol": journal.get("journal", {}).get("key"),
            "posting_date": journal.get("glPostingDate"),
            "description": journal.get("description"),
            "reference_number": journal.get("referenceNumber"),
            "state": journal.get("state"),
            "total_entered": journal.get("totalEntered"),
            "lines": [
                {
                    "key": entry.get("key"),
                    "account_no": entry.get("glAccount", {}).get("accountNo"),
                    "amount": entry.get("amount"),
                    "memo": entry.get("memo"),
                    "department_id": entry.get("department", {}).get("id"),
                    "location_id": entry.get("location", {}).get("id"),
                }
                for entry in lines
            ],
            "created_date": journal.get("audit", {}).get("createdDateTime"),
            "modified_date": journal.get("audit", {}).get("modifiedDateTime"),
        }

    def _format_journal_line_for_api(self, line: dict[str, Any]) -> dict[str, Any]:
        """Format a journal line for Sage Intacct API request."""
        formatted: dict[str, Any] = {
            "glAccount": {"accountNo": line["account_no"]},
            "amount": line["amount"],
        }

        if line.get("memo"):
            formatted["memo"] = line["memo"]
        if line.get("department_id"):
            formatted["department"] = {"id": line["department_id"]}
        if line.get("location_id"):
            formatted["location"] = {"id": line["location_id"]}

        return formatted
