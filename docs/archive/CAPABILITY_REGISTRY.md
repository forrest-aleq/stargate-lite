# Stargate Capability Registry

**Complete API Reference for MARS Integration**

**Total Capabilities**: 294
**Services**: 22
**Last Updated**: October 18, 2025

---

## Quick Reference

### Endpoint
```
POST /api/v1/execute
```

### Request Format
```json
{
  "capability_key": "vendor.create",
  "org_id": "your_org_id",
  "user_id": "your_user_id",
  "args": {
    // Capability-specific arguments
  }
}
```

### Response Format (Success)
```json
{
  // Capability-specific response data
  "status": "success"
}
```

### Response Format (Error)
```json
{
  "error": true,
  "error_code": "CREDENTIAL_MISSING",
  "error_message": "No credentials found for service 'quickbooks'",
  "retry_strategy": "human_intervention",
  "details": {
    "service": "quickbooks",
    "org_id": "test_org",
    "user_id": "test_user"
  }
}
```

---

## Error Taxonomy

All Stargate responses include standardized error codes for MARS error handling:

| Error Code | Retry Strategy | Description |
|------------|---------------|-------------|
| `CREDENTIAL_MISSING` | `human_intervention` | User has not connected this service |
| `CREDENTIAL_INVALID` | `human_intervention` | Credentials expired or revoked |
| `RATE_LIMIT` | `backoff` | API rate limit exceeded |
| `API_DOWN` | `backoff` | External API temporarily unavailable |
| `MISSING_PERMISSION` | `human_intervention` | User needs to grant additional OAuth scopes |
| `VALIDATION_ERROR` | `none` | Input data from MARS was invalid |
| `NOT_FOUND` | `none` | Resource does not exist |
| `INTERNAL_STARGATE_ERROR` | `backoff` | Internal Stargate error (bug or config issue) |
| `EXTERNAL_API_ERROR` | `backoff` | Generic error from external API |

---

## Services Overview

| Service | Capabilities | Auth Type | Description |
|---------|--------------|-----------|-------------|
| **quickbooks** | 31 | OAuth 2.0 | Accounting operations (vendors, bills, invoices, customers, etc.) |
| **stripe** | 61 | API Key | Payment processing (intents, customers, products, subscriptions, etc.) |
| **billcom** | 9 | OAuth 2.0 | AP automation (bills, payments, approvals) |
| **netsuite** | 15 | OAuth 2.0 | ERP operations (vendors, bills, payments, journal entries) |
| **recurly** | 9 | API Key | Subscription billing |
| **plaid** | 11 | API Key | Banking data aggregation |
| **ramp** | 5 | OAuth 2.0 | Corporate card management |
| **mercury** | 6 | API Key | Business banking |
| **brex** | 8 | OAuth 2.0 | Corporate card and expense management |
| **chase** | 8 | OAuth 2.0 | Business banking and payments |
| **hubspot** | 4 | OAuth 2.0 | CRM operations |
| **notion** | 10 | OAuth 2.0 | Workspace and database operations |
| **asana** | 12 | OAuth 2.0 | Project and task management |
| **powerbi** | 10 | OAuth 2.0 | Business intelligence and reporting |
| **google** | 20 | OAuth 2.0 | Gmail (3), Drive (5), Calendar (5), Sheets (7) |
| **slack** | 6 | OAuth 2.0 | Team communication |
| **blandai** | 8 | API Key | AI phone calls |
| **twilio** | 8 | API Key | SMS/MMS messaging |
| **ibkr** | 15 | API Key | Trading and portfolio management |
| **schwab** | 12 | OAuth 2.0 | Trading and market data |
| **microsoft** | 16 | OAuth 2.0 | Excel (6), OneDrive (5), Outlook Calendar (5) |
| **ocr** | 4 | None | Document intelligence (W-9, invoices, bank statements) |

**Total**: 294 capabilities

---

## NETSUITE (15 capabilities)

