"""
Sage Intacct Cash Management connector.

Reference: https://developer.sage.com/intacct/docs/

Provides:
- Bank accounts (checking accounts)
- Bank transactions
- Deposits
- Transfers
- Cash flow statements
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .ar import ARMixin

logger = get_logger(__name__)


class CashManagementMixin(ARMixin):
    """Mixin providing Cash Management capabilities."""

    def list_bank_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List checking accounts (bank accounts).

        Args:
            status: Filter by status - "active", "inactive"
            bank_name: Filter by bank name
            page_size: Results per page
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("status"):
            filters.append(f'status eq "{args["status"]}"')
        if args.get("bank_name"):
            filters.append(f'bankName eq "{args["bank_name"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        accounts = self._paginate("objects/checking-account", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct bank accounts listed",
            service="sage_intacct",
            count=len(accounts),
            log_event="bank_accounts_listed",
        )

        return {
            "bank_accounts": [self._format_bank_account(a) for a in accounts],
            "count": len(accounts),
            "status": "success",
        }

    def get_bank_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific bank account.

        Args:
            bank_account_id: Bank account ID (required)
        """
        cred = self._get_access_token(org_id, user_id)

        bank_account_id = args.get("bank_account_id")
        if not bank_account_id:
            raise ValidationError("bank_account_id", "bank_account_id is required")

        result = self._make_api_call("GET", f"objects/checking-account/{bank_account_id}", cred)
        account = result.get("ia::result", {})

        if not account:
            return {"bank_account": None, "status": "not_found"}

        return {"bank_account": self._format_bank_account(account), "status": "success"}

    def get_bank_account_balance(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get current balance for a bank account.

        Args:
            bank_account_id: Bank account ID (required)
            as_of_date: Balance as of date (YYYY-MM-DD, default today)
        """
        cred = self._get_access_token(org_id, user_id)

        bank_account_id = args.get("bank_account_id")
        if not bank_account_id:
            raise ValidationError("bank_account_id", "bank_account_id is required")

        params: dict[str, Any] = {"accountId": bank_account_id}
        if args.get("as_of_date"):
            params["asOfDate"] = args["as_of_date"]

        result = self._make_api_call("GET", "services/cash-management/balance", cred, params=params)
        data = result.get("ia::result", {})

        logger.info(
            "Sage Intacct bank account balance retrieved",
            service="sage_intacct",
            bank_account_id=bank_account_id,
            log_event="bank_balance_retrieved",
        )

        return {
            "bank_account_id": bank_account_id,
            "as_of_date": args.get("as_of_date"),
            "book_balance": data.get("bookBalance"),
            "cleared_balance": data.get("clearedBalance"),
            "uncleared_deposits": data.get("unclearedDeposits"),
            "uncleared_payments": data.get("unclearedPayments"),
            "available_balance": data.get("availableBalance"),
            "currency": data.get("currency"),
            "status": "success",
        }

    def list_bank_transactions(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List bank transactions (deposits, payments, transfers).

        Args:
            bank_account_id: Filter by bank account
            date_from: Filter from this date (YYYY-MM-DD)
            date_to: Filter to this date (YYYY-MM-DD)
            transaction_type: Filter by type - "deposit", "payment", "transfer"
            cleared: Filter by cleared status - true/false
            page_size: Results per page
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("bank_account_id"):
            filters.append(f'checkingAccount.id eq "{args["bank_account_id"]}"')
        if args.get("date_from"):
            filters.append(f'transactionDate ge "{args["date_from"]}"')
        if args.get("date_to"):
            filters.append(f'transactionDate le "{args["date_to"]}"')
        if args.get("cleared") is not None:
            filters.append(f'cleared eq {str(args["cleared"]).lower()}')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        transactions = self._paginate("objects/other-receipt", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct bank transactions listed",
            service="sage_intacct",
            count=len(transactions),
            log_event="bank_transactions_listed",
        )

        return {
            "transactions": [self._format_bank_transaction(t) for t in transactions],
            "count": len(transactions),
            "status": "success",
        }

    def create_deposit(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a bank deposit.

        Args:
            bank_account_id: Bank account ID (required)
            deposit_date: Deposit date YYYY-MM-DD (required)
            amount: Deposit amount (required)
            gl_account_no: GL account to credit (required)
            description: Deposit description
            reference_no: Check number or reference
            department_id: Department ID
            location_id: Location ID
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("bank_account_id"):
            raise ValidationError("bank_account_id", "bank_account_id is required")
        if not args.get("deposit_date"):
            raise ValidationError("deposit_date", "deposit_date is required")
        if not args.get("amount"):
            raise ValidationError("amount", "amount is required")
        if not args.get("gl_account_no"):
            raise ValidationError("gl_account_no", "gl_account_no is required")

        deposit_data: dict[str, Any] = {
            "checkingAccount": {"id": args["bank_account_id"]},
            "receiptDate": args["deposit_date"],
            "otherReceiptItem": [
                {
                    "glAccount": {"accountNo": args["gl_account_no"]},
                    "amount": args["amount"],
                }
            ],
        }

        if args.get("description"):
            deposit_data["otherReceiptItem"][0]["memo"] = args["description"]
        if args.get("reference_no"):
            deposit_data["referenceNo"] = args["reference_no"]
        if args.get("department_id"):
            deposit_data["otherReceiptItem"][0]["department"] = {"id": args["department_id"]}
        if args.get("location_id"):
            deposit_data["otherReceiptItem"][0]["location"] = {"id": args["location_id"]}

        result = self._make_api_call("POST", "objects/other-receipt", cred, data=deposit_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct deposit created",
            service="sage_intacct",
            deposit_key=created.get("key"),
            bank_account_id=args["bank_account_id"],
            amount=args["amount"],
            log_event="deposit_created",
        )

        return {
            "deposit": {
                "key": created.get("key"),
                "record_no": created.get("recordNo"),
                "bank_account_id": args["bank_account_id"],
                "date": args["deposit_date"],
                "amount": args["amount"],
            },
            "status": "success",
        }

    def create_bank_transfer(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a bank transfer between accounts.

        Args:
            from_account_id: Source bank account ID (required)
            to_account_id: Destination bank account ID (required)
            transfer_date: Transfer date YYYY-MM-DD (required)
            amount: Transfer amount (required)
            description: Transfer description
            reference_no: Reference number
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("from_account_id"):
            raise ValidationError("from_account_id", "from_account_id is required")
        if not args.get("to_account_id"):
            raise ValidationError("to_account_id", "to_account_id is required")
        if not args.get("transfer_date"):
            raise ValidationError("transfer_date", "transfer_date is required")
        if not args.get("amount"):
            raise ValidationError("amount", "amount is required")

        transfer_data: dict[str, Any] = {
            "fromCheckingAccount": {"id": args["from_account_id"]},
            "toCheckingAccount": {"id": args["to_account_id"]},
            "transferDate": args["transfer_date"],
            "amount": args["amount"],
        }

        if args.get("description"):
            transfer_data["description"] = args["description"]
        if args.get("reference_no"):
            transfer_data["referenceNo"] = args["reference_no"]

        result = self._make_api_call("POST", "objects/fund-transfer", cred, data=transfer_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct bank transfer created",
            service="sage_intacct",
            transfer_key=created.get("key"),
            from_account=args["from_account_id"],
            to_account=args["to_account_id"],
            amount=args["amount"],
            log_event="bank_transfer_created",
        )

        return {
            "transfer": {
                "key": created.get("key"),
                "record_no": created.get("recordNo"),
                "from_account_id": args["from_account_id"],
                "to_account_id": args["to_account_id"],
                "date": args["transfer_date"],
                "amount": args["amount"],
            },
            "status": "success",
        }

    def reconcile_bank_account(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get bank reconciliation data.

        Args:
            bank_account_id: Bank account ID (required)
            statement_date: Statement ending date YYYY-MM-DD (required)
            statement_balance: Statement ending balance (required)
        """
        cred = self._get_access_token(org_id, user_id)

        bank_account_id = args.get("bank_account_id")
        if not bank_account_id:
            raise ValidationError("bank_account_id", "bank_account_id is required")
        if not args.get("statement_date"):
            raise ValidationError("statement_date", "statement_date is required")
        if args.get("statement_balance") is None:
            raise ValidationError("statement_balance", "statement_balance is required")

        params: dict[str, Any] = {
            "accountId": bank_account_id,
            "statementDate": args["statement_date"],
            "statementBalance": args["statement_balance"],
        }

        result = self._make_api_call(
            "GET", "services/cash-management/reconciliation", cred, params=params
        )
        data = result.get("ia::result", {})

        uncleared_items = data.get("unclearedItems", [])

        logger.info(
            "Sage Intacct bank reconciliation retrieved",
            service="sage_intacct",
            bank_account_id=bank_account_id,
            uncleared_count=len(uncleared_items),
            log_event="bank_reconciliation_retrieved",
        )

        return {
            "bank_account_id": bank_account_id,
            "statement_date": args["statement_date"],
            "statement_balance": args["statement_balance"],
            "book_balance": data.get("bookBalance"),
            "adjusted_book_balance": data.get("adjustedBookBalance"),
            "difference": data.get("difference"),
            "uncleared_deposits": data.get("totalUnclearedDeposits"),
            "uncleared_payments": data.get("totalUnclearedPayments"),
            "uncleared_items": [
                {
                    "key": item.get("key"),
                    "type": item.get("transactionType"),
                    "date": item.get("transactionDate"),
                    "reference": item.get("referenceNo"),
                    "amount": item.get("amount"),
                    "description": item.get("description"),
                }
                for item in uncleared_items
            ],
            "uncleared_count": len(uncleared_items),
            "status": "success",
        }

    def mark_transactions_cleared(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Mark bank transactions as cleared.

        Args:
            bank_account_id: Bank account ID (required)
            transaction_keys: List of transaction keys to clear (required)
            clear_date: Date to mark as cleared (YYYY-MM-DD, default today)
        """
        cred = self._get_access_token(org_id, user_id)

        bank_account_id = args.get("bank_account_id")
        if not bank_account_id:
            raise ValidationError("bank_account_id", "bank_account_id is required")
        if not args.get("transaction_keys"):
            raise ValidationError("transaction_keys", "transaction_keys is required")

        clear_data: dict[str, Any] = {
            "checkingAccount": {"id": bank_account_id},
            "items": [{"key": key, "cleared": True} for key in args["transaction_keys"]],
        }

        if args.get("clear_date"):
            clear_data["clearedDate"] = args["clear_date"]

        self._make_api_call("POST", "services/cash-management/mark-cleared", cred, data=clear_data)

        logger.info(
            "Sage Intacct transactions marked cleared",
            service="sage_intacct",
            bank_account_id=bank_account_id,
            cleared_count=len(args["transaction_keys"]),
            log_event="transactions_cleared",
        )

        return {
            "bank_account_id": bank_account_id,
            "cleared_count": len(args["transaction_keys"]),
            "status": "success",
        }

    def get_cash_flow_statement(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get cash flow statement.

        Args:
            start_date: Report start date YYYY-MM-DD (required)
            end_date: Report end date YYYY-MM-DD (required)
            method: "direct" or "indirect" (default "indirect")
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("start_date"):
            raise ValidationError("start_date", "start_date is required")
        if not args.get("end_date"):
            raise ValidationError("end_date", "end_date is required")

        params: dict[str, Any] = {
            "startDate": args["start_date"],
            "endDate": args["end_date"],
            "method": args.get("method", "indirect"),
        }

        result = self._make_api_call(
            "GET", "services/cash-management/cash-flow", cred, params=params
        )
        data = result.get("ia::result", {})

        logger.info(
            "Sage Intacct cash flow statement retrieved",
            service="sage_intacct",
            start_date=args["start_date"],
            end_date=args["end_date"],
            log_event="cash_flow_retrieved",
        )

        return {
            "start_date": args["start_date"],
            "end_date": args["end_date"],
            "method": args.get("method", "indirect"),
            "operating_activities": {
                "net_income": data.get("operatingActivities", {}).get("netIncome"),
                "adjustments": data.get("operatingActivities", {}).get("adjustments"),
                "changes_in_working_capital": data.get("operatingActivities", {}).get(
                    "changesInWorkingCapital"
                ),
                "net_cash_from_operating": data.get("operatingActivities", {}).get("netCash"),
            },
            "investing_activities": {
                "purchases": data.get("investingActivities", {}).get("purchases"),
                "sales": data.get("investingActivities", {}).get("sales"),
                "net_cash_from_investing": data.get("investingActivities", {}).get("netCash"),
            },
            "financing_activities": {
                "debt_proceeds": data.get("financingActivities", {}).get("debtProceeds"),
                "debt_payments": data.get("financingActivities", {}).get("debtPayments"),
                "dividends_paid": data.get("financingActivities", {}).get("dividendsPaid"),
                "net_cash_from_financing": data.get("financingActivities", {}).get("netCash"),
            },
            "net_change_in_cash": data.get("netChangeInCash"),
            "beginning_cash": data.get("beginningCash"),
            "ending_cash": data.get("endingCash"),
            "status": "success",
        }

    def _format_bank_account(self, account: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct bank account for API response."""
        return {
            "key": account.get("key"),
            "account_id": account.get("id"),
            "name": account.get("name"),
            "description": account.get("description"),
            "bank_name": account.get("bankName"),
            "bank_account_no": account.get("bankAccountNo"),
            "routing_no": account.get("routingNo"),
            "account_type": account.get("accountType"),
            "gl_account_no": account.get("glAccount", {}).get("accountNo"),
            "currency": account.get("currency", {}).get("baseCurrency"),
            "status": account.get("status"),
            "current_balance": account.get("currentBalance"),
            "last_reconciled_date": account.get("lastReconciledDate"),
            "last_reconciled_balance": account.get("lastReconciledBalance"),
            "href": account.get("href"),
        }

    def _format_bank_transaction(self, txn: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct bank transaction for API response."""
        return {
            "key": txn.get("key"),
            "record_no": txn.get("recordNo"),
            "transaction_type": txn.get("transactionType"),
            "bank_account_id": txn.get("checkingAccount", {}).get("id"),
            "transaction_date": txn.get("transactionDate") or txn.get("receiptDate"),
            "amount": txn.get("amount") or txn.get("totalAmount"),
            "reference_no": txn.get("referenceNo"),
            "description": txn.get("description"),
            "payee": txn.get("payee", {}).get("name"),
            "cleared": txn.get("cleared", False),
            "cleared_date": txn.get("clearedDate"),
            "state": txn.get("state"),
            "created_date": txn.get("audit", {}).get("createdDateTime"),
        }
