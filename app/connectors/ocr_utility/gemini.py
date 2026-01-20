"""
Gemini Flash extraction operations for OCR utility.
"""

import base64
import binascii
import json
from typing import Any

from app.errors import InternalStargateError, ValidationError
from app.logging_config import get_logger

from .deepdoc import DeepDocMixin

logger = get_logger(__name__)


class GeminiMixin(DeepDocMixin):
    """Mixin with Gemini Flash extraction operations."""

    def extract_with_gemini(
        self, org_id: str, user_id: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract structured data from any document using Gemini Flash.
        Better for complex layouts, tables, and multi-format documents.

        Args:
            file_content: Base64 encoded file
            file_type: pdf, png, jpg (default: pdf)
            extraction_prompt: Custom prompt for extraction (optional)
            output_format: json or text (default: json)
        """
        self._ensure_gemini_initialized()

        file_content = args.get("file_content")
        if not file_content:
            raise ValidationError("file_content", "file_content is required")

        file_type = args.get("file_type", "pdf")
        output_format = args.get("output_format", "json")

        # Decode base64
        try:
            file_bytes = base64.b64decode(file_content)
        except (binascii.Error, ValueError) as e:
            raise ValidationError("file_content", f"Invalid base64 encoding: {e}") from e

        # Prepare image for Gemini
        mime_type = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
        }.get(file_type.lower(), "application/pdf")

        # Default extraction prompt
        extraction_prompt = (
            args.get("extraction_prompt")
            or """
Extract all text and structured data from this document.
Return as JSON with these fields:
- document_type: What type of document this is
- raw_text: All text content
- tables: Any tables found (as arrays of objects)
- key_fields: Important fields extracted (invoice number, dates, amounts, names, etc.)
- confidence: high/medium/low based on extraction quality
"""
        )

        if output_format == "json":
            extraction_prompt += "\n\nReturn valid JSON only, no markdown formatting."

        try:
            # Create file part for Gemini
            file_part = {"mime_type": mime_type, "data": file_bytes}

            response = self._gemini_model.generate_content([extraction_prompt, file_part])

            result_text = response.text

            # Parse JSON if requested
            if output_format == "json":
                # Strip markdown code blocks if present
                if result_text.startswith("```"):
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                try:
                    extracted_data = json.loads(result_text.strip())
                except json.JSONDecodeError:
                    extracted_data = {"raw_text": result_text, "parse_error": True}
            else:
                extracted_data = {"raw_text": result_text}

            logger.info(
                "Gemini extraction complete",
                service="ocr",
                file_type=file_type,
                log_event="gemini_extraction",
            )

            return {
                "extracted_data": extracted_data,
                "method": "gemini-flash",
                "status": "extracted",
            }

        except Exception as e:
            logger.error(
                "Gemini extraction failed",
                service="ocr",
                error=str(e),
                log_event="gemini_extraction_error",
            )
            raise InternalStargateError(
                f"Gemini extraction failed: {e!s}", details={"service": "ocr", "error": str(e)}
            ) from e

    def extract_tables(self, org_id: str, user_id: str, args: dict[str, Any]) -> dict[str, Any]:
        """
        Extract tables from a document using Gemini Flash.
        Specifically designed for structured table extraction.

        Args:
            file_content: Base64 encoded file
            file_type: pdf, png, jpg
            table_schema: Optional schema hint for expected columns
        """
        self._ensure_gemini_initialized()

        file_content = args.get("file_content")
        if not file_content:
            raise ValidationError("file_content", "file_content is required")

        file_type = args.get("file_type", "pdf")
        table_schema = args.get("table_schema")

        try:
            file_bytes = base64.b64decode(file_content)
        except (binascii.Error, ValueError) as e:
            raise ValidationError("file_content", f"Invalid base64 encoding: {e}") from e

        mime_type = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
        }.get(file_type.lower(), "application/pdf")

        prompt = """Extract ALL tables from this document.

For each table found, return:
- table_index: 0-based index
- headers: Column headers as array
- rows: Array of objects with header keys

Return as JSON array. Example:
[
  {
    "table_index": 0,
    "headers": ["Date", "Description", "Amount"],
    "rows": [
      {"Date": "01/15/2024", "Description": "Payment", "Amount": "$100.00"}
    ]
  }
]

Return valid JSON only, no markdown."""

        if table_schema:
            prompt += f"\n\nExpected columns: {table_schema}"

        try:
            file_part = {"mime_type": mime_type, "data": file_bytes}

            response = self._gemini_model.generate_content([prompt, file_part])
            result_text = response.text

            # Parse JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            try:
                tables = json.loads(result_text.strip())
            except json.JSONDecodeError:
                tables = []

            logger.info(
                "Table extraction complete",
                service="ocr",
                table_count=len(tables),
                log_event="gemini_table_extraction",
            )

            return {
                "tables": tables,
                "table_count": len(tables),
                "method": "gemini-flash",
                "status": "extracted",
            }

        except Exception as e:
            logger.error(
                "Table extraction failed",
                service="ocr",
                error=str(e),
                log_event="gemini_table_error",
            )
            raise InternalStargateError(
                f"Table extraction failed: {e!s}", details={"service": "ocr", "error": str(e)}
            ) from e
