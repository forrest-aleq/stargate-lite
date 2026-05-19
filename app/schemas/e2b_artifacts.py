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
        "author": ParameterSchema(
            type="string",
            required=False,
            description="Workbook author metadata",
            default="Aleq",
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
                "rows, optional formulas, optional charts, optional table_name / as_table, "
                "and optional currency_columns / percent_columns / integer_columns. Row cells "
                "may be raw values or objects with value/formula/style/number_format."
            ),
            items_type="object",
        ),
        "named_ranges": ParameterSchema(
            type="array",
            required=False,
            description=(
                "Optional workbook-level named ranges. Each item should include name plus "
                "reference like \"'Forecast'!$B$2:$M$2\"."
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
        "formula_count": ReturnFieldSchema(
            type="integer",
            description="Number of formula cells written into the workbook",
        ),
        "table_count": ReturnFieldSchema(
            type="integer",
            description="Number of Excel tables created across all sheets",
        ),
        "chart_count": ReturnFieldSchema(
            type="integer",
            description="Number of embedded charts created across all sheets",
        ),
        "named_range_count": ReturnFieldSchema(
            type="integer",
            description="Number of workbook named ranges created",
        ),
        "sheet_summaries": ReturnFieldSchema(
            type="array",
            description=(
                "Per-sheet workbook summary objects with name, row_count, column_count, "
                "formula_count, table_count, and chart_count."
            ),
            items_type="object",
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
                "named_ranges": [
                    {"name": "PromoteRange", "reference": "'Waterfall'!$C$2:$C$3"},
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
    "artifact.docx.build": CapabilitySchema(
        capability_key="artifact.docx.build",
        service="e2b",
        category="artifact",
        description="Build a DOCX document inside a reusable sandbox",
        description_detailed=(
            "Creates a finance-friendly Word document from structured sections, paragraphs, "
            "bullets, and tables so Aleq can return editable document work product."
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
                description="Filename for the DOCX document",
                default="aleq-document.docx",
            ),
            "path": ParameterSchema(
                type="string",
                required=False,
                description="Explicit output path inside the sandbox",
            ),
            "title": ParameterSchema(type="string", required=False, description="Document title"),
            "subtitle": ParameterSchema(
                type="string",
                required=False,
                description="Optional subtitle shown beneath the title",
            ),
            "author": ParameterSchema(type="string", required=False, description="Document author"),
            "sections": ParameterSchema(
                type="array",
                required=True,
                description=(
                    "Ordered section objects with heading, optional level, paragraphs, bullets, "
                    "and optional table payloads."
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
                example="document",
            ),
            "file_name": ReturnFieldSchema(type="string", description="Document filename"),
            "path": ReturnFieldSchema(type="string", description="Document path inside sandbox"),
            "mime_type": ReturnFieldSchema(
                type="string",
                description="DOCX MIME type",
                example="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            "size_bytes": ReturnFieldSchema(type="integer", description="Document size in bytes"),
            "section_count": ReturnFieldSchema(
                type="integer",
                description="Number of sections rendered",
            ),
            "paragraph_count": ReturnFieldSchema(
                type="integer",
                description="Number of paragraph blocks rendered",
            ),
            "file_content": ReturnFieldSchema(
                type="string",
                description="Base64-encoded DOCX payload",
            ),
        },
        errors=[
            ErrorHint(
                error_code=ErrorCode.VALIDATION_ERROR,
                description="Document sections are missing or malformed",
                recovery_hint="Provide at least one section object with valid text fields",
            ),
            ErrorHint(
                error_code=ErrorCode.EXECUTION_ERROR,
                description="Document generation failed inside the sandbox",
                recovery_hint="Inspect the generation payload and sandbox execution details",
            ),
        ],
        workflow=WorkflowHints(
            typically_preceded_by=["sandbox.ensure"],
            typically_followed_by=["sandbox.snapshot.create", "sandbox.pause"],
            related_capabilities=["artifact.pptx.build", "artifact.xlsx.build"],
        ),
        examples=[
            UsageExample(
                description="Build a board update memo",
                args={
                    "file_name": "board-update.docx",
                    "title": "Q1 board update",
                    "subtitle": "Collections and burn review",
                    "sections": [
                        {
                            "heading": "Executive summary",
                            "paragraphs": [
                                (
                                    "Revenue outperformed plan while collections "
                                    "slowed late in the quarter."
                                )
                            ],
                            "bullets": [
                                "Net burn improved 11% month over month.",
                                "AR aging above 60 days remains the main working-capital risk.",
                            ],
                        }
                    ],
                },
            )
        ],
        idempotent=False,
        has_side_effects=True,
    ),
    "artifact.pptx.build": CapabilitySchema(
        capability_key="artifact.pptx.build",
        service="e2b",
        category="artifact",
        description="Build a PPTX presentation inside a reusable sandbox",
        description_detailed=(
            "Creates a presentation artifact from structured slides, bullets, and key metrics "
            "so Aleq can return finance decks as first-class work product."
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
                description="Filename for the PPTX deck",
                default="aleq-deck.pptx",
            ),
            "path": ParameterSchema(
                type="string",
                required=False,
                description="Explicit output path inside the sandbox",
            ),
            "title": ParameterSchema(type="string", required=False, description="Deck title"),
            "author": ParameterSchema(type="string", required=False, description="Deck author"),
            "slides": ParameterSchema(
                type="array",
                required=True,
                description=(
                    "Ordered slide objects with title plus optional subtitle, paragraphs, "
                    "bullets, and metric cards."
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
                example="presentation",
            ),
            "file_name": ReturnFieldSchema(type="string", description="Deck filename"),
            "path": ReturnFieldSchema(type="string", description="Deck path inside sandbox"),
            "mime_type": ReturnFieldSchema(
                type="string",
                description="PPTX MIME type",
                example="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
            "size_bytes": ReturnFieldSchema(type="integer", description="Deck size in bytes"),
            "slide_count": ReturnFieldSchema(
                type="integer",
                description="Number of slides rendered",
            ),
            "file_content": ReturnFieldSchema(
                type="string",
                description="Base64-encoded PPTX payload",
            ),
        },
        errors=[
            ErrorHint(
                error_code=ErrorCode.VALIDATION_ERROR,
                description="Slide definitions are missing or malformed",
                recovery_hint="Provide at least one slide with a title and optional body content",
            ),
            ErrorHint(
                error_code=ErrorCode.EXECUTION_ERROR,
                description="Deck generation failed inside the sandbox",
                recovery_hint="Inspect the generation payload and sandbox execution details",
            ),
        ],
        workflow=WorkflowHints(
            typically_preceded_by=["sandbox.ensure"],
            typically_followed_by=["sandbox.snapshot.create", "sandbox.pause"],
            related_capabilities=["artifact.docx.build", "chart.render"],
        ),
        examples=[
            UsageExample(
                description="Build a collections review deck",
                args={
                    "file_name": "collections-review.pptx",
                    "title": "Collections review",
                    "slides": [
                        {
                            "title": "Collections posture",
                            "subtitle": "AR risk concentration",
                            "bullets": [
                                "Overdue balance is concentrated in three enterprise accounts.",
                                "Collections cycle slipped by five days month over month.",
                            ],
                            "metrics": [
                                {"label": "Overdue AR", "value": "$1.8M"},
                                {"label": "DSO", "value": "54 days"},
                            ],
                        }
                    ],
                },
            )
        ],
        idempotent=False,
        has_side_effects=True,
    ),
    "artifact.pdf.build": CapabilitySchema(
        capability_key="artifact.pdf.build",
        service="e2b",
        category="artifact",
        description="Build a PDF report inside a reusable sandbox",
        description_detailed=(
            "Creates a finance-friendly PDF from structured sections, paragraphs, bullets, "
            "and tables so Aleq can return portable report artifacts without relying on "
            "external rendering services."
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
                description="Filename for the PDF document",
                default="aleq-report.pdf",
            ),
            "path": ParameterSchema(
                type="string",
                required=False,
                description="Explicit output path inside the sandbox",
            ),
            "title": ParameterSchema(type="string", required=False, description="Report title"),
            "subtitle": ParameterSchema(
                type="string",
                required=False,
                description="Optional subtitle shown beneath the title",
            ),
            "author": ParameterSchema(type="string", required=False, description="Document author"),
            "sections": ParameterSchema(
                type="array",
                required=True,
                description=(
                    "Ordered section objects with heading, optional level, paragraphs, bullets, "
                    "and optional table payloads."
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
                example="document",
            ),
            "file_name": ReturnFieldSchema(type="string", description="PDF filename"),
            "path": ReturnFieldSchema(type="string", description="PDF path inside sandbox"),
            "mime_type": ReturnFieldSchema(
                type="string",
                description="PDF MIME type",
                example="application/pdf",
            ),
            "size_bytes": ReturnFieldSchema(type="integer", description="PDF size in bytes"),
            "page_count": ReturnFieldSchema(type="integer", description="Number of pages rendered"),
            "section_count": ReturnFieldSchema(
                type="integer",
                description="Number of sections rendered",
            ),
            "paragraph_count": ReturnFieldSchema(
                type="integer",
                description="Number of paragraph blocks rendered",
            ),
            "file_content": ReturnFieldSchema(
                type="string",
                description="Base64-encoded PDF payload",
            ),
        },
        errors=[
            ErrorHint(
                error_code=ErrorCode.VALIDATION_ERROR,
                description="PDF sections are missing or malformed",
                recovery_hint="Provide at least one section object with valid text fields",
            ),
            ErrorHint(
                error_code=ErrorCode.EXECUTION_ERROR,
                description="PDF generation failed inside the sandbox",
                recovery_hint="Inspect the generation payload and sandbox execution details",
            ),
        ],
        workflow=WorkflowHints(
            typically_preceded_by=["sandbox.ensure"],
            typically_followed_by=["sandbox.snapshot.create", "sandbox.pause"],
            related_capabilities=["artifact.docx.build", "chart.render"],
        ),
        examples=[
            UsageExample(
                description="Build a board-ready PDF brief",
                args={
                    "file_name": "board-brief.pdf",
                    "title": "Board brief",
                    "subtitle": "Collections and runway review",
                    "sections": [
                        {
                            "heading": "Executive summary",
                            "paragraphs": [
                                (
                                    "Collections remained the main drag on working capital "
                                    "during the month."
                                )
                            ],
                            "bullets": [
                                "Overdue AR is concentrated in three accounts.",
                                (
                                    "Cash remains above the board threshold if collections "
                                    "land inside 21 days."
                                ),
                            ],
                        }
                    ],
                },
            )
        ],
        idempotent=False,
        has_side_effects=True,
    ),
}

__all__ = ["E2B_ARTIFACT_SCHEMAS"]