**Authentication**: OAuth 2.0
**Service Key**: `netsuite`

### vendor.create
Create a vendor in NetSuite

### vendor.get
Get vendor details from NetSuite

### vendor.update ⭐ NEW
Update vendor record (address, phone, email, etc.)
```json
{
  "vendor_id": "ns:12345",
  "address": {
    "street1": "123 Main St",
    "city": "Boston",
    "state": "MA",
    "zip": "02101"
  }
}
```

### vendor.search ⭐ NEW
Search for vendors by company name
```json
{
  "vendor_name": "Lighthouse Marine",
  "limit": 20
}
```

### bill.create
Create a vendor bill in NetSuite

### bill.approve ⭐ NEW
Approve a vendor bill (set approval status)
```json
{
  "bill_id": "ns:67890",
  "approver_note": "Approved for payment"
}
```

### payment.create ⭐ NEW
Create a payment for vendor bills
```json
{
  "vendor_id": "ns:12345",
  "bank_account_id": "123",
  "bills_to_pay": [
    {"doc": "67890", "amount": 1500.00}
  ]
}
```

### payment.batch ⭐ NEW
Process multiple vendor payments in batch
```json
{
  "payments": [
    {"vendor_id": "ns:111", "bank_account_id": "123", "bills_to_pay": [...]},
    {"vendor_id": "ns:222", "bank_account_id": "123", "bills_to_pay": [...]}
  ]
}
```

### vendor.upload_document ⭐ NEW
Attach W-9, contract, or other document to vendor record
```json
{
  "vendor_id": "ns:12345",
  "file_name": "W9_LighthouseMarine.pdf",
  "file_content": "base64_encoded_pdf_content",
  "file_type": "_PDF"
}
```

### journal.create
Create a journal entry

### purchaseorder.create
Create a purchase order

### query
Query records using SuiteQL

### subsidiary.list
Get list of subsidiaries

### reconcile.bank
Reconcile bank statement

### customrecord.create
Create a custom record

---

## GOOGLE (20 capabilities)

**Authentication**: OAuth 2.0 (shared credential for Gmail, Drive, Calendar, Sheets)
**Service Key**: `google`

### Gmail (3 capabilities)

#### email.send
Send an email via Gmail

#### email.read
Read emails from Gmail inbox

#### email.draft
Create a draft email

### Google Drive (5 capabilities) ⭐ NEW

#### gdrive.file.upload
Upload file to Google Drive
```json
{
  "file_name": "W9_Form.pdf",
  "file_content": "base64_encoded_content",
  "folder_id": "optional_folder_id",
  "mime_type": "application/pdf"
}
```

#### gdrive.file.download
Download file from Google Drive
```json
{
  "file_id": "1ABC123xyz"
}
```
Returns base64-encoded file content.

#### gdrive.file.list
List files in Google Drive folder
```json
{
  "folder_id": "optional_folder_id",
  "query": "optional_drive_query",
  "max_results": 100
}
```

#### gdrive.folder.create
Create folder in Google Drive
```json
{
  "folder_name": "Vendor Documents",
  "parent_folder_id": "optional_parent"
}
```

#### gdrive.file.metadata
Get file metadata without downloading content
```json
{
  "file_id": "1ABC123xyz"
}
```

### Google Calendar (5 capabilities) ⭐ NEW

#### gcal.event.create
Create calendar event (impersonating user via domain-wide delegation)
```json
{
  "summary": "Process improvement discussion",
  "description": "Review AP workflow",
  "start_datetime": "2025-10-19T14:00:00-04:00",
  "end_datetime": "2025-10-19T15:00:00-04:00",
  "timezone": "America/New_York",
  "attendees": ["lisa@dockwa.com"],
  "add_conference": true
}
```

#### gcal.availability.check
Check free/busy time for attendees
```json
{
  "attendees": ["lisa@dockwa.com", "jordan@dockwa.com"],
  "time_min": "2025-10-19T09:00:00-04:00",
  "time_max": "2025-10-19T17:00:00-04:00"
}
```

