"""
QuickBooks Online connector - Bills and Payables module
"""

from datetime import datetime
from typing import Any

from app.connectors.quickbooks import deep_links
from app.http_client import http_client


class QuickBooksBillsMixin:
    """QuickBooks bill and payables operations mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def create_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a bill in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        vendor_id = args.get("vendor_id", "").replace("qb:", "")

        bill_data: dict[str, Any] = {
            "VendorRef": {"value": vendor_id},
            "Line": args.get("line_items", []),
            "DueDate": args.get("due_date"),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        url = f"{self.base_url}/{realm_id}/bill"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=bill_data,
        )

        bill = result.get("Bill", {})
        bill_id = bill.get("Id")
        return {
            "bill_id": f"qb:{bill_id}",
            "doc_number": bill.get("DocNumber"),
            "total_amount": bill.get("TotalAmt"),
            "due_date": bill.get("DueDate"),
            "status": "open",
            "deep_link": deep_links.bill_link(bill_id),
        }

    def get_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get bill details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        bill_id = args.get("bill_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/bill/{bill_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        bill = result.get("Bill", {})
        bid = bill.get("Id")
        return {
            "bill_id": f"qb:{bid}",
            "doc_number": bill.get("DocNumber"),
            "total_amount": bill.get("TotalAmt"),
            "due_date": bill.get("DueDate"),
            "balance": bill.get("Balance"),
            "vendor_id": f"qb:{bill.get('VendorRef', {}).get('value')}",
            "deep_link": deep_links.bill_link(bid),
        }

    def list_bills(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List bills from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Bill"
        conditions = []
        if args.get("vendor_id"):
            vendor_id = args["vendor_id"].replace("qb:", "")
            conditions.append(f"VendorRef = '{vendor_id}'")
        if args.get("unpaid_only"):
            conditions.append("Balance > 0")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
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

        bills = result.get("QueryResponse", {}).get("Bill", [])
        return {
            "bills": [
                {
                    "bill_id": f"qb:{b.get('Id')}",
                    "doc_number": b.get("DocNumber"),
                    "total_amount": b.get("TotalAmt"),
                    "balance": b.get("Balance"),
                    "due_date": b.get("DueDate"),
                    "vendor": b.get("VendorRef", {}).get("name"),
                    "deep_link": deep_links.bill_link(b.get("Id")),
                }
                for b in bills
            ],
            "count": len(bills),
        }

    def create_bill_payment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a bill payment in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        vendor_id = args.get("vendor_id", "").replace("qb:", "")

        payment_data: dict[str, Any] = {
            "VendorRef": {"value": vendor_id},
            "TotalAmt": args.get("amount"),
            "PayType": args.get("payment_type", "Check"),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("check_num"):
            payment_data["CheckNum"] = args["check_num"]

        if args.get("bill_ids"):
            payment_data["Line"] = [
                {
                    "Amount": args["amount"],
                    "LinkedTxn": [{"TxnId": bid.replace("qb:", ""), "TxnType": "Bill"}],
                }
                for bid in args["bill_ids"]
            ]

        url = f"{self.base_url}/{realm_id}/billpayment"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payment_data,
        )

        payment = result.get("BillPayment", {})
        payment_id = payment.get("Id")
        return {
            "payment_id": f"qb:{payment_id}",
            "amount": payment.get("TotalAmt"),
            "pay_type": payment.get("PayType"),
            "txn_date": payment.get("TxnDate"),
            "deep_link": deep_links.bill_payment_link(payment_id),
        }

    def list_bill_payments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List bill payments from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM BillPayment"
        if args.get("vendor_id"):
            vendor_id = args["vendor_id"].replace("qb:", "")
            query += f" WHERE VendorRef = '{vendor_id}'"
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

        payments = result.get("QueryResponse", {}).get("BillPayment", [])
        return {
            "payments": [
                {
                    "payment_id": f"qb:{p.get('Id')}",
                    "amount": p.get("TotalAmt"),
                    "pay_type": p.get("PayType"),
                    "txn_date": p.get("TxnDate"),
                    "vendor": p.get("VendorRef", {}).get("name"),
                    "deep_link": deep_links.bill_payment_link(p.get("Id")),
                }
                for p in payments
            ],
            "count": len(payments),
        }

    def create_expense(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an expense in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        expense_data: dict[str, Any] = {
            "PaymentType": args.get("payment_type", "Cash"),
            "Line": args.get("line_items", []),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("vendor_id"):
            expense_data["EntityRef"] = {
                "value": args["vendor_id"].replace("qb:", ""),
                "type": "Vendor",
            }
        if args.get("account_ref"):
            expense_data["AccountRef"] = {"value": args["account_ref"]}

        url = f"{self.base_url}/{realm_id}/purchase"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=expense_data,
        )

        expense = result.get("Purchase", {})
        expense_id = expense.get("Id")
        return {
            "expense_id": f"qb:{expense_id}",
            "total_amount": expense.get("TotalAmt"),
            "payment_type": expense.get("PaymentType"),
            "deep_link": deep_links.expense_link(expense_id),
        }

    def create_purchase_order(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a purchase order in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        vendor_id = args.get("vendor_id", "").replace("qb:", "")

        po_data: dict[str, Any] = {
            "VendorRef": {"value": vendor_id},
            "Line": args.get("line_items", []),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("ship_address"):
            po_data["ShipAddr"] = args["ship_address"]

        url = f"{self.base_url}/{realm_id}/purchaseorder"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=po_data,
        )

        po = result.get("PurchaseOrder", {})
        po_id = po.get("Id")
        return {
            "purchase_order_id": f"qb:{po_id}",
            "doc_number": po.get("DocNumber"),
            "total_amount": po.get("TotalAmt"),
            "vendor_id": f"qb:{vendor_id}",
            "deep_link": deep_links.purchase_order_link(po_id),
        }

    def get_purchase_order(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get purchase order details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        po_id = args.get("purchase_order_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/purchaseorder/{po_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        po = result.get("PurchaseOrder", {})
        po_id = po.get("Id")
        return {
            "purchase_order_id": f"qb:{po_id}",
            "doc_number": po.get("DocNumber"),
            "total_amount": po.get("TotalAmt"),
            "due_date": po.get("DueDate"),
            "txn_date": po.get("TxnDate"),
            "vendor_id": f"qb:{po.get('VendorRef', {}).get('value')}",
            "vendor_name": po.get("VendorRef", {}).get("name"),
            "status": po.get("POStatus", "Open"),
            "line_items": [
                {
                    "description": line.get("Description"),
                    "amount": line.get("Amount"),
                    "item_id": line.get("ItemBasedExpenseLineDetail", {})
                    .get("ItemRef", {})
                    .get("value"),
                    "quantity": line.get("ItemBasedExpenseLineDetail", {}).get("Qty"),
                    "unit_price": line.get("ItemBasedExpenseLineDetail", {}).get("UnitPrice"),
                }
                for line in po.get("Line", [])
                if line.get("DetailType") in ("ItemBasedExpenseLineDetail", None)
            ],
            "deep_link": deep_links.purchase_order_link(po_id),
        }

    def list_purchase_orders(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """List purchase orders from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM PurchaseOrder"
        conditions = []
        if args.get("vendor_id"):
            vendor_id = args["vendor_id"].replace("qb:", "")
            conditions.append(f"VendorRef = '{vendor_id}'")
        if args.get("status"):
            conditions.append(f"POStatus = '{args['status']}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
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

        pos = result.get("QueryResponse", {}).get("PurchaseOrder", [])
        return {
            "purchase_orders": [
                {
                    "purchase_order_id": f"qb:{p.get('Id')}",
                    "doc_number": p.get("DocNumber"),
                    "total_amount": p.get("TotalAmt"),
                    "due_date": p.get("DueDate"),
                    "txn_date": p.get("TxnDate"),
                    "vendor_id": f"qb:{p.get('VendorRef', {}).get('value')}",
                    "vendor_name": p.get("VendorRef", {}).get("name"),
                    "status": p.get("POStatus", "Open"),
                    "deep_link": deep_links.purchase_order_link(p.get("Id")),
                }
                for p in pos
            ],
            "count": len(pos),
        }
