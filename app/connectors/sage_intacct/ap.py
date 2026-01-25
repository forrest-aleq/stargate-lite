"""
Sage Intacct Accounts Payable connector.

Reference: https://developer.sage.com/intacct/docs/

Provides:
- Bills (AP Bills)
- Bill payments
- AP aging
"""

from typing import Any

from app.errors import ValidationError
from app.logging_config import get_logger

from .vendors import VendorMixin

logger = get_logger(__name__)


class APMixin(VendorMixin):
    """Mixin providing Accounts Payable capabilities."""

    def list_bills(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List AP bills.

        Args:
            vendor_id: Filter by vendor
            status: Filter by status - "open", "paid", "partialPaid"
            date_from: Filter from this date (YYYY-MM-DD)
            date_to: Filter to this date (YYYY-MM-DD)
            page_size: Results per page
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("vendor_id"):
            filters.append(f'vendor.id eq "{args["vendor_id"]}"')
        if args.get("status"):
            filters.append(f'paymentStatus eq "{args["status"]}"')
        if args.get("date_from"):
            filters.append(f'createdDate ge "{args["date_from"]}"')
        if args.get("date_to"):
            filters.append(f'createdDate le "{args["date_to"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        bills = self._paginate("objects/ap-bill", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct bills listed",
            service="sage_intacct",
            count=len(bills),
            log_event="bills_listed",
        )

        return {
            "bills": [self._format_bill(b) for b in bills],
            "count": len(bills),
            "status": "success",
        }

    def get_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific AP bill.

        Args:
            bill_key: Bill key (required)
        """
        cred = self._get_access_token(org_id, user_id)

        bill_key = args.get("bill_key")
        if not bill_key:
            raise ValidationError("bill_key", "bill_key is required")

        result = self._make_api_call("GET", f"objects/ap-bill/{bill_key}", cred)
        bill = result.get("ia::result", {})

        if not bill:
            return {"bill": None, "status": "not_found"}

        return {"bill": self._format_bill(bill), "status": "success"}

    def create_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Create an AP bill.

        Args:
            vendor_id: Vendor ID (required)
            bill_date: Bill date YYYY-MM-DD (required)
            due_date: Due date YYYY-MM-DD
            bill_number: Vendor's invoice number
            lines: Bill lines (required)
                - gl_account: GL account number
                - amount: Line amount
                - memo: Line description
                - department_id: Department ID
                - location_id: Location ID
            description: Bill description
            payment_term: Payment term key
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("vendor_id"):
            raise ValidationError("vendor_id", "vendor_id is required")
        if not args.get("bill_date"):
            raise ValidationError("bill_date", "bill_date is required")
        if not args.get("lines"):
            raise ValidationError("lines", "At least one line is required")

        bill_data: dict[str, Any] = {
            "vendor": {"id": args["vendor_id"]},
            "billDate": args["bill_date"],
            "apBillItem": [self._format_bill_line_for_api(line) for line in args["lines"]],
        }

        if args.get("due_date"):
            bill_data["dueDate"] = args["due_date"]
        if args.get("bill_number"):
            bill_data["billNumber"] = args["bill_number"]
        if args.get("description"):
            bill_data["description"] = args["description"]
        if args.get("payment_term"):
            bill_data["paymentTerm"] = {"key": args["payment_term"]}

        result = self._make_api_call("POST", "objects/ap-bill", cred, data=bill_data)
        created = result.get("ia::result", {})

        logger.info(
            "Sage Intacct bill created",
            service="sage_intacct",
            bill_key=created.get("key"),
            vendor_id=args["vendor_id"],
            log_event="bill_created",
        )

        return {"bill": self._format_bill(created), "status": "success"}

    def update_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Update an AP bill (only draft bills can be updated).

        Args:
            bill_key: Bill key (required)
            due_date: Updated due date
            description: Updated description
        """
        cred = self._get_access_token(org_id, user_id)

        bill_key = args.get("bill_key")
        if not bill_key:
            raise ValidationError("bill_key", "bill_key is required")

        bill_data: dict[str, Any] = {}
        if args.get("due_date"):
            bill_data["dueDate"] = args["due_date"]
        if args.get("description"):
            bill_data["description"] = args["description"]

        result = self._make_api_call("PATCH", f"objects/ap-bill/{bill_key}", cred, data=bill_data)
        updated = result.get("ia::result", {})

        logger.info(
            "Sage Intacct bill updated",
            service="sage_intacct",
            bill_key=bill_key,
            log_event="bill_updated",
        )

        return {"bill": self._format_bill(updated), "status": "success"}

    def delete_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Delete an AP bill (only draft bills can be deleted).

        Args:
            bill_key: Bill key (required)
        """
        cred = self._get_access_token(org_id, user_id)

        bill_key = args.get("bill_key")
        if not bill_key:
            raise ValidationError("bill_key", "bill_key is required")

        self._make_api_call("DELETE", f"objects/ap-bill/{bill_key}", cred)

        logger.info(
            "Sage Intacct bill deleted",
            service="sage_intacct",
            bill_key=bill_key,
            log_event="bill_deleted",
        )

        return {"bill_key": bill_key, "status": "deleted"}

    def post_bill(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Post a draft AP bill.

        Args:
            bill_key: Bill key (required)
        """
        cred = self._get_access_token(org_id, user_id)

        bill_key = args.get("bill_key")
        if not bill_key:
            raise ValidationError("bill_key", "bill_key is required")

        self._make_api_call("PATCH", f"objects/ap-bill/{bill_key}", cred, data={"state": "posted"})

        logger.info(
            "Sage Intacct bill posted",
            service="sage_intacct",
            bill_key=bill_key,
            log_event="bill_posted",
        )

        return {"bill_key": bill_key, "status": "posted"}

    def list_bill_payments(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """List AP payments.

        Args:
            vendor_id: Filter by vendor
            date_from: Filter from this date (YYYY-MM-DD)
            date_to: Filter to this date (YYYY-MM-DD)
            page_size: Results per page
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        filters: list[str] = []

        if args.get("vendor_id"):
            filters.append(f'vendor.id eq "{args["vendor_id"]}"')
        if args.get("date_from"):
            filters.append(f'paymentDate ge "{args["date_from"]}"')
        if args.get("date_to"):
            filters.append(f'paymentDate le "{args["date_to"]}"')

        if filters:
            params["filter"] = " and ".join(filters)

        page_size = args.get("page_size", 100)
        payments = self._paginate("objects/ap-payment", cred, params, page_size=page_size)

        logger.info(
            "Sage Intacct bill payments listed",
            service="sage_intacct",
            count=len(payments),
            log_event="bill_payments_listed",
        )

        return {
            "payments": [self._format_bill_payment(p) for p in payments],
            "count": len(payments),
            "status": "success",
        }

    def create_bill_payment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a payment for one or more bills.

        Args:
            bank_account_id: Bank account ID (required)
            payment_date: Payment date YYYY-MM-DD (required)
            bills: List of bills to pay (required)
                - bill_key: Bill key
                - amount: Payment amount
            payment_method: Payment method
            reference_number: Check/reference number
        """
        cred = self._get_access_token(org_id, user_id)

        if not args.get("bank_account_id"):
            raise ValidationError("bank_account_id", "bank_account_id is required")
        if not args.get("payment_date"):
            raise ValidationError("payment_date", "payment_date is required")
        if not args.get("bills"):
            raise ValidationError("bills", "At least one bill is required")

        payment_data: dict[str, Any] = {
            "financialAccount": {"id": args["bank_account_id"]},
            "paymentDate": args["payment_date"],
            "apPaymentDetail": [
                {
                    "apBill": {"key": b["bill_key"]},
                    "paymentAmount": b["amount"],
                }
                for b in args["bills"]
            ],
        }

        if args.get("payment_method"):
            payment_data["paymentMethod"] = {"name": args["payment_method"]}
        if args.get("reference_number"):
            payment_data["referenceNo"] = args["reference_number"]

        result = self._make_api_call("POST", "objects/ap-payment", cred, data=payment_data)
        created = result.get("ia::result", {})

        total_amount = sum(b["amount"] for b in args["bills"])
        logger.info(
            "Sage Intacct bill payment created",
            service="sage_intacct",
            payment_key=created.get("key"),
            total_amount=total_amount,
            log_event="bill_payment_created",
        )

        return {
            "payment": {
                "key": created.get("key"),
                "record_no": created.get("recordNo"),
                "payment_date": args["payment_date"],
                "total_amount": total_amount,
                "bill_count": len(args["bills"]),
            },
            "status": "success",
        }

    def get_ap_aging(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Get AP aging report.

        Args:
            as_of_date: Report date (YYYY-MM-DD)
            vendor_id: Filter by vendor
        """
        cred = self._get_access_token(org_id, user_id)

        params: dict[str, Any] = {}
        if args.get("as_of_date"):
            params["asOfDate"] = args["as_of_date"]
        if args.get("vendor_id"):
            params["vendorId"] = args["vendor_id"]

        result = self._make_api_call("GET", "services/ap/aging", cred, params=params)
        data = result.get("ia::result", {})

        aging = data.get("agingBuckets", [])

        logger.info(
            "Sage Intacct AP aging retrieved",
            service="sage_intacct",
            log_event="ap_aging_retrieved",
        )

        return {
            "as_of_date": args.get("as_of_date"),
            "aging": {
                "current": next((b.get("amount") for b in aging if b.get("name") == "current"), 0),
                "1_30_days": next((b.get("amount") for b in aging if b.get("name") == "1-30"), 0),
                "31_60_days": next((b.get("amount") for b in aging if b.get("name") == "31-60"), 0),
                "61_90_days": next((b.get("amount") for b in aging if b.get("name") == "61-90"), 0),
                "over_90_days": next((b.get("amount") for b in aging if b.get("name") == "90+"), 0),
            },
            "total": sum(b.get("amount", 0) for b in aging),
            "status": "success",
        }

    def _format_bill(self, bill: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct AP bill for API response."""
        lines = bill.get("apBillItem", [])

        return {
            "key": bill.get("key"),
            "record_no": bill.get("recordNo"),
            "vendor": {
                "id": bill.get("vendor", {}).get("id"),
                "name": bill.get("vendor", {}).get("name"),
            },
            "bill_number": bill.get("billNumber"),
            "bill_date": bill.get("billDate"),
            "due_date": bill.get("dueDate"),
            "description": bill.get("description"),
            "payment_status": bill.get("paymentStatus"),
            "state": bill.get("state"),
            "total_entered": bill.get("totalEntered"),
            "total_paid": bill.get("totalPaid"),
            "total_due": bill.get("totalDue"),
            "currency": bill.get("currency", {}).get("currency"),
            "lines": [
                {
                    "key": li.get("key"),
                    "gl_account": li.get("glAccount", {}).get("accountNo"),
                    "amount": li.get("amount"),
                    "memo": li.get("memo"),
                    "department_id": li.get("department", {}).get("id"),
                    "location_id": li.get("location", {}).get("id"),
                }
                for li in lines
            ],
            "created_date": bill.get("audit", {}).get("createdDateTime"),
            "modified_date": bill.get("audit", {}).get("modifiedDateTime"),
            "href": bill.get("href"),
        }

    def _format_bill_line_for_api(self, line: dict[str, Any]) -> dict[str, Any]:
        """Format a bill line for Sage Intacct API request."""
        formatted: dict[str, Any] = {
            "glAccount": {"accountNo": line["gl_account"]},
            "amount": line["amount"],
        }

        if line.get("memo"):
            formatted["memo"] = line["memo"]
        if line.get("department_id"):
            formatted["department"] = {"id": line["department_id"]}
        if line.get("location_id"):
            formatted["location"] = {"id": line["location_id"]}

        return formatted

    def _format_bill_payment(self, payment: dict[str, Any]) -> dict[str, Any]:
        """Format a Sage Intacct AP payment for API response."""
        details = payment.get("apPaymentDetail", [])

        return {
            "key": payment.get("key"),
            "record_no": payment.get("recordNo"),
            "payment_date": payment.get("paymentDate"),
            "total_amount": payment.get("totalPaymentAmount"),
            "payment_method": payment.get("paymentMethod", {}).get("name"),
            "bank_account_id": payment.get("financialAccount", {}).get("id"),
            "reference_no": payment.get("referenceNo"),
            "state": payment.get("state"),
            "bills_paid": [
                {
                    "bill_key": detail.get("apBill", {}).get("key"),
                    "bill_number": detail.get("apBill", {}).get("billNumber"),
                    "amount_paid": detail.get("paymentAmount"),
                }
                for detail in details
            ],
            "created_date": payment.get("audit", {}).get("createdDateTime"),
        }
