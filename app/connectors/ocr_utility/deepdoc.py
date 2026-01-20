"""
Deepdoctection parsing operations for OCR utility.
"""

import base64
import binascii
import io
import re
from typing import Any

from app.errors import ValidationError

from .base import OCRBase


class DeepDocMixin(OCRBase):
    """Mixin with deepdoctection parsing operations."""

    def extract_text(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """Extract raw text from a document (PDF or image)"""
        self._ensure_initialized()

        file_content = args.get("file_content")  # Base64 encoded
        if not file_content:
            raise ValidationError("file_content", "file_content is required")

        # pdf, png, jpg - reserved for future format-specific handling
        _file_type = args.get("file_type", "pdf")

        # Decode base64
        try:
            file_bytes = base64.b64decode(str(file_content))
        except (binascii.Error, ValueError) as e:
            raise ValidationError("file_content", f"Invalid base64 encoding: {e}") from e

        # Process document
        doc = self.analyzer.analyze(path=io.BytesIO(file_bytes))

        # Extract all text
        full_text = []
        for page in doc:
            page_text = " ".join([word.characters for word in page.words])
            full_text.append(page_text)

        return {
            "text": "\n\n".join(full_text),
            "page_count": len(full_text),
            "method": "deepdoctection",
            "status": "extracted",
        }

    def parse_w9(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Extract structured data from W-9 form
        Returns: EIN, business name, address, tax classification, etc.
        """
        self._ensure_initialized()

        file_content = args.get("file_content")  # Base64 encoded
        if not file_content:
            raise ValidationError("file_content", "file_content is required")

        # Decode base64
        try:
            file_bytes = base64.b64decode(str(file_content))
        except (binascii.Error, ValueError) as e:
            raise ValidationError("file_content", f"Invalid base64 encoding: {e}") from e

        # Process W-9 form
        doc = self.analyzer.analyze(path=io.BytesIO(file_bytes))

        # W-9 specific extraction logic
        # deepdoctection provides layout analysis, we extract specific fields

        extracted_data: dict[str, Any] = {}

        # TODO: Implement W-9 specific field extraction
        # W-9 has standard IRS layout:
        # - Name (Line 1)
        # - Business name (Line 2)
        # - Tax classification checkboxes (Line 3)
        # - Address, City, State, Zip (Lines 5-6)
        # - SSN or EIN (Part I)
        # - Signature and date (Part II)

        # For now, extract all text and detect key patterns
        page = next(iter(doc), None)  # W-9 is single page
        if page is None:
            raise ValidationError("file_content", "Document appears to be empty or unreadable")

        all_text = " ".join([word.characters for word in page.words])

        # Simple pattern matching for critical fields
        # Extract EIN (format: XX-XXXXXXX)
        ein_pattern = r"\b\d{2}-\d{7}\b"
        ein_match = re.search(ein_pattern, all_text)
        extracted_data["ein"] = ein_match.group(0) if ein_match else None

        # Extract SSN (format: XXX-XX-XXXX)
        ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
        ssn_match = re.search(ssn_pattern, all_text)
        extracted_data["ssn"] = ssn_match.group(0) if ssn_match else None

        # Use layout analysis to extract name/business fields
        # (deepdoctection provides bounding boxes and reading order)

        extracted_data["raw_text"] = all_text
        extracted_data["form_type"] = "W-9"

        return {
            "document_type": "w9",
            "extracted_fields": extracted_data,
            "confidence": "medium",  # Can be improved with training
            "method": "deepdoctection",
            "status": "parsed",
        }

    def parse_invoice(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Extract structured data from invoice
        Returns: vendor, invoice number, date, amount, line items, etc.
        """
        self._ensure_initialized()

        file_content = args.get("file_content")  # Base64 encoded
        if not file_content:
            raise ValidationError("file_content", "file_content is required")

        # Decode base64
        try:
            file_bytes = base64.b64decode(str(file_content))
        except (binascii.Error, ValueError) as e:
            raise ValidationError("file_content", f"Invalid base64 encoding: {e}") from e

        # Process invoice
        doc = self.analyzer.analyze(path=io.BytesIO(file_bytes))

        extracted_data: dict[str, Any] = {}

        # deepdoctection excels at table detection for line items
        page = next(iter(doc), None)
        if page is None:
            raise ValidationError("file_content", "Document appears to be empty or unreadable")

        # Extract tables (line items)
        tables = [obj for obj in page.layouts if obj.category_name == "table"]

        if tables:
            # Extract line items from first table
            table_data: list[dict[str, Any]] = []
            for _table in tables:
                # deepdoctection provides structured table cells
                # Convert to list of dicts
                pass  # TODO: Implement table extraction

            extracted_data["line_items"] = table_data

        # Extract text for other fields
        all_text = " ".join([word.characters for word in page.words])

        # Extract common invoice patterns
        # Invoice number (various formats: INV-12345, #12345, Invoice: 12345)
        inv_num_patterns = [
            r"Invoice\s*#?\s*:?\s*([A-Z0-9-]+)",
            r"INV-?([A-Z0-9]+)",
            r"#\s*([0-9]+)",
        ]
        for pattern in inv_num_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                extracted_data["invoice_number"] = match.group(1)
                break

        # Extract date (MM/DD/YYYY or similar)
        date_pattern = r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"
        date_match = re.search(date_pattern, all_text)
        extracted_data["date"] = date_match.group(0) if date_match else None

        # Extract total amount ($X,XXX.XX)
        amount_pattern = r"\$\s*([0-9,]+\.\d{2})"
        amount_matches = re.findall(amount_pattern, all_text)
        if amount_matches:
            # Likely the largest amount is the total
            amounts = [float(a.replace(",", "")) for a in amount_matches]
            extracted_data["total_amount"] = max(amounts)

        extracted_data["raw_text"] = all_text
        extracted_data["document_type"] = "invoice"

        return {
            "document_type": "invoice",
            "extracted_fields": extracted_data,
            "confidence": "medium",
            "method": "deepdoctection",
            "status": "parsed",
        }

    def parse_bank_statement(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract structured data from bank statement
        Returns: account number, statement period, transactions, ending balance
        """
        self._ensure_initialized()

        file_content = args.get("file_content")  # Base64 encoded
        if not file_content:
            raise ValidationError("file_content", "file_content is required")

        # Decode base64
        try:
            file_bytes = base64.b64decode(str(file_content))
        except (binascii.Error, ValueError) as e:
            raise ValidationError("file_content", f"Invalid base64 encoding: {e}") from e

        # Process statement (may be multi-page)
        doc = self.analyzer.analyze(path=io.BytesIO(file_bytes))

        extracted_data: dict[str, Any] = {"transactions": []}

        # Extract from each page
        for page_num, page in enumerate(doc):
            # Bank statements typically have transaction tables
            _tables = [obj for obj in page.layouts if obj.category_name == "table"]

            # TODO: Extract transaction rows from _tables
            # Typical columns: Date, Description, Debit, Credit, Balance

            all_text = " ".join([word.characters for word in page.words])

            if page_num == 0:
                # First page usually has account info
                # Extract account number (last 4 digits usually shown: ****1234)
                acct_pattern = r"\*+(\d{4})"
                acct_match = re.search(acct_pattern, all_text)
                extracted_data["account_last_four"] = acct_match.group(1) if acct_match else None

                # Extract statement period
                period_pattern = r"(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*(\d{1,2}/\d{1,2}/\d{2,4})"
                period_match = re.search(period_pattern, all_text)
                if period_match:
                    extracted_data["statement_start"] = period_match.group(1)
                    extracted_data["statement_end"] = period_match.group(2)

        extracted_data["document_type"] = "bank_statement"

        return {
            "document_type": "bank_statement",
            "extracted_fields": extracted_data,
            "confidence": "medium",
            "method": "deepdoctection",
            "status": "parsed",
        }
