"""
NetSuite Vendor Capability Schemas.

Vendor management operations for NetSuite ERP.
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    WorkflowHints,
)

# ============ VENDOR GET ============

NETSUITE_VENDOR_GET = CapabilitySchema(
    capability_key="netsuite.vendor.get",
    service="netsuite",
    category="vendors",
    description="Get vendor details from NetSuite",
    description_detailed=(
        "Retrieves a vendor record from NetSuite by its internal ID. "
        "Returns company information, contact details, and current balance."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor internal ID (with or without 'ns:' prefix)",
            example="ns:1234",
        ),
    },
    returns={
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="NetSuite internal ID prefixed with 'ns:'",
        ),
        "company_name": ReturnFieldSchema(
            type="string",
            description="Vendor company name",
        ),
        "email": ReturnFieldSchema(
            type="string",
            description="Primary email address",
        ),
        "phone": ReturnFieldSchema(
            type="string",
            description="Primary phone number",
        ),
        "balance": ReturnFieldSchema(
            type="number",
            description="Current open balance",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Vendor not found",
            recovery_hint="Verify the vendor_id is correct using netsuite.vendor.search",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendor.search"],
        typically_followed_by=["netsuite.vendorbill.create"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ VENDOR CREATE ============

NETSUITE_VENDOR_CREATE = CapabilitySchema(
    capability_key="netsuite.vendor.create",
    service="netsuite",
    category="vendors",
    description="Create a vendor in NetSuite",
    description_detailed=(
        "Creates a new vendor record in NetSuite. "
        "Vendors are entities you pay - suppliers, contractors, service providers. "
        "The vendor_id returned can be used to create bills and payments."
    ),
    parameters={
        "company_name": ParameterSchema(
            type="string",
            required=True,
            description="Vendor company name (must be unique)",
            example="Acme Supply Co.",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="Primary email address",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="Primary phone number",
        ),
        "terms": ParameterSchema(
            type="string",
            required=False,
            description="Payment terms internal ID",
        ),
        "account_number": ParameterSchema(
            type="string",
            required=False,
            description="Your account number with this vendor",
        ),
        "subsidiary_id": ParameterSchema(
            type="string",
            required=False,
            description="Subsidiary internal ID (OneWorld only)",
        ),
    },
    returns={
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="NetSuite internal ID prefixed with 'ns:'",
        ),
        "company_name": ReturnFieldSchema(
            type="string",
            description="Confirmed company name",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Vendor status ('active')",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Duplicate vendor name or missing required field",
            recovery_hint="Use netsuite.vendor.search first to check for duplicates",
        ),
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="NetSuite credentials not configured",
            recovery_hint="Complete TBA or OAuth 2.0 authentication",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendor.search"],
        typically_followed_by=["netsuite.vendorbill.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ VENDOR UPDATE ============

NETSUITE_VENDOR_UPDATE = CapabilitySchema(
    capability_key="netsuite.vendor.update",
    service="netsuite",
    category="vendors",
    description="Update vendor record",
    description_detailed=(
        "Updates an existing vendor record in NetSuite. "
        "Can update contact info, address, payment terms, and other fields. "
        "Only provided fields are updated - others remain unchanged."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor internal ID (with or without 'ns:' prefix)",
        ),
        "company_name": ParameterSchema(
            type="string",
            required=False,
            description="New company name",
        ),
        "email": ParameterSchema(
            type="string",
            required=False,
            description="New email address",
        ),
        "phone": ParameterSchema(
            type="string",
            required=False,
            description="New phone number",
        ),
        "address": ParameterSchema(
            type="object",
            required=False,
            description="Address object with street1, street2, city, state, zip, country",
        ),
        "terms": ParameterSchema(
            type="string",
            required=False,
            description="Payment terms internal ID",
        ),
        "account_number": ParameterSchema(
            type="string",
            required=False,
            description="Your account number with this vendor",
        ),
    },
    returns={
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="Vendor internal ID",
        ),
        "company_name": ReturnFieldSchema(
            type="string",
            description="Updated company name",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Update status ('updated')",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Vendor not found or duplicate name",
            recovery_hint="Verify vendor_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendor.get"],
    ),
    idempotent=True,
    has_side_effects=True,
)

# ============ VENDOR SEARCH ============

NETSUITE_VENDOR_SEARCH = CapabilitySchema(
    capability_key="netsuite.vendor.search",
    service="netsuite",
    category="vendors",
    description="Search for vendors by company name",
    description_detailed=(
        "Searches for vendors in NetSuite by company name using SuiteQL. "
        "Returns matching vendors with basic info. "
        "Use before creating vendors to avoid duplicates."
    ),
    parameters={
        "vendor_name": ParameterSchema(
            type="string",
            required=True,
            description="Company name to search for (partial match supported)",
            example="Acme",
        ),
        "limit": ParameterSchema(
            type="integer",
            required=False,
            description="Max results to return",
            default=20,
        ),
    },
    returns={
        "vendors": ReturnFieldSchema(
            type="array",
            description="List of matching vendors",
        ),
        "count": ReturnFieldSchema(
            type="integer",
            description="Number of vendors found",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Empty search term",
            recovery_hint="Provide a vendor_name to search for",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["netsuite.vendor.create", "netsuite.vendor.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ VENDOR UPLOAD DOCUMENT ============

NETSUITE_VENDOR_UPLOAD_DOC = CapabilitySchema(
    capability_key="netsuite.vendor.upload_document",
    service="netsuite",
    category="vendors",
    description="Attach document to vendor record",
    description_detailed=(
        "Uploads a document (W-9, contract, etc.) to NetSuite File Cabinet "
        "and attaches it to a vendor record. "
        "File content must be base64 encoded."
    ),
    parameters={
        "vendor_id": ParameterSchema(
            type="string",
            required=True,
            description="Vendor internal ID",
        ),
        "file_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the file",
            example="W9_AcmeSupply.pdf",
        ),
        "file_content": ParameterSchema(
            type="string",
            required=True,
            description="Base64 encoded file content",
        ),
        "file_type": ParameterSchema(
            type="string",
            required=False,
            description="File type (default: _PDF)",
            default="_PDF",
        ),
        "folder_id": ParameterSchema(
            type="string",
            required=False,
            description="File Cabinet folder ID",
        ),
    },
    returns={
        "file_id": ReturnFieldSchema(
            type="string",
            description="NetSuite file ID",
        ),
        "file_name": ReturnFieldSchema(
            type="string",
            description="Uploaded file name",
        ),
        "vendor_id": ReturnFieldSchema(
            type="string",
            description="Vendor the file is attached to",
        ),
        "status": ReturnFieldSchema(
            type="string",
            description="Upload status ('attached')",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Invalid vendor_id or file content",
            recovery_hint="Ensure vendor exists and file_content is valid base64",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["netsuite.vendor.create", "netsuite.vendor.get"],
    ),
    idempotent=False,
    has_side_effects=True,
)

NETSUITE_VENDOR_SCHEMAS: dict[str, CapabilitySchema] = {
    "netsuite.vendor.get": NETSUITE_VENDOR_GET,
    "netsuite.vendor.create": NETSUITE_VENDOR_CREATE,
    "netsuite.vendor.update": NETSUITE_VENDOR_UPDATE,
    "netsuite.vendor.search": NETSUITE_VENDOR_SEARCH,
    "netsuite.vendor.upload_document": NETSUITE_VENDOR_UPLOAD_DOC,
}

__all__ = ["NETSUITE_VENDOR_SCHEMAS"]