#### gcal.event.update
Update existing calendar event

#### gcal.event.list
List calendar events in date range

#### gcal.event.cancel
Cancel calendar event

### Google Sheets (7 capabilities) ⭐ NEW

#### gsheets.range.get
Get values from range in Google Sheets
```json
{
  "spreadsheet_id": "1ABC123xyz",
  "range": "Sheet1!A1:D10"
}
```

#### gsheets.range.update
Update values in range
```json
{
  "spreadsheet_id": "1ABC123xyz",
  "range": "Sheet1!A1:D10",
  "values": [
    ["Name", "Amount", "Date", "Status"],
    ["Vendor A", "1500", "2025-10-18", "Paid"]
  ]
}
```

#### gsheets.row.append
Append row to Google Sheets
```json
{
  "spreadsheet_id": "1ABC123xyz",
  "range": "Sheet1!A:D",
  "values": ["Vendor B", "2500", "2025-10-19", "Pending"]
}
```

#### gsheets.sheet.create
Create new sheet (tab) in spreadsheet

#### gsheets.batch.update
Perform batch updates (structure and values)

#### gsheets.range.clear
Clear values in range

#### gsheets.metadata.get
Get spreadsheet metadata (sheets, properties)

---

## MICROSOFT (16 capabilities) ⭐ NEW

**Authentication**: OAuth 2.0 (shared credential for Excel, OneDrive, Outlook Calendar)
**Service Key**: `microsoft`

### Microsoft Excel (6 capabilities)

#### excel.range.get
Get values from range in Excel workbook via Microsoft Graph
```json
{
  "workbook_id": "drive_item_id",
  "worksheet_name": "Sheet1",
  "range": "A1:D10"
}
```

#### excel.range.update
Update values in range

#### excel.row.append
Append row to Excel worksheet

#### excel.worksheet.create
Create new worksheet in workbook

#### excel.worksheet.list
List all worksheets in workbook

#### excel.table.create
Create table in Excel worksheet

### Microsoft OneDrive (5 capabilities)

#### onedrive.file.upload
Upload file to OneDrive
```json
{
  "file_name": "document.pdf",
  "file_content": "base64_encoded_content",
  "folder_path": "/Documents"
}
```

#### onedrive.file.download
Download file from OneDrive

#### onedrive.file.list
List files in OneDrive folder

#### onedrive.folder.create
Create folder in OneDrive

#### onedrive.file.metadata
Get file metadata from OneDrive

### Microsoft Outlook Calendar (5 capabilities)

#### outlook.event.create
Create calendar event (impersonating user)
```json
{
  "subject": "Vendor payment review",
  "body": "Discuss overdue invoices",
  "start_datetime": "2025-10-19T14:00:00",
  "end_datetime": "2025-10-19T15:00:00",
  "timezone": "Eastern Standard Time",
  "attendees": ["manager@company.com"],
  "add_teams_meeting": true
}
```

#### outlook.availability.check
Check free/busy schedule for attendees

#### outlook.event.update
Update calendar event

#### outlook.event.list
List calendar events

#### outlook.event.cancel
Cancel calendar event

---

## OCR / DOCUMENT INTELLIGENCE (4 capabilities) ⭐ NEW

**Authentication**: None (internal utility)
**Service Key**: `ocr`
**Technology**: deepdoctection (open-source document AI)

### ocr.text.extract
Extract raw text from document (PDF or image)
```json
{
  "file_content": "base64_encoded_pdf",
  "file_type": "pdf"
}
```

**Returns**:
```json
{
  "text": "Extracted text content...",
  "page_count": 2,
  "method": "deepdoctection",
  "status": "extracted"
}
```

### ocr.w9.parse
Extract structured data from W-9 form
```json
{
  "file_content": "base64_encoded_w9_pdf"
}
```

