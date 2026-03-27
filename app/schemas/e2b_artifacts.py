"""Schema metadata for E2B-backed artifact capabilities."""

from app.errors import ErrorCode
from app.schemas.base import (
    CapabilitySchema,
    ErrorHint,
    ParameterSchema,
    ReturnFieldSchema,
    UsageExample,
    WorkflowHints,
)

ARTIFACT_XLSX_BUILD = CapabilitySchema(
    capability_key="artifact.xlsx.build",
    service="e2b",
    category="artifact",
    description="Build an XLSX workbook inside a reusable sandbox",
    description_detailed=(
        "Creates a spreadsheet artifact from structured sheet data and returns the workbook "
        "as a first-class file payload Aleq can attach to task work product."
    ),
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=False,
            description="Existing sandbox to reuse for artifact generation",
        ),
        "workbook_name": ParameterSchema(
            type="string",
            required=False,
            description="Filename for the workbook",
            default="aleq-workbook.xlsx",
        ),
        "path": ParameterSchema(
            type="string",
            required=False,
            description="Explicit output path inside the sandbox",
        ),
        "sheets": ParameterSchema(
            type="array",
            required=True,
            description=(
                "Workbook sheets. Each item should be an object with name, optional columns, "
                "rows, and optional currency_columns / percent_columns / integer_columns."
            ),
            items_type="object",
        ),
        "command_timeout_seconds": ParameterSchema(
            type="number",
            required=False,
            description="How long to wait for generation before disconnecting",
            default=0,
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "artifact_kind": ReturnFieldSchema(
            type="string",
            description="Artifact family",
            example="spreadsheet",
        ),
        "file_name": ReturnFieldSchema(type="string", description="Workbook filename"),
        "path": ReturnFieldSchema(type="string", description="Workbook path inside sandbox"),
        "mime_type": ReturnFieldSchema(
            type="string",
            description="Workbook MIME type",
            example="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        "size_bytes": ReturnFieldSchema(type="integer", description="Workbook size in bytes"),
        "sheet_count": ReturnFieldSchema(type="integer", description="Number of sheets created"),
        "sheet_names": ReturnFieldSchema(
            type="array",
            description="Ordered sheet names",
            items_type="string",
        ),
        "file_content": ReturnFieldSchema(
            type="string",
            description="Base64-encoded workbook payload",
        ),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Workbook input is missing or malformed",
            recovery_hint="Provide at least one sheet with rows and valid array/object fields",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Workbook generation failed inside the sandbox",
            recovery_hint="Inspect the generation payload and sandbox execution details",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure"],
        typically_followed_by=["sandbox.snapshot.create", "sandbox.pause"],
        related_capabilities=["chart.render"],
    ),
    examples=[
        UsageExample(
            description="Build a simple waterfall workbook",
            args={
                "workbook_name": "waterfall.xlsx",
                "sheets": [
                    {
                        "name": "Waterfall",
                        "columns": ["Partner", "Distribution", "Promote %"],
                        "rows": [
                            ["GP", 1250000, 0.2],
                            ["LP", 3750000, 0.8],
                        ],
                        "currency_columns": ["Distribution"],
                        "percent_columns": ["Promote %"],
                    }
                ],
            },
        )
    ],
    idempotent=False,
    has_side_effects=True,
)

CHART_RENDER = CapabilitySchema(
    capability_key="chart.render",
    service="e2b",
    category="artifact",
    description="Render a chart artifact inside a reusable sandbox",
    description_detailed=(
        "Creates an SVG chart artifact from structured labels and series data so Aleq can "
        "attach visual work product to reports, dashboards, and finance reviews."
    ),
    parameters={
        "sandbox_id": ParameterSchema(
            type="string",
            required=False,
            description="Existing sandbox to reuse for artifact generation",
        ),
        "file_name": ParameterSchema(
            type="string",
            required=False,
            description="Filename for the chart artifact",
            default="aleq-chart.svg",
        ),
        "path": ParameterSchema(
            type="string",
            required=False,
            description="Explicit output path inside the sandbox",
        ),
        "chart_type": ParameterSchema(
            type="string",
            required=False,
            description="Chart style",
            default="line",
            enum=["line", "bar", "column"],
        ),
        "title": ParameterSchema(type="string", required=False, description="Chart title"),
        "subtitle": ParameterSchema(type="string", required=False, description="Chart subtitle"),
        "x_axis_label": ParameterSchema(type="string", required=False, description="X-axis label"),
        "y_axis_label": ParameterSchema(type="string", required=False, description="Y-axis label"),
        "labels": ParameterSchema(
            type="array",
            required=True,
            description="Ordered x-axis labels",
            items_type="string",
        ),
        "series": ParameterSchema(
            type="array",
            required=True,
            description="Series objects with name, values, and optional color",
            items_type="object",
        ),
        "width": ParameterSchema(
            type="integer",
            required=False,
            description="SVG width",
            default=960,
        ),
        "height": ParameterSchema(
            type="integer",
            required=False,
            description="SVG height",
            default=540,
        ),
        "command_timeout_seconds": ParameterSchema(
            type="number",
            required=False,
            description="How long to wait for rendering before disconnecting",
            default=0,
        ),
    },
    returns={
        "sandbox_id": ReturnFieldSchema(type="string", description="Sandbox identifier"),
        "artifact_kind": ReturnFieldSchema(
            type="string",
            description="Artifact family",
            example="report",
        ),
        "file_name": ReturnFieldSchema(type="string", description="Chart filename"),
        "path": ReturnFieldSchema(type="string", description="Chart path inside sandbox"),
        "mime_type": ReturnFieldSchema(
            type="string",
            description="Chart MIME type",
            example="image/svg+xml",
        ),
        "size_bytes": ReturnFieldSchema(type="integer", description="Chart size in bytes"),
        "chart_type": ReturnFieldSchema(type="string", description="Resolved chart type"),
        "series_count": ReturnFieldSchema(type="integer", description="Number of series rendered"),
        "file_content": ReturnFieldSchema(type="string", description="Base64-encoded SVG payload"),
    },
    errors=[
        ErrorHint(
            error_code=ErrorCode.VALIDATION_ERROR,
            description="Chart labels or series are malformed",
            recovery_hint="Provide labels plus at least one series with matching value counts",
        ),
        ErrorHint(
            error_code=ErrorCode.EXECUTION_ERROR,
            description="Chart rendering failed inside the sandbox",
            recovery_hint="Inspect the generation payload and retry with simpler series data",
        ),
    ],
    workflow=WorkflowHints(
        typically_preceded_by=["sandbox.ensure"],
        typically_followed_by=["artifact.xlsx.build", "sandbox.snapshot.create"],
        related_capabilities=["artifact.xlsx.build"],
    ),
    examples=[
        UsageExample(
            description="Render a monthly burn chart",
            args={
                "chart_type": "line",
                "title": "Monthly burn",
                "labels": ["Jan", "Feb", "Mar"],
                "series": [{"name": "Burn", "values": [320000, 295000, 310000]}],
            },
        )
    ],
    idempotent=False,
    has_side_effects=True,
)

E2B_ARTIFACT_SCHEMAS = {
    "artifact.xlsx.build": ARTIFACT_XLSX_BUILD,
    "chart.render": CHART_RENDER,
}

__all__ = ["E2B_ARTIFACT_SCHEMAS"]
