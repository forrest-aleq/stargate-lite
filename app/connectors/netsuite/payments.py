"""
Payment operations for NetSuite connector.
"""

from datetime import datetime
from typing import Any

from app.logging_config import get_logger

from .vendors import VendorsMixin

logger = get_logger(__name__)


class PaymentsMixin(VendorsMixin):
    """Mixin with payment and document operations."""

    def approve_vendor_bill(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Approve a vendor bill (set approval status)"""
        from app.errors import ValidationError

        logger.info(
            "Approving vendor bill",
            service="netsuite",
            bill_id=args.get("bill_id"),
            log_event="netsuite_bill_approve",
        )
        cred = self._get_credentials(org_id, user_id)

        bill_id = str(args.get("bill_id", "")).replace("ns:", "")
        if not bill_id:
            raise ValidationError("bill_id", "is required")

        # Update bill approval status
        approval_data: dict[str, Any] = {
            "approvalStatus": {"id": "2"}  # 2 = Approved in NetSuite
        }

        # Optional: Add approver note
        if args.get("approver_note"):
            approval_data["memo"] = args["approver_note"]

        result = self._make_request("PATCH", f"record/v1/vendorbill/{bill_id}", cred, approval_data)

        logger.info(
            "Vendor bill approved",
            service="netsuite",
            bill_id=result.get("id"),
            log_event="netsuite_bill_approved",
        )

        return {
            "bill_id": f"ns:{result.get('id')}",
            "approval_status": "approved",
            "status": result.get("status"),
        }

    def create_vendor_payment(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a payment for vendor bills"""
        from app.errors import ValidationError

        logger.info(
            "Creating vendor payment",
            service="netsuite",
            vendor_id=args.get("vendor_id"),
            log_event="netsuite_payment_create",
        )
        cred = self._get_credentials(org_id, user_id)

        vendor_id = str(args.get("vendor_id", "")).replace("ns:", "")
        if not vendor_id:
            raise ValidationError("vendor_id", "is required")

        bank_account_id = args.get("bank_account_id")
        if not bank_account_id:
            raise ValidationError("bank_account_id", "is required")

        # Transform bills to NetSuite REST format
        bills_to_pay = args.get("bills_to_pay", [])
        apply_items = []
        for bill in bills_to_pay:
            apply_item: dict[str, Any] = {
                "doc": {"id": str(bill.get("bill_id", "")).replace("ns:", "")},
                "apply": True,
            }
            if bill.get("amount"):
                apply_item["amount"] = float(bill["amount"])
            apply_items.append(apply_item)

        payment_data: dict[str, Any] = {
            "entity": {"id": vendor_id},
            "account": {"id": str(bank_account_id).replace("ns:", "")},
            "tranDate": args.get("payment_date", datetime.now().strftime("%Y-%m-%d")),
        }

        if apply_items:
            payment_data["apply"] = {"items": apply_items}
        if args.get("memo"):
            payment_data["memo"] = args["memo"]
        if args.get("payment_method"):
            payment_data["paymentMethod"] = {"id": str(args["payment_method"])}
        if args.get("subsidiary_id"):
            payment_data["subsidiary"] = {"id": str(args["subsidiary_id"])}

        result = self._make_request("POST", "record/v1/vendorpayment", cred, payment_data)

        logger.info(
            "Vendor payment created",
            service="netsuite",
            payment_id=result.get("id"),
            total=result.get("total"),
            log_event="netsuite_payment_created",
        )

        return {
            "payment_id": f"ns:{result.get('id')}",
            "tran_id": result.get("tranId"),
            "total": result.get("total"),
            "status": result.get("status"),
        }

    def batch_vendor_payments(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Process multiple vendor payments in batch"""
        payments = args.get("payments", [])
        logger.info(
            "Processing batch vendor payments",
            service="netsuite",
            payment_count=len(payments),
            log_event="netsuite_batch_payment_start",
        )
        # Validate credentials exist upfront (individual payments will use their own auth)
        self._get_credentials(org_id, user_id)
        results = []
        errors = []

        for payment_spec in payments:
            try:
                payment_result = self.create_vendor_payment(org_id, user_id, payment_spec)
                results.append(payment_result)
            except Exception as e:
                logger.error(
                    "Batch payment failed",
                    service="netsuite",
                    vendor_id=payment_spec.get("vendor_id"),
                    error=str(e),
                    log_event="netsuite_batch_payment_error",
                )
                errors.append({"vendor_id": payment_spec.get("vendor_id"), "error": str(e)})

        logger.info(
            "Batch vendor payments complete",
            service="netsuite",
            processed=len(results),
            failed=len(errors),
            log_event="netsuite_batch_payment_complete",
        )

        return {
            "processed": len(results),
            "failed": len(errors),
            "payments": results,
            "errors": errors,
        }

    def upload_vendor_document(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Attach a document (W-9, contract, etc.) to vendor record"""
        from app.errors import ValidationError

        logger.info(
            "Uploading vendor document",
            service="netsuite",
            vendor_id=args.get("vendor_id"),
            file_name=args.get("file_name"),
            log_event="netsuite_doc_upload",
        )
        cred = self._get_credentials(org_id, user_id)

        vendor_id = str(args.get("vendor_id", "")).replace("ns:", "")
        if not vendor_id:
            raise ValidationError("vendor_id", "is required")

        file_name = args.get("file_name")
        if not file_name:
            raise ValidationError("file_name", "is required")

        file_content = args.get("file_content")  # Base64 encoded file content
        if not file_content:
            raise ValidationError("file_content", "is required (base64 encoded)")

        folder_id = args.get("folder_id", "")  # Optional: specific folder

        # Create file record - REST API format
        file_data: dict[str, Any] = {
            "name": file_name,
            "fileType": {"id": args.get("file_type", "_PDF")},
            "content": file_content,
        }

        if folder_id:
            file_data["folder"] = {"id": str(folder_id)}

        # Upload to File Cabinet
        file_result = self._make_request("POST", "record/v1/file", cred, file_data)
        file_id = file_result.get("id")

        # Attach file to vendor record
        vendor_update: dict[str, Any] = {"attachments": {"items": [{"file": {"id": str(file_id)}}]}}

        self._make_request("PATCH", f"record/v1/vendor/{vendor_id}", cred, vendor_update)

        logger.info(
            "Vendor document uploaded",
            service="netsuite",
            file_id=file_id,
            vendor_id=vendor_id,
            log_event="netsuite_doc_uploaded",
        )

        return {
            "file_id": f"ns:{file_id}",
            "file_name": file_name,
            "vendor_id": f"ns:{vendor_id}",
            "status": "attached",
        }