**Returns**:
```json
{
  "document_type": "w9",
  "extracted_fields": {
    "ein": "12-3456789",
    "ssn": null,
    "raw_text": "Full form text..."
  },
  "confidence": "medium",
  "status": "parsed"
}
```

### ocr.invoice.parse
Extract structured data from invoice
```json
{
  "file_content": "base64_encoded_invoice_pdf"
}
```

**Returns**:
```json
{
  "document_type": "invoice",
  "extracted_fields": {
    "invoice_number": "INV-12345",
    "date": "10/15/2025",
    "total_amount": 1500.00,
    "line_items": [],
    "raw_text": "Full invoice text..."
  },
  "confidence": "medium",
  "status": "parsed"
}
```

### ocr.bankstatement.parse
Extract structured data from bank statement
```json
{
  "file_content": "base64_encoded_statement_pdf"
}
```

**Returns**:
```json
{
  "document_type": "bank_statement",
  "extracted_fields": {
    "account_last_four": "1234",
    "statement_start": "09/01/2025",
    "statement_end": "09/30/2025",
    "transactions": []
  },
  "confidence": "medium",
  "status": "parsed"
}
```

---

## Usage Examples for MARS Subgraphs

### Example 1: OnboardNewVendor_Subgraph

```python
# Node 1: Check if vendor exists
response = stargate.execute(
    capability_key="netsuite.vendor.search",
    org_id=org_id,
    user_id=user_id,
    args={"vendor_name": "Lighthouse Marine Services"}
)

if response.get("error"):
    # Handle error based on error_code and retry_strategy
    if response["error_code"] == "CREDENTIAL_MISSING":
        # Escalate to human - need to connect NetSuite
        pass

# Node 2: Request W-9 via email
email_response = stargate.execute(
    capability_key="email.send",
    org_id=org_id,
    user_id=user_id,
    args={
        "to": "tony@lighthousemarine.com",
        "subject": "W-9 Request",
        "body": "Please provide completed W-9...",
        "attachments": [...]
    }
)

# Node 3: Parse W-9 when received
w9_data = stargate.execute(
    capability_key="ocr.w9.parse",
    org_id=org_id,
    user_id=user_id,
    args={"file_content": base64_w9_pdf}
)

# Node 4: Upload W-9 to NetSuite
upload_response = stargate.execute(
    capability_key="netsuite.vendor.upload_document",
    org_id=org_id,
    user_id=user_id,
    args={
        "vendor_id": "ns:12345",
        "file_name": "W9_LighthouseMarine.pdf",
        "file_content": base64_w9_pdf,
        "file_type": "_PDF"
    }
)
```

### Example 2: CollectWeeklyBalances_Subgraph

```python
# For each bank account
for bank in bank_accounts:
    if bank["has_api"]:
        # Use API connector
        balance = stargate.execute(
            capability_key="mercury.account.get",
            org_id=org_id,
            user_id=user_id,
            args={"account_id": bank["account_id"]}
        )
    else:
        # Use browser automation (future)
        pass

    # Update Google Sheet with balance
    stargate.execute(
        capability_key="gsheets.row.append",
        org_id=org_id,
        user_id=user_id,
        args={
            "spreadsheet_id": "1ABC123xyz",
            "range": "Balances!A:E",
            "values": [
                bank["name"],
                bank["account_number"],
                balance["current_balance"],
                datetime.now().isoformat(),
                "Collected"
            ]
        }
    )
```

---

## Complete Capability List

For a complete list of all 294 capabilities with detailed parameters, see the individual service sections above.

**Key Capabilities for Initial MARS Integration**:
- `netsuite.vendor.*` - Vendor management
- `email.send` - Email communication
- `ocr.*` - Document parsing
- `gdrive.*` / `onedrive.*` - File storage
- `gsheets.*` / `excel.*` - Spreadsheet operations
- `gcal.*` / `outlook.*` - Calendar management

---

**For Questions or Issues**: Contact Stargate team
**Last Updated**: October 18, 2025
