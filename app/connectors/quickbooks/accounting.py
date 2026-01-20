"""
QuickBooks Online connector - Accounting module (Journal entries, Chart of Accounts, etc.)
"""

from datetime import datetime
from typing import Any

from app.http_client import http_client


class QuickBooksAccountingMixin:
    """QuickBooks accounting operations mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def create_journal_entry(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a journal entry in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        journal_data: dict[str, Any] = {
            "Line": args.get("lines"),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
            "PrivateNote": args.get("memo", ""),
        }

        if args.get("doc_number"):
            journal_data["DocNumber"] = args["doc_number"]

        url = f"{self.base_url}/{realm_id}/journalentry"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=journal_data,
        )

        je = result.get("JournalEntry", {})
        return {
            "journal_entry_id": f"qb:{je.get('Id')}",
            "doc_number": je.get("DocNumber"),
            "txn_date": je.get("TxnDate"),
            "total_amount": je.get("TotalAmt"),
            "memo": je.get("PrivateNote"),
        }

    def get_chart_of_accounts(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get chart of accounts from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Account"
        if args.get("account_type"):
            query += f" WHERE AccountType = '{args['account_type']}'"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        accounts = result.get("QueryResponse", {}).get("Account", [])
        return {
            "accounts": [
                {
                    "account_id": f"qb:{acc.get('Id')}",
                    "name": acc.get("Name"),
                    "type": acc.get("AccountType"),
                    "number": acc.get("AcctNum"),
                    "balance": acc.get("CurrentBalance", 0),
                }
                for acc in accounts
            ],
            "count": len(accounts),
        }

    def list_classes(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List classes from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Class"
        if args.get("active_only"):
            query += " WHERE Active = true"
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        classes = result.get("QueryResponse", {}).get("Class", [])
        return {
            "classes": [
                {
                    "class_id": f"qb:{c.get('Id')}",
                    "name": c.get("Name"),
                    "fully_qualified_name": c.get("FullyQualifiedName"),
                    "active": c.get("Active"),
                }
                for c in classes
            ],
            "count": len(classes),
        }

    def list_departments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List departments from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Department"
        if args.get("active_only"):
            query += " WHERE Active = true"
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        depts = result.get("QueryResponse", {}).get("Department", [])
        return {
            "departments": [
                {
                    "department_id": f"qb:{d.get('Id')}",
                    "name": d.get("Name"),
                    "fully_qualified_name": d.get("FullyQualifiedName"),
                    "active": d.get("Active"),
                }
                for d in depts
            ],
            "count": len(depts),
        }

    def list_employees(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List employees from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Employee"
        if args.get("active_only"):
            query += " WHERE Active = true"
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        employees = result.get("QueryResponse", {}).get("Employee", [])
        return {
            "employees": [
                {
                    "employee_id": f"qb:{e.get('Id')}",
                    "display_name": e.get("DisplayName"),
                    "given_name": e.get("GivenName"),
                    "family_name": e.get("FamilyName"),
                    "email": e.get("PrimaryEmailAddr", {}).get("Address"),
                    "active": e.get("Active"),
                }
                for e in employees
            ],
            "count": len(employees),
        }

    def get_employee(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get employee details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        employee_id = args.get("employee_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/employee/{employee_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        emp = result.get("Employee", {})
        return {
            "employee_id": f"qb:{emp.get('Id')}",
            "display_name": emp.get("DisplayName"),
            "given_name": emp.get("GivenName"),
            "family_name": emp.get("FamilyName"),
            "email": emp.get("PrimaryEmailAddr", {}).get("Address"),
            "phone": emp.get("PrimaryPhone", {}).get("FreeFormNumber"),
            "hired_date": emp.get("HiredDate"),
            "active": emp.get("Active"),
        }

    def create_deposit(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a deposit in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        deposit_data: dict[str, Any] = {
            "DepositToAccountRef": {"value": args.get("deposit_account_id", "").replace("qb:", "")},
            "Line": args.get("line_items", []),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("memo"):
            deposit_data["PrivateNote"] = args["memo"]

        url = f"{self.base_url}/{realm_id}/deposit"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=deposit_data,
        )

        deposit = result.get("Deposit", {})
        return {
            "deposit_id": f"qb:{deposit.get('Id')}",
            "total_amount": deposit.get("TotalAmt"),
            "txn_date": deposit.get("TxnDate"),
        }

    def create_time_activity(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a time activity in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        time_data: dict[str, Any] = {
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
            "NameOf": args.get("name_of", "Employee"),
            "Hours": args.get("hours"),
            "Minutes": args.get("minutes", 0),
        }

        if args.get("employee_id"):
            time_data["EmployeeRef"] = {"value": args["employee_id"].replace("qb:", "")}
        if args.get("customer_id"):
            time_data["CustomerRef"] = {"value": args["customer_id"].replace("qb:", "")}
        if args.get("item_id"):
            time_data["ItemRef"] = {"value": args["item_id"].replace("qb:", "")}
        if args.get("description"):
            time_data["Description"] = args["description"]
        if args.get("billable"):
            time_data["BillableStatus"] = "Billable"

        url = f"{self.base_url}/{realm_id}/timeactivity"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=time_data,
        )

        time_activity = result.get("TimeActivity", {})
        return {
            "time_activity_id": f"qb:{time_activity.get('Id')}",
            "hours": time_activity.get("Hours"),
            "minutes": time_activity.get("Minutes"),
            "txn_date": time_activity.get("TxnDate"),
        }

    def create_transfer(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create account-to-account transfer in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        transfer_data: dict[str, Any] = {
            "FromAccountRef": {"value": args.get("from_account_id", "").replace("qb:", "")},
            "ToAccountRef": {"value": args.get("to_account_id", "").replace("qb:", "")},
            "Amount": args.get("amount"),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("memo"):
            transfer_data["PrivateNote"] = args["memo"]

        url = f"{self.base_url}/{realm_id}/transfer"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=transfer_data,
        )

        transfer = result.get("Transfer", {})
        return {
            "transfer_id": f"qb:{transfer.get('Id')}",
            "amount": transfer.get("Amount"),
            "from_account": transfer.get("FromAccountRef", {}).get("name"),
            "to_account": transfer.get("ToAccountRef", {}).get("name"),
            "txn_date": transfer.get("TxnDate"),
        }

    def get_account(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get single account details with balance"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        account_id = args.get("account_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/account/{account_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        acc = result.get("Account", {})
        return {
            "account_id": f"qb:{acc.get('Id')}",
            "name": acc.get("Name"),
            "type": acc.get("AccountType"),
            "sub_type": acc.get("AccountSubType"),
            "number": acc.get("AcctNum"),
            "balance": acc.get("CurrentBalance", 0),
            "active": acc.get("Active"),
        }

    def list_terms(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List payment terms from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Term"
        if args.get("active_only"):
            query += " WHERE Active = true"
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        terms = result.get("QueryResponse", {}).get("Term", [])
        return {
            "terms": [
                {
                    "term_id": f"qb:{t.get('Id')}",
                    "name": t.get("Name"),
                    "due_days": t.get("DueDays"),
                    "discount_percent": t.get("DiscountPercent"),
                    "discount_days": t.get("DiscountDays"),
                    "active": t.get("Active"),
                }
                for t in terms
            ],
            "count": len(terms),
        }

    def list_tax_codes(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List tax codes from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM TaxCode"
        if args.get("active_only"):
            query += " WHERE Active = true"
        query += f" MAXRESULTS {args.get('limit', 100)}"

        url = f"{self.base_url}/{realm_id}/query?query={query}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        tax_codes = result.get("QueryResponse", {}).get("TaxCode", [])
        return {
            "tax_codes": [
                {
                    "tax_code_id": f"qb:{tc.get('Id')}",
                    "name": tc.get("Name"),
                    "description": tc.get("Description"),
                    "taxable": tc.get("Taxable"),
                    "active": tc.get("Active"),
                }
                for tc in tax_codes
            ],
            "count": len(tax_codes),
        }

    def get_company_info(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get company information from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        url = f"{self.base_url}/{realm_id}/companyinfo/{realm_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        info = result.get("CompanyInfo", {})
        return {
            "company_name": info.get("CompanyName"),
            "legal_name": info.get("LegalName"),
            "company_addr": info.get("CompanyAddr"),
            "email": info.get("Email", {}).get("Address"),
            "phone": info.get("PrimaryPhone", {}).get("FreeFormNumber"),
            "fiscal_year_start": info.get("FiscalYearStartMonth"),
            "country": info.get("Country"),
        }
