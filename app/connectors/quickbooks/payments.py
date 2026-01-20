"""
QuickBooks Online connector - Payments module
"""

from datetime import datetime
from typing import Any, cast

import requests

from app.http_client import http_client


class QuickBooksPaymentsMixin:
    """QuickBooks payment operations mixin"""

    base_url: str

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        """Get valid access token - implemented in base class"""
        raise NotImplementedError

    def create_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create a payment (customer payment) in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        customer_id = args.get("customer_id", "").replace("qb:", "")

        payment_data: dict[str, Any] = {
            "CustomerRef": {"value": customer_id},
            "TotalAmt": args.get("amount"),
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("invoice_ids"):
            payment_data["Line"] = [
                {
                    "Amount": args["amount"],
                    "LinkedTxn": [{"TxnId": inv_id.replace("qb:", ""), "TxnType": "Invoice"}],
                }
                for inv_id in args["invoice_ids"]
            ]

        url = f"{self.base_url}/{realm_id}/payment"
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

        payment = result.get("Payment", {})
        return {
            "payment_id": f"qb:{payment.get('Id')}",
            "amount": payment.get("TotalAmt"),
            "customer_id": f"qb:{customer_id}",
            "txn_date": payment.get("TxnDate"),
        }

    def get_payment(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get payment details from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        payment_id = args.get("payment_id", "").replace("qb:", "")

        url = f"{self.base_url}/{realm_id}/payment/{payment_id}"
        result = http_client.get(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
            },
        )

        payment = result.get("Payment", {})
        return {
            "payment_id": f"qb:{payment.get('Id')}",
            "amount": payment.get("TotalAmt"),
            "customer_id": f"qb:{payment.get('CustomerRef', {}).get('value')}",
            "txn_date": payment.get("TxnDate"),
        }

    def list_payments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List customer payments from QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        query = "SELECT * FROM Payment"
        if args.get("customer_id"):
            customer_id = args["customer_id"].replace("qb:", "")
            query += f" WHERE CustomerRef = '{customer_id}'"
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

        payments = result.get("QueryResponse", {}).get("Payment", [])
        return {
            "payments": [
                {
                    "payment_id": f"qb:{p.get('Id')}",
                    "amount": p.get("TotalAmt"),
                    "customer": p.get("CustomerRef", {}).get("name"),
                    "txn_date": p.get("TxnDate"),
                }
                for p in payments
            ],
            "count": len(payments),
        }

    def _get_payment_method_ref(self, payment_method: str) -> str:
        """Map payment method to QuickBooks PaymentMethod reference ID"""
        method_map = {
            "check": "1",
            "cash": "2",
            "credit_card": "4",
            "bank_transfer": "5",
            "debit_card": "6",
        }
        return method_map.get(payment_method.lower(), "1")

    def apply_payment_to_invoice(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply payment to specific invoice(s)"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]

        customer_id = args.get("customer_id", "").replace("qb:", "")
        invoice_allocations = args.get("invoice_allocations", [])
        payment_method = args.get("payment_method", "check")
        reference = args.get("reference")
        txn_date = args.get("txn_date", datetime.now().strftime("%Y-%m-%d"))

        if not customer_id:
            raise ValueError("customer_id is required")
        if not invoice_allocations:
            raise ValueError("invoice_allocations is required")

        line_items = []
        total_amount = 0.0
        for alloc in invoice_allocations:
            invoice_id = alloc.get("invoice_id", "").replace("qb:", "")
            amount = alloc.get("amount", 0.0)
            if invoice_id and amount > 0:
                total_amount += amount
                line_items.append(
                    {
                        "Amount": amount,
                        "LinkedTxn": [{"TxnId": invoice_id, "TxnType": "Invoice"}],
                    }
                )

        payment_data: dict[str, Any] = {
            "CustomerRef": {"value": customer_id},
            "TotalAmt": total_amount,
            "TxnDate": txn_date,
            "Line": line_items,
        }

        method_ref = self._get_payment_method_ref(payment_method)
        if method_ref:
            payment_data["PaymentMethodRef"] = {"value": method_ref}
        if reference:
            payment_data["PrivateNote"] = reference

        raw_response = http_client.post(
            url=f"{self.base_url}/{realm_id}/payment",
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payment_data,
            timeout=(5, 30),
            parse_json=False,
        )
        response = cast(requests.Response, raw_response)

        if response.status_code == 200:
            payment = response.json().get("Payment", {})
            return {
                "payment_id": f"qb:{payment['Id']}",
                "customer_id": f"qb:{customer_id}",
                "total_amount": total_amount,
                "invoice_allocations": [
                    {
                        "invoice_id": f"qb:{a['invoice_id'].replace('qb:', '')}",
                        "amount_applied": a["amount"],
                    }
                    for a in invoice_allocations
                ],
                "status": "applied",
            }

        error_body = (
            response.json() if "json" in response.headers.get("content-type", "") else response.text
        )
        raise Exception(f"QuickBooks API error ({response.status_code}): {error_body}")

    def create_refund_receipt(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a refund receipt in QuickBooks"""
        cred = self._get_access_token(org_id, user_id)
        realm_id = cred["realm_id"]
        customer_id = args.get("customer_id", "").replace("qb:", "")

        refund_data: dict[str, Any] = {
            "CustomerRef": {"value": customer_id},
            "TxnDate": args.get("txn_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if args.get("line_items"):
            refund_data["Line"] = args["line_items"]

        if args.get("deposit_account_id"):
            refund_data["DepositToAccountRef"] = {
                "value": args["deposit_account_id"].replace("qb:", "")
            }

        if args.get("memo"):
            refund_data["PrivateNote"] = args["memo"]

        if args.get("payment_method_id"):
            refund_data["PaymentMethodRef"] = {
                "value": args["payment_method_id"].replace("qb:", "")
            }

        url = f"{self.base_url}/{realm_id}/refundreceipt"
        result = http_client.post(
            url=url,
            service="quickbooks",
            headers={
                "Authorization": f"Bearer {cred['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=refund_data,
        )

        refund = result.get("RefundReceipt", {})
        return {
            "refund_receipt_id": f"qb:{refund.get('Id')}",
            "customer_id": f"qb:{customer_id}",
            "total_amount": refund.get("TotalAmt"),
            "txn_date": refund.get("TxnDate"),
        }
