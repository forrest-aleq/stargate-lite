"""
Xero Bank Transactions connector - Bank account and transaction management.

Reference: https://developer.xero.com/documentation/api/accounting/banktransactions

Bank Transactions in Xero:
- RECEIVE: Money in (deposits)
- RECEIVE-OVERPAYMENT: Customer overpayment
- RECEIVE-PREPAYMENT: Customer prepayment
- SPEND: Money out (expenses)
- SPEND-OVERPAYMENT: Supplier overpayment
- SPEND-PREPAYMENT: Supplier prepayment

Bank accounts are managed via the Accounts endpoint with type BANK.
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .credit_notes import CreditNotesMixin

logger = get_logger(__name__)


class BankMixin(CreditNotesMixin):
    """Mixin providing bank account and transaction management capabilities."""

    def list_bank_accounts(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List all bank accounts.

        Args:
            include_archived: Include archived accounts (default False)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        where_clauses: list[str] = ['Type=="BANK"']

        if not args.get("include_archived", False):
            where_clauses.append('Status!="ARCHIVED"')

        params = {"where": " AND ".join(where_clauses)}

        result = self._make_api_call("GET", "Accounts", cred, tenant_id, params=params)
        accounts = result.get("Accounts", [])

        logger.info(
            "Xero bank accounts listed",
            service="xero",
            count=len(accounts),
            log_event="bank_accounts_listed",
        )

        return {
            "accounts": [self._format_bank_account(acct) for acct in accounts],
            "count": len(accounts),
            "status": "success",
        }

    def get_bank_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific bank account.

        Args:
            account_id: Xero AccountID (UUID)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        account_id = args.get("account_id")
        if not account_id:
            raise ValidationError("account_id", "account_id is required")

        result = self._make_api_call("GET", f"Accounts/{account_id}", cred, tenant_id)
        accounts = result.get("Accounts", [])

        if not accounts:
            return {"account": None, "status": "not_found"}

        account = accounts[0]
        if account.get("Type") != "BANK":
            return {"account": None, "status": "not_bank_account"}

        return {"account": self._format_bank_account(account), "status": "success"}

    def list_bank_transactions(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List bank transactions with optional filtering.

        Args:
            where: Filter expression
            order: Sort field
            page: Page number (1-indexed)
            bank_account_id: Filter by bank account
            transaction_type: Filter by type (SPEND, RECEIVE, etc.)
            date_from: Filter from this date
            date_to: Filter to this date
            status: Filter by status - AUTHORISED or DELETED
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}
        where_clauses: list[str] = []

        if args.get("where"):
            where_clauses.append(args["where"])

        if args.get("bank_account_id"):
            where_clauses.append(f'BankAccount.AccountID==GUID("{args["bank_account_id"]}")')

        if args.get("transaction_type"):
            where_clauses.append(f'Type=="{args["transaction_type"]}"')

        if args.get("status"):
            where_clauses.append(f'Status=="{args["status"]}"')

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

        result = self._make_api_call("GET", "BankTransactions", cred, tenant_id, params=params)
        transactions = result.get("BankTransactions", [])

        logger.info(
            "Xero bank transactions listed",
            service="xero",
            count=len(transactions),
            page=page,
            log_event="bank_transactions_listed",
        )

        return {
            "transactions": [self._format_bank_transaction(txn) for txn in transactions],
            "count": len(transactions),
            "page": page,
            "status": "success",
        }

    def get_bank_transaction(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get a specific bank transaction.

        Args:
            transaction_id: Xero BankTransactionID (UUID)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        transaction_id = args.get("transaction_id")
        if not transaction_id:
            raise ValidationError("transaction_id", "transaction_id is required")

        result = self._make_api_call("GET", f"BankTransactions/{transaction_id}", cred, tenant_id)
        transactions = result.get("BankTransactions", [])

        if not transactions:
            return {"transaction": None, "status": "not_found"}

        return {
            "transaction": self._format_bank_transaction(transactions[0]),
            "status": "success",
        }

    def create_bank_transaction(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a bank transaction (spend or receive).

        Args:
            bank_account_id: Bank account ID (required)
            type: Transaction type (required) - SPEND or RECEIVE
            line_items: List of line items (required)
                - description: Description
                - quantity: Quantity
                - unit_amount: Unit amount
                - account_code: GL account code
                - tax_type: Tax type
            contact_id: Optional contact
            date: Transaction date (YYYY-MM-DD)
            reference: Reference
            is_reconciled: Mark as reconciled
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("bank_account_id"):
            raise ValidationError("bank_account_id", "bank_account_id is required")
        if not args.get("type"):
            raise ValidationError("type", "type (SPEND or RECEIVE) is required")
        if not args.get("line_items"):
            raise ValidationError("line_items", "At least one line item is required")

        txn_type = args["type"].upper()
        if txn_type not in ["SPEND", "RECEIVE"]:
            raise ValidationError("type", "type must be SPEND or RECEIVE")

        txn_data: dict[str, Any] = {
            "Type": txn_type,
            "BankAccount": {"AccountID": args["bank_account_id"]},
            "LineItems": self._format_bank_txn_line_items(args["line_items"]),
        }

        if args.get("contact_id"):
            txn_data["Contact"] = {"ContactID": args["contact_id"]}
        if args.get("date"):
            txn_data["Date"] = args["date"]
        if args.get("reference"):
            txn_data["Reference"] = args["reference"]
        if args.get("is_reconciled") is not None:
            txn_data["IsReconciled"] = args["is_reconciled"]

        result = self._make_api_call(
            "POST", "BankTransactions", cred, tenant_id, data={"BankTransactions": [txn_data]}
        )

        created = result.get("BankTransactions", [])[0] if result.get("BankTransactions") else {}

        logger.info(
            "Xero bank transaction created",
            service="xero",
            transaction_id=created.get("BankTransactionID"),
            type=txn_type,
            total=created.get("Total"),
            log_event="bank_transaction_created",
        )

        return {"transaction": self._format_bank_transaction(created), "status": "success"}

    def create_spend_transaction(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a spend (money out) transaction.

        Convenience method that sets type=SPEND.

        Args:
            bank_account_id: Bank account ID (required)
            line_items: List of line items (required)
            contact_id: Optional supplier contact
            date: Transaction date
            reference: Reference
        """
        args["type"] = "SPEND"
        return self.create_bank_transaction(org_id, user_id, args)

    def create_receive_transaction(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a receive (money in) transaction.

        Convenience method that sets type=RECEIVE.

        Args:
            bank_account_id: Bank account ID (required)
            line_items: List of line items (required)
            contact_id: Optional customer contact
            date: Transaction date
            reference: Reference
        """
        args["type"] = "RECEIVE"
        return self.create_bank_transaction(org_id, user_id, args)

    def delete_bank_transaction(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Delete a bank transaction.

        Args:
            transaction_id: BankTransactionID
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        transaction_id = args.get("transaction_id")
        if not transaction_id:
            raise ValidationError("transaction_id", "transaction_id is required")

        txn_data = {"BankTransactionID": transaction_id, "Status": "DELETED"}

        self._make_api_call(
            "POST",
            f"BankTransactions/{transaction_id}",
            cred,
            tenant_id,
            data={"BankTransactions": [txn_data]},
        )

        logger.info(
            "Xero bank transaction deleted",
            service="xero",
            transaction_id=transaction_id,
            log_event="bank_transaction_deleted",
        )

        return {"transaction_id": transaction_id, "status": "deleted"}

    def get_bank_statement(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get bank statement lines from a bank account.

        Args:
            bank_account_id: Bank account ID (required)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        bank_account_id = args.get("bank_account_id")
        if not bank_account_id:
            raise ValidationError("bank_account_id", "bank_account_id is required")

        params: dict[str, Any] = {"BankAccountID": bank_account_id}

        if args.get("date_from"):
            params["DateFrom"] = args["date_from"]
        if args.get("date_to"):
            params["DateTo"] = args["date_to"]

        result = self._make_api_call("GET", "BankStatements", cred, tenant_id, params=params)
        statements = result.get("BankStatements", [])

        # Flatten statement lines
        all_lines: list[dict[str, Any]] = []
        for stmt in statements:
            all_lines.extend(
                {
                    "date": line.get("Date"),
                    "description": line.get("Description"),
                    "amount": line.get("Amount"),
                    "transaction_id": line.get("TransactionId"),
                    "payee": line.get("Payee"),
                    "reference": line.get("Reference"),
                    "cheque_number": line.get("ChequeNumber"),
                }
                for line in stmt.get("StatementLines", [])
            )

        logger.info(
            "Xero bank statement retrieved",
            service="xero",
            bank_account_id=bank_account_id,
            line_count=len(all_lines),
            log_event="bank_statement_retrieved",
        )

        return {
            "bank_account_id": bank_account_id,
            "lines": all_lines,
            "count": len(all_lines),
            "status": "success",
        }

    def get_bank_transfers(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List bank transfers between accounts.

        Args:
            date_from: Filter from this date
            date_to: Filter to this date
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        params: dict[str, Any] = {}
        where_clauses: list[str] = []

        if args.get("date_from"):
            where_clauses.append(f'Date>=DateTime({args["date_from"].replace("-", ",")})')
        if args.get("date_to"):
            where_clauses.append(f'Date<=DateTime({args["date_to"].replace("-", ",")})')

        if where_clauses:
            params["where"] = " AND ".join(where_clauses)

        result = self._make_api_call("GET", "BankTransfers", cred, tenant_id, params=params)
        transfers = result.get("BankTransfers", [])

        logger.info(
            "Xero bank transfers listed",
            service="xero",
            count=len(transfers),
            log_event="bank_transfers_listed",
        )

        return {
            "transfers": [
                {
                    "transfer_id": t.get("BankTransferID"),
                    "date": t.get("Date"),
                    "amount": t.get("Amount"),
                    "from_bank_account": {
                        "account_id": t.get("FromBankAccount", {}).get("AccountID"),
                        "name": t.get("FromBankAccount", {}).get("Name"),
                    },
                    "to_bank_account": {
                        "account_id": t.get("ToBankAccount", {}).get("AccountID"),
                        "name": t.get("ToBankAccount", {}).get("Name"),
                    },
                }
                for t in transfers
            ],
            "count": len(transfers),
            "status": "success",
        }

    def create_bank_transfer(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a bank transfer between accounts.

        Args:
            from_bank_account_id: Source bank account (required)
            to_bank_account_id: Destination bank account (required)
            amount: Transfer amount (required)
            date: Transfer date (YYYY-MM-DD)
        """
        cred = self._get_access_token(org_id, user_id)
        tenant_id = self._get_tenant_id(cred, org_id, user_id)

        if not args.get("from_bank_account_id"):
            raise ValidationError("from_bank_account_id", "from_bank_account_id is required")
        if not args.get("to_bank_account_id"):
            raise ValidationError("to_bank_account_id", "to_bank_account_id is required")
        if args.get("amount") is None:
            raise ValidationError("amount", "amount is required")

        transfer_data: dict[str, Any] = {
            "FromBankAccount": {"AccountID": args["from_bank_account_id"]},
            "ToBankAccount": {"AccountID": args["to_bank_account_id"]},
            "Amount": args["amount"],
        }

        if args.get("date"):
            transfer_data["Date"] = args["date"]

        result = self._make_api_call(
            "POST",
            "BankTransfers",
            cred,
            tenant_id,
            data={"BankTransfers": [transfer_data]},
        )

        created = result.get("BankTransfers", [])[0] if result.get("BankTransfers") else {}

        logger.info(
            "Xero bank transfer created",
            service="xero",
            transfer_id=created.get("BankTransferID"),
            amount=args["amount"],
            log_event="bank_transfer_created",
        )

        return {
            "transfer": {
                "transfer_id": created.get("BankTransferID"),
                "date": created.get("Date"),
                "amount": created.get("Amount"),
                "from_bank_account": {
                    "account_id": created.get("FromBankAccount", {}).get("AccountID"),
                    "name": created.get("FromBankAccount", {}).get("Name"),
                },
                "to_bank_account": {
                    "account_id": created.get("ToBankAccount", {}).get("AccountID"),
                    "name": created.get("ToBankAccount", {}).get("Name"),
                },
            },
            "status": "success",
        }

    def _format_bank_account(self, account: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero bank account for API response."""
        return {
            "account_id": account.get("AccountID"),
            "code": account.get("Code"),
            "name": account.get("Name"),
            "status": account.get("Status"),
            "bank_account_number": account.get("BankAccountNumber"),
            "bank_account_type": account.get("BankAccountType"),
            "currency_code": account.get("CurrencyCode"),
            "description": account.get("Description"),
            "updated_date": account.get("UpdatedDateUTC"),
        }

    def _format_bank_transaction(self, txn: dict[str, Any]) -> dict[str, Any]:
        """Format a Xero bank transaction for API response."""
        contact = txn.get("Contact", {})
        bank_account = txn.get("BankAccount", {})
        line_items = txn.get("LineItems", [])

        return {
            "transaction_id": txn.get("BankTransactionID"),
            "type": txn.get("Type"),
            "status": txn.get("Status"),
            "date": txn.get("Date"),
            "reference": txn.get("Reference"),
            "is_reconciled": txn.get("IsReconciled", False),
            "currency_code": txn.get("CurrencyCode"),
            "currency_rate": txn.get("CurrencyRate"),
            "sub_total": txn.get("SubTotal"),
            "total_tax": txn.get("TotalTax"),
            "total": txn.get("Total"),
            "contact": {
                "contact_id": contact.get("ContactID"),
                "name": contact.get("Name"),
            }
            if contact
            else None,
            "bank_account": {
                "account_id": bank_account.get("AccountID"),
                "code": bank_account.get("Code"),
                "name": bank_account.get("Name"),
            },
            "line_items": [
                {
                    "line_item_id": li.get("LineItemID"),
                    "description": li.get("Description"),
                    "quantity": li.get("Quantity"),
                    "unit_amount": li.get("UnitAmount"),
                    "account_code": li.get("AccountCode"),
                    "tax_type": li.get("TaxType"),
                    "tax_amount": li.get("TaxAmount"),
                    "line_amount": li.get("LineAmount"),
                }
                for li in line_items
            ],
            "updated_date": txn.get("UpdatedDateUTC"),
        }

    def _format_bank_txn_line_items(self, line_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format line items for bank transaction API request."""
        formatted: list[dict[str, Any]] = []
        for li in line_items:
            xero_li: dict[str, Any] = {}

            if li.get("description"):
                xero_li["Description"] = li["description"]
            if li.get("quantity") is not None:
                xero_li["Quantity"] = li["quantity"]
            else:
                xero_li["Quantity"] = 1
            if li.get("unit_amount") is not None:
                xero_li["UnitAmount"] = li["unit_amount"]
            if li.get("account_code"):
                xero_li["AccountCode"] = li["account_code"]
            if li.get("tax_type"):
                xero_li["TaxType"] = li["tax_type"]

            formatted.append(xero_li)
        return formatted
