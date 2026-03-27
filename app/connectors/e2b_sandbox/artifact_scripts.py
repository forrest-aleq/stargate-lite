# ruff: noqa: E501
"""Pure-Python artifact builders that run inside an E2B sandbox."""

from __future__ import annotations

import base64
import json
from textwrap import dedent
from typing import Any


def _encode_spec(spec: dict[str, Any]) -> str:
    payload = json.dumps(spec, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return base64.b64encode(payload).decode("ascii")


def build_xlsx_script(spec: dict[str, Any]) -> str:
    encoded = _encode_spec(spec)
    return dedent(
        f"""
        import base64
        import io
        import json
        import zipfile
        from pathlib import Path
        from xml.sax.saxutils import escape

        SPEC = json.loads(base64.b64decode("{encoded}").decode("utf-8"))


        def column_letter(index):
            index += 1
            out = []
            while index:
                index, remainder = divmod(index - 1, 26)
                out.append(chr(65 + remainder))
            return "".join(reversed(out))


        def xml_text(value):
            if value is None:
                return ""
            if isinstance(value, bool):
                return "TRUE" if value else "FALSE"
            return str(value)


        def normalize_columns(rows, explicit):
            if explicit:
                return [str(col) for col in explicit]
            names = []
            seen = set()
            for row in rows:
                if isinstance(row, dict):
                    for key in row:
                        key_text = str(key)
                        if key_text not in seen:
                            seen.add(key_text)
                            names.append(key_text)
            return names


        def normalize_rows(rows, columns):
            normalized = []
            for row in rows:
                if isinstance(row, dict):
                    normalized.append([row.get(column) for column in columns])
                elif isinstance(row, list):
                    normalized.append(row[: len(columns)] + [None] * max(0, len(columns) - len(row)))
                else:
                    normalized.append([row] + [None] * max(0, len(columns) - 1))
            return normalized


        def style_for(header, value, currency_columns, percent_columns, integer_columns):
            header_key = header.lower()
            if value is None:
                return 0
            if header_key in currency_columns and isinstance(value, (int, float)):
                return 2
            if header_key in percent_columns and isinstance(value, (int, float)):
                return 3
            if header_key in integer_columns and isinstance(value, (int, float)):
                return 4
            return 0


        def cell_payload(value):
            if value is None:
                return "string", ""
            if isinstance(value, bool):
                return "bool", "1" if value else "0"
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return "number", repr(value)
            return "string", xml_text(value)


        shared_strings = []
        shared_index = {{}}


        def intern_shared(value):
            if value not in shared_index:
                shared_index[value] = len(shared_strings)
                shared_strings.append(value)
            return shared_index[value]


        def build_sheet_xml(sheet_spec):
            name = str(sheet_spec.get("name") or "Sheet")
            rows = list(sheet_spec.get("rows") or [])
            columns = normalize_columns(rows, sheet_spec.get("columns") or [])
            if not columns:
                columns = ["Value"]
            body_rows = normalize_rows(rows, columns)
            currency_columns = {{str(col).lower() for col in sheet_spec.get("currency_columns", [])}}
            percent_columns = {{str(col).lower() for col in sheet_spec.get("percent_columns", [])}}
            integer_columns = {{str(col).lower() for col in sheet_spec.get("integer_columns", [])}}

            all_rows = [columns] + body_rows
            widths = [len(xml_text(col)) for col in columns]
            for row in body_rows:
                for idx, cell in enumerate(row):
                    widths[idx] = min(max(widths[idx], len(xml_text(cell))), 36)

            col_xml = "".join(
                f'<col min="{{idx + 1}}" max="{{idx + 1}}" width="{{max(10, width + 2)}}" customWidth="1"/>'
                for idx, width in enumerate(widths)
            )
            row_xml = []
            for row_idx, row in enumerate(all_rows, start=1):
                cells = []
                for col_idx, header in enumerate(columns):
                    value = row[col_idx] if col_idx < len(row) else None
                    if row_idx == 1:
                        style = 1
                        kind, payload = "string", xml_text(header)
                    else:
                        style = style_for(header, value, currency_columns, percent_columns, integer_columns)
                        kind, payload = cell_payload(value)
                    cell_ref = f"{{column_letter(col_idx)}}{{row_idx}}"
                    if kind == "number":
                        cells.append(f'<c r="{{cell_ref}}" s="{{style}}"><v>{{payload}}</v></c>')
                    elif kind == "bool":
                        cells.append(f'<c r="{{cell_ref}}" t="b" s="{{style}}"><v>{{payload}}</v></c>')
                    else:
                        string_id = intern_shared(payload)
                        cells.append(f'<c r="{{cell_ref}}" t="s" s="{{style}}"><v>{{string_id}}</v></c>')
                row_xml.append(f'<row r="{{row_idx}}">' + "".join(cells) + "</row>")

            freeze_header = sheet_spec.get("freeze_header", True)
            top_left = "A2" if freeze_header else "A1"
            pane_xml = (
                '<sheetViews><sheetView workbookViewId="0">'
                '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
                "</sheetView></sheetViews>"
                if freeze_header
                else '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
            )
            auto_filter = (
                f'<autoFilter ref="A1:{{column_letter(len(columns) - 1)}}{{len(all_rows)}}"/>'
                if sheet_spec.get("auto_filter", True) and all_rows
                else ""
            )
            dimension = f"A1:{{column_letter(len(columns) - 1)}}{{max(1, len(all_rows))}}"
            xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f"<dimension ref=\\"{{dimension}}\\"/>"
                f"{{pane_xml}}"
                f"<cols>{{col_xml}}</cols>"
                "<sheetData>"
                + "".join(row_xml)
                + "</sheetData>"
                + auto_filter
                + "</worksheet>"
            )
            return name[:31], xml


        sheets = SPEC.get("sheets") or []
        if not sheets:
            raise ValueError("At least one sheet is required")

        workbook_name = str(SPEC.get("workbook_name") or "aleq-workbook.xlsx")
        if not workbook_name.lower().endswith(".xlsx"):
            workbook_name += ".xlsx"
        path = str(SPEC.get("path") or f"/workspace/{{workbook_name}}")
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        sheet_xml = [build_sheet_xml(sheet) for sheet in sheets]

        workbook = io.BytesIO()
        with zipfile.ZipFile(workbook, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/styles.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                '<Override PartName="/xl/sharedStrings.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
                + "".join(
                    f'<Override PartName="/xl/worksheets/sheet{{idx}}.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                    for idx in range(1, len(sheet_xml) + 1)
                )
                + "</Types>",
            )
            archive.writestr(
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="xl/workbook.xml"/>'
                "</Relationships>",
            )
            archive.writestr(
                "xl/workbook.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                "<sheets>"
                + "".join(
                    f'<sheet name="{{escape(name)}}" sheetId="{{idx}}" r:id="rId{{idx}}"/>'
                    for idx, (name, _) in enumerate(sheet_xml, start=1)
                )
                + "</sheets></workbook>",
            )
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + "".join(
                    f'<Relationship Id="rId{{idx}}" '
                    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                    f'Target="worksheets/sheet{{idx}}.xml"/>'
                    for idx in range(1, len(sheet_xml) + 1)
                )
                + f'<Relationship Id="rId{{len(sheet_xml) + 1}}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                'Target="styles.xml"/>'
                + f'<Relationship Id="rId{{len(sheet_xml) + 2}}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" '
                'Target="sharedStrings.xml"/>'
                + "</Relationships>",
            )
            archive.writestr(
                "xl/styles.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<numFmts count="3">'
                '<numFmt numFmtId="164" formatCode="$#,##0.00;[Red]-$#,##0.00"/>'
                '<numFmt numFmtId="165" formatCode="0.0%"/>'
                '<numFmt numFmtId="166" formatCode="#,##0"/>'
                "</numFmts>"
                '<fonts count="2">'
                '<font><sz val="11"/><name val="Aptos"/></font>'
                '<font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Aptos"/></font>'
                "</fonts>"
                '<fills count="3">'
                '<fill><patternFill patternType="none"/></fill>'
                '<fill><patternFill patternType="gray125"/></fill>'
                '<fill><patternFill patternType="solid"><fgColor rgb="FF3F51B5"/><bgColor indexed="64"/></patternFill></fill>'
                "</fills>"
                '<borders count="2">'
                '<border><left/><right/><top/><bottom/><diagonal/></border>'
                '<border><left/><right/><top style="thin"><color rgb="FFD0D7EE"/></top><bottom style="thin"><color rgb="FFD0D7EE"/></bottom><diagonal/></border>'
                "</borders>"
                '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                '<cellXfs count="5">'
                '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
                '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>'
                '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
                '<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
                '<xf numFmtId="166" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
                "</cellXfs>"
                "</styleSheet>",
            )
            archive.writestr(
                "xl/sharedStrings.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                f'count="{{len(shared_strings)}}" uniqueCount="{{len(shared_strings)}}">'
                + "".join(f"<si><t>{{escape(value)}}</t></si>" for value in shared_strings)
                + "</sst>",
            )
            for idx, (_, xml) in enumerate(sheet_xml, start=1):
                archive.writestr(f"xl/worksheets/sheet{{idx}}.xml", xml)

        payload = workbook.getvalue()
        Path(path).write_bytes(payload)
        print(
            json.dumps(
                {{
                    "file_name": workbook_name,
                    "path": path,
                    "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "size_bytes": len(payload),
                    "sheet_count": len(sheet_xml),
                    "sheet_names": [name for name, _ in sheet_xml],
                    "file_content": base64.b64encode(payload).decode("ascii"),
                }}
            )
        )
        """
    ).strip()


def build_chart_script(spec: dict[str, Any]) -> str:
    encoded = _encode_spec(spec)
    return dedent(
        f"""
        import base64
        import json
        import math
        from pathlib import Path
        from xml.sax.saxutils import escape

        SPEC = json.loads(base64.b64decode("{encoded}").decode("utf-8"))

        width = int(SPEC.get("width") or 960)
        height = int(SPEC.get("height") or 540)
        chart_type = str(SPEC.get("chart_type") or "line").lower()
        if chart_type == "column":
            chart_type = "bar"
        labels = [str(label) for label in SPEC.get("labels") or []]
        series = [item for item in SPEC.get("series") or [] if isinstance(item, dict)]
        if not labels:
            raise ValueError("labels are required")
        if not series:
            raise ValueError("series are required")

        file_name = str(SPEC.get("file_name") or "aleq-chart.svg")
        if not file_name.lower().endswith(".svg"):
            file_name += ".svg"
        path = str(SPEC.get("path") or f"/workspace/{{file_name}}")
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        title = str(SPEC.get("title") or "Aleq chart")
        subtitle = str(SPEC.get("subtitle") or "")
        x_axis_label = str(SPEC.get("x_axis_label") or "")
        y_axis_label = str(SPEC.get("y_axis_label") or "")
        palette = ["#3F51B5", "#00A896", "#FF7A59", "#6C5CE7", "#EF476F", "#118AB2"]

        values = []
        for item in series:
            row = [float(value) for value in item.get("values") or []]
            if len(row) != len(labels):
                raise ValueError("each series must have the same number of values as labels")
            values.extend(row)
        min_val = min(0.0, min(values))
        max_val = max(0.0, max(values))
        if math.isclose(max_val, min_val):
            max_val = min_val + 1.0

        margin_left = 92
        margin_right = 36
        margin_top = 92 if subtitle else 72
        margin_bottom = 84
        plot_width = width - margin_left - margin_right
        plot_height = height - margin_top - margin_bottom

        def x_for(index):
            if len(labels) == 1:
                return margin_left + plot_width / 2
            return margin_left + (plot_width * index) / (len(labels) - 1)

        def y_for(value):
            ratio = (float(value) - min_val) / (max_val - min_val)
            return margin_top + plot_height - (ratio * plot_height)

        grid_lines = []
        y_ticks = 5
        for idx in range(y_ticks + 1):
            value = min_val + ((max_val - min_val) * idx / y_ticks)
            y = y_for(value)
            grid_lines.append(f'<line x1="{{margin_left}}" y1="{{y:.2f}}" x2="{{margin_left + plot_width}}" y2="{{y:.2f}}" stroke="#E4E8F2" stroke-width="1"/>')
            grid_lines.append(f'<text x="{{margin_left - 12}}" y="{{y + 4:.2f}}" text-anchor="end" font-size="12" fill="#6A7285">{{escape(f"{{value:,.0f}}")}}</text>')

        x_labels = []
        for idx, label in enumerate(labels):
            x = x_for(idx)
            x_labels.append(f'<text x="{{x:.2f}}" y="{{margin_top + plot_height + 24}}" text-anchor="middle" font-size="12" fill="#6A7285">{{escape(label)}}</text>')

        chart_nodes = []
        if chart_type == "line":
            for idx, item in enumerate(series):
                color = str(item.get("color") or palette[idx % len(palette)])
                points = " ".join(f"{{x_for(i):.2f}},{{y_for(v):.2f}}" for i, v in enumerate(item.get("values") or []))
                chart_nodes.append(f'<polyline fill="none" stroke="{{color}}" stroke-width="3" points="{{points}}"/>')
                for point_idx, value in enumerate(item.get("values") or []):
                    chart_nodes.append(
                        f'<circle cx="{{x_for(point_idx):.2f}}" cy="{{y_for(value):.2f}}" r="4" fill="{{color}}" stroke="white" stroke-width="2"/>'
                    )
        else:
            group_width = plot_width / max(len(labels), 1)
            bar_width = min(56, max(18, group_width / max(len(series), 1) * 0.66))
            for idx, item in enumerate(series):
                color = str(item.get("color") or palette[idx % len(palette)])
                for point_idx, value in enumerate(item.get("values") or []):
                    baseline = y_for(0)
                    top = y_for(value)
                    x = margin_left + group_width * point_idx + ((group_width - (bar_width * len(series))) / 2) + (idx * bar_width)
                    y = min(top, baseline)
                    h = abs(baseline - top)
                    chart_nodes.append(
                        f'<rect x="{{x:.2f}}" y="{{y:.2f}}" width="{{bar_width - 6:.2f}}" height="{{max(h, 1):.2f}}" rx="6" fill="{{color}}" />'
                    )

        legend = []
        legend_x = margin_left
        legend_y = 24
        for idx, item in enumerate(series):
            color = str(item.get("color") or palette[idx % len(palette)])
            name = str(item.get("name") or f"Series {{idx + 1}}")
            legend.append(f'<rect x="{{legend_x}}" y="{{legend_y}}" width="12" height="12" rx="3" fill="{{color}}"/>')
            legend.append(f'<text x="{{legend_x + 18}}" y="{{legend_y + 10}}" font-size="12" fill="#4D5566">{{escape(name)}}</text>')
            legend_x += 18 + max(56, len(name) * 7)

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{{width}}" height="{{height}}" viewBox="0 0 {{width}} {{height}}" role="img">'
            f'<rect width="{{width}}" height="{{height}}" rx="24" fill="#FFFFFF"/>'
            f'<text x="{{margin_left}}" y="36" font-size="28" font-weight="700" fill="#141A24">{{escape(title)}}</text>'
            + (f'<text x="{{margin_left}}" y="58" font-size="14" fill="#6A7285">{{escape(subtitle)}}</text>' if subtitle else "")
            + "".join(legend)
            + f'<line x1="{{margin_left}}" y1="{{margin_top + plot_height}}" x2="{{margin_left + plot_width}}" y2="{{margin_top + plot_height}}" stroke="#BBC4D7" stroke-width="1.5"/>'
            + f'<line x1="{{margin_left}}" y1="{{margin_top}}" x2="{{margin_left}}" y2="{{margin_top + plot_height}}" stroke="#BBC4D7" stroke-width="1.5"/>'
            + "".join(grid_lines)
            + "".join(chart_nodes)
            + "".join(x_labels)
            + (f'<text x="{{margin_left + plot_width / 2:.2f}}" y="{{height - 18}}" text-anchor="middle" font-size="12" fill="#6A7285">{{escape(x_axis_label)}}</text>' if x_axis_label else "")
            + (f'<text x="22" y="{{margin_top + plot_height / 2:.2f}}" text-anchor="middle" font-size="12" fill="#6A7285" transform="rotate(-90 22 {{margin_top + plot_height / 2:.2f}})">{{escape(y_axis_label)}}</text>' if y_axis_label else "")
            + "</svg>"
        )
        payload = svg.encode("utf-8")
        Path(path).write_bytes(payload)
        print(
            json.dumps(
                {{
                    "file_name": file_name,
                    "path": path,
                    "mime_type": "image/svg+xml",
                    "size_bytes": len(payload),
                    "chart_type": chart_type,
                    "series_count": len(series),
                    "file_content": base64.b64encode(payload).decode("ascii"),
                }}
            )
        )
        """
    ).strip()
