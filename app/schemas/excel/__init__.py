"""
Microsoft Excel Capability Schemas.

Rich metadata for Excel workbook operations via Microsoft Graph API.
Finance teams use Excel for financial modeling, data analysis, reporting, and reconciliation.

Excel is the #1 productivity tool (442K instances in training data).
"""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    UsageExample,
    WorkflowHints,
)

# ============ RANGE GET ============

EXCEL_RANGE_GET = CapabilitySchema(
    capability_key="excel.range.get",
    service="microsoft",
    category="spreadsheets",
    description="Get cell values from an Excel range",
    description_detailed=(
        "Retrieves values from a specified range in an Excel workbook stored in OneDrive. "
        "Returns a 2D array of cell values. Use for reading financial data, reports, or any "
        "tabular data. The workbook must be accessible via Microsoft Graph API."
    ),
    parameters={
        "workbook_id": ParameterSchema(
            type="string",
            required=True,
            description="OneDrive item ID of the Excel file",
            example="01ABCDEFGHIJKLMNOP",
        ),
        "worksheet_name": ParameterSchema(
            type="string",
            required=False,
            description="Name of the worksheet (default: Sheet1)",
            example="Q4 Financials",
        ),
        "range": ParameterSchema(
            type="string",
            required=True,
            description="Cell range in A1 notation",
            example="A1:D10",
        ),
    },
    returns={
        "workbook_id": ReturnFieldSchema(type="string", description="Workbook ID"),
        "worksheet": ReturnFieldSchema(type="string", description="Worksheet name"),
        "range": ReturnFieldSchema(type="string", description="Actual range address"),
        "values": ReturnFieldSchema(
            type="array",
            description="2D array of cell values (rows x columns)",
            items_type="array",
        ),
        "row_count": ReturnFieldSchema(type="integer", description="Number of rows"),
        "column_count": ReturnFieldSchema(type="integer", description="Number of columns"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="Workbook or worksheet not found",
            recovery_hint="Verify workbook_id and worksheet_name are correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["onedrive.file.list"],
        typically_followed_by=["excel.range.update"],
        related_capabilities=["excel.worksheet.list", "excel.table.create"],
    ),
    examples=[
        UsageExample(
            description="Read Q4 revenue data from financial model",
            args={
                "workbook_id": "01ABCDEFGHIJKLMNOP",
                "worksheet_name": "Revenue",
                "range": "A1:E20",
            },
            expected_output={
                "values": [
                    ["Month", "Product A", "Product B", "Product C", "Total"],
                    ["Oct", 125000, 89000, 45000, 259000],
                ],
                "row_count": 20,
                "column_count": 5,
            },
        ),
    ],
    idempotent=True,
    has_side_effects=False,
)

# ============ RANGE UPDATE ============

EXCEL_RANGE_UPDATE = CapabilitySchema(
    capability_key="excel.range.update",
    service="microsoft",
    category="spreadsheets",
    description="Update cell values in an Excel range",
    description_detailed=(
        "Updates values in a specified range of an Excel workbook. Values must be "
        "provided as a 2D array matching the dimensions of the target range. "
        "Use for updating financial data, posting journal entries, or bulk data updates."
    ),
    parameters={
        "workbook_id": ParameterSchema(
            type="string",
            required=True,
            description="OneDrive item ID of the Excel file",
        ),
        "worksheet_name": ParameterSchema(
            type="string",
            required=False,
            description="Name of the worksheet (default: Sheet1)",
        ),
        "range": ParameterSchema(
            type="string",
            required=True,
            description="Cell range to update in A1 notation",
            example="B2:D5",
        ),
        "values": ParameterSchema(
            type="array",
            required=True,
            description="2D array of values to write (must match range dimensions)",
            items_type="array",
        ),
    },
    returns={
        "workbook_id": ReturnFieldSchema(type="string", description="Workbook ID"),
        "worksheet": ReturnFieldSchema(type="string", description="Worksheet name"),
        "updated_range": ReturnFieldSchema(type="string", description="Updated range address"),
        "status": ReturnFieldSchema(type="string", description="Should be 'updated'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Values array dimensions don't match range",
            recovery_hint="Ensure values 2D array matches the specified range size",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["excel.range.get"],
        related_capabilities=["excel.row.append"],
    ),
    examples=[
        UsageExample(
            description="Update budget figures for Q4",
            args={
                "workbook_id": "01ABCDEFGHIJKLMNOP",
                "worksheet_name": "Budget",
                "range": "B2:B4",
                "values": [[150000], [175000], [200000]],
            },
        ),
    ],
    idempotent=True,
    has_side_effects=True,
)

# ============ ROW APPEND ============

EXCEL_ROW_APPEND = CapabilitySchema(
    capability_key="excel.row.append",
    service="microsoft",
    category="spreadsheets",
    description="Append a row to the end of data in Excel worksheet",
    description_detailed=(
        "Appends a single row of data after the last used row in a worksheet. "
        "Automatically detects the end of existing data and adds the new row below. "
        "Ideal for adding new transactions, log entries, or incremental data."
    ),
    parameters={
        "workbook_id": ParameterSchema(
            type="string",
            required=True,
            description="OneDrive item ID of the Excel file",
        ),
        "worksheet_name": ParameterSchema(
            type="string",
            required=False,
            description="Name of the worksheet (default: Sheet1)",
        ),
        "values": ParameterSchema(
            type="array",
            required=True,
            description="Array of values for the new row",
            items_type="string",
            example=["2025-01-15", "Invoice #1234", 2500.00, "Paid"],
        ),
    },
    returns={
        "workbook_id": ReturnFieldSchema(type="string", description="Workbook ID"),
        "worksheet": ReturnFieldSchema(type="string", description="Worksheet name"),
        "appended_range": ReturnFieldSchema(
            type="string",
            description="Range address of the appended row (e.g., A25:D25)",
        ),
        "status": ReturnFieldSchema(type="string", description="Should be 'appended'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Values must be a list",
            recovery_hint="Provide values as a single array representing one row",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["excel.range.get"],
        related_capabilities=["excel.range.update", "excel.table.create"],
    ),
    examples=[
        UsageExample(
            description="Add new transaction to ledger",
            args={
                "workbook_id": "01ABCDEFGHIJKLMNOP",
                "worksheet_name": "Transactions",
                "values": ["2025-01-15", "Vendor Payment", -5000.00, "Bank of America"],
            },
        ),
    ],
    idempotent=False,
    has_side_effects=True,
)

# ============ WORKSHEET CREATE ============

EXCEL_WORKSHEET_CREATE = CapabilitySchema(
    capability_key="excel.worksheet.create",
    service="microsoft",
    category="spreadsheets",
    description="Create a new worksheet in an Excel workbook",
    description_detailed=(
        "Creates a new worksheet (tab) in an existing Excel workbook. "
        "Use for organizing data by period, department, or category."
    ),
    parameters={
        "workbook_id": ParameterSchema(
            type="string",
            required=True,
            description="OneDrive item ID of the Excel file",
        ),
        "worksheet_name": ParameterSchema(
            type="string",
            required=True,
            description="Name for the new worksheet",
            example="January 2025",
        ),
    },
    returns={
        "workbook_id": ReturnFieldSchema(type="string", description="Workbook ID"),
        "worksheet_id": ReturnFieldSchema(type="string", description="New worksheet ID"),
        "worksheet_name": ReturnFieldSchema(type="string", description="Worksheet name"),
        "status": ReturnFieldSchema(type="string", description="Should be 'created'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Worksheet name already exists or invalid",
            recovery_hint="Use a unique worksheet name",
        ),
    ],
    workflow=WorkflowHints(
        typically_followed_by=["excel.range.update", "excel.table.create"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# ============ WORKSHEET LIST ============

EXCEL_WORKSHEET_LIST = CapabilitySchema(
    capability_key="excel.worksheet.list",
    service="microsoft",
    category="spreadsheets",
    description="List all worksheets in an Excel workbook",
    description_detailed=(
        "Lists all worksheets (tabs) in an Excel workbook with their IDs, names, "
        "positions, and visibility status. Use to discover available data sheets."
    ),
    parameters={
        "workbook_id": ParameterSchema(
            type="string",
            required=True,
            description="OneDrive item ID of the Excel file",
        ),
    },
    returns={
        "workbook_id": ReturnFieldSchema(type="string", description="Workbook ID"),
        "worksheets": ReturnFieldSchema(
            type="array",
            description="List of worksheets with id, name, position, visibility",
        ),
        "count": ReturnFieldSchema(type="integer", description="Number of worksheets"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.NOT_FOUND,
            description="Workbook not found",
            recovery_hint="Verify workbook_id is correct",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["onedrive.file.list"],
        typically_followed_by=["excel.range.get"],
    ),
    idempotent=True,
    has_side_effects=False,
)

# ============ TABLE CREATE ============

EXCEL_TABLE_CREATE = CapabilitySchema(
    capability_key="excel.table.create",
    service="microsoft",
    category="spreadsheets",
    description="Create an Excel table from a range",
    description_detailed=(
        "Converts a range of cells into a formatted Excel table. Tables provide "
        "structured references, auto-filtering, and better formula support. "
        "Ideal for financial data that needs sorting, filtering, or PivotTable source."
    ),
    parameters={
        "workbook_id": ParameterSchema(
            type="string",
            required=True,
            description="OneDrive item ID of the Excel file",
        ),
        "worksheet_name": ParameterSchema(
            type="string",
            required=False,
            description="Name of the worksheet (default: Sheet1)",
        ),
        "range": ParameterSchema(
            type="string",
            required=True,
            description="Range to convert to table in A1 notation",
            example="A1:E100",
        ),
        "has_headers": ParameterSchema(
            type="boolean",
            required=False,
            description="Whether the first row contains headers (default: true)",
            default=True,
        ),
    },
    returns={
        "workbook_id": ReturnFieldSchema(type="string", description="Workbook ID"),
        "worksheet": ReturnFieldSchema(type="string", description="Worksheet name"),
        "table_id": ReturnFieldSchema(type="string", description="Created table ID"),
        "table_name": ReturnFieldSchema(type="string", description="Table name"),
        "status": ReturnFieldSchema(type="string", description="Should be 'created'"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.CREDENTIALS_MISSING,
            description="Microsoft OAuth credentials not configured",
            recovery_hint="User must complete Microsoft OAuth flow",
        ),
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Range overlaps existing table or invalid",
            recovery_hint="Ensure range doesn't overlap with existing tables",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["excel.range.update", "excel.row.append"],
    ),
    idempotent=False,
    has_side_effects=True,
)

# Export all schemas
EXCEL_SCHEMAS: dict[str, CapabilitySchema] = {
    "excel.range.get": EXCEL_RANGE_GET,
    "excel.range.update": EXCEL_RANGE_UPDATE,
    "excel.row.append": EXCEL_ROW_APPEND,
    "excel.worksheet.create": EXCEL_WORKSHEET_CREATE,
    "excel.worksheet.list": EXCEL_WORKSHEET_LIST,
    "excel.table.create": EXCEL_TABLE_CREATE,
}

__all__ = ["EXCEL_SCHEMAS"]
