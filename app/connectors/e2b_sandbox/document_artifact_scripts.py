# ruff: noqa: E501
"""Pure-Python DOCX builders that run inside an E2B sandbox."""

from __future__ import annotations

import base64
import json
from textwrap import dedent
from typing import Any


def _encode_spec(spec: dict[str, Any]) -> str:
    payload = json.dumps(spec, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return base64.b64encode(payload).decode("ascii")


def build_docx_script(spec: dict[str, Any]) -> str:
    encoded = _encode_spec(spec)
    return dedent(
        f"""
        import base64
        import io
        import json
        import zipfile
        from datetime import datetime, timezone
        from pathlib import Path
        from xml.sax.saxutils import escape

        SPEC = json.loads(base64.b64decode("{encoded}").decode("utf-8"))


        def text_runs(text):
            value = "" if text is None else str(text)
            parts = value.split("\\n")
            runs = []
            for index, part in enumerate(parts):
                runs.append(f'<w:r><w:t xml:space="preserve">{{escape(part)}}</w:t></w:r>')
                if index < len(parts) - 1:
                    runs.append("<w:r><w:br/></w:r>")
            return "".join(runs)


        def paragraph(text, style="BodyText"):
            return (
                "<w:p>"
                f'<w:pPr><w:pStyle w:val="{{style}}"/></w:pPr>'
                f"{{text_runs(text)}}"
                "</w:p>"
            )


        def table_xml(table_spec):
            columns = [str(column) for column in table_spec.get("columns") or []]
            rows = list(table_spec.get("rows") or [])
            if not columns and rows and isinstance(rows[0], dict):
                columns = [str(key) for key in rows[0].keys()]
            if not columns:
                columns = ["Value"]

            def row_values(row):
                if isinstance(row, dict):
                    return [row.get(column) for column in columns]
                if isinstance(row, list):
                    return row[: len(columns)] + [None] * max(0, len(columns) - len(row))
                return [row] + [None] * max(0, len(columns) - 1)

            grid = "".join('<w:gridCol w:w="2400"/>' for _ in columns)
            cells = []
            header_cells = "".join(
                "<w:tc>"
                '<w:tcPr><w:tcW w:w="2400" w:type="dxa"/></w:tcPr>'
                f"{{paragraph(column, 'TableHeader')}}"
                "</w:tc>"
                for column in columns
            )
            cells.append(f"<w:tr>{{header_cells}}</w:tr>")

            for row in rows:
                row_cells = []
                for value in row_values(row):
                    row_cells.append(
                        "<w:tc>"
                        '<w:tcPr><w:tcW w:w="2400" w:type="dxa"/></w:tcPr>'
                        f"{{paragraph('' if value is None else value, 'BodyText')}}"
                        "</w:tc>"
                    )
                cells.append("<w:tr>" + "".join(row_cells) + "</w:tr>")

            return (
                "<w:tbl>"
                "<w:tblPr>"
                '<w:tblStyle w:val="AleqTable"/>'
                '<w:tblW w:w="0" w:type="auto"/>'
                "<w:tblBorders>"
                '<w:top w:val="single" w:sz="8" w:space="0" w:color="D0D7EE"/>'
                '<w:left w:val="single" w:sz="8" w:space="0" w:color="D0D7EE"/>'
                '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="D0D7EE"/>'
                '<w:right w:val="single" w:sz="8" w:space="0" w:color="D0D7EE"/>'
                '<w:insideH w:val="single" w:sz="6" w:space="0" w:color="E6EAF5"/>'
                '<w:insideV w:val="single" w:sz="6" w:space="0" w:color="E6EAF5"/>'
                "</w:tblBorders>"
                "</w:tblPr>"
                f"<w:tblGrid>{{grid}}</w:tblGrid>"
                + "".join(cells)
                + "</w:tbl>"
            )


        file_name = str(SPEC.get("file_name") or "aleq-document.docx")
        if not file_name.lower().endswith(".docx"):
            file_name += ".docx"
        path = str(SPEC.get("path") or f"/workspace/{{file_name}}")
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        title = str(SPEC.get("title") or "Aleq document")
        subtitle = str(SPEC.get("subtitle") or "")
        author = str(SPEC.get("author") or "Aleq")
        sections = [section for section in SPEC.get("sections") or [] if isinstance(section, dict)]
        if not sections:
            raise ValueError("sections are required")

        body = [paragraph(title, "Title")]
        if subtitle:
            body.append(paragraph(subtitle, "Subtitle"))

        paragraph_count = 1 + (1 if subtitle else 0)
        for section in sections:
            heading = str(section.get("heading") or "Section")
            level = int(section.get("level") or 1)
            style = "Heading1" if level <= 1 else "Heading2" if level == 2 else "Heading3"
            body.append(paragraph(heading, style))
            paragraph_count += 1

            for item in section.get("paragraphs") or []:
                body.append(paragraph(item, "BodyText"))
                paragraph_count += 1

            for bullet in section.get("bullets") or []:
                body.append(paragraph(f"• {{bullet}}", "BodyText"))
                paragraph_count += 1

            table = section.get("table")
            if isinstance(table, dict):
                body.append(table_xml(table))

        body.append(
            '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
            '<w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080" '
            'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
        )

        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        document_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
            'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
            'xmlns:o="urn:schemas-microsoft-com:office:office" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
            'xmlns:v="urn:schemas-microsoft-com:vml" '
            'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
            'xmlns:w10="urn:schemas-microsoft-com:office:word" '
            'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
            'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
            'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
            'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
            'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
            'mc:Ignorable="w14 wp14">'
            '<w:body>'
            + "".join(body)
            + "</w:body></w:document>"
        )

        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/>'
            '<w:sz w:val="22"/><w:szCs w:val="22"/><w:color w:val="1B2230"/></w:rPr>'
            '</w:rPrDefault></w:docDefaults>'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
            '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/>'
            '<w:pPr><w:spacing w:before="0" w:after="160"/></w:pPr>'
            '<w:rPr><w:b/><w:color w:val="141A24"/><w:sz w:val="36"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/>'
            '<w:pPr><w:spacing w:before="0" w:after="240"/></w:pPr>'
            '<w:rPr><w:color w:val="6A7285"/><w:sz w:val="24"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/>'
            '<w:pPr><w:spacing w:before="280" w:after="120"/></w:pPr>'
            '<w:rPr><w:b/><w:color w:val="1B2230"/><w:sz w:val="30"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/>'
            '<w:pPr><w:spacing w:before="220" w:after="80"/></w:pPr>'
            '<w:rPr><w:b/><w:color w:val="243040"/><w:sz w:val="26"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="Heading 3"/><w:basedOn w:val="Normal"/>'
            '<w:pPr><w:spacing w:before="180" w:after="60"/></w:pPr>'
            '<w:rPr><w:b/><w:color w:val="334155"/><w:sz w:val="24"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/><w:basedOn w:val="Normal"/>'
            '<w:pPr><w:spacing w:before="0" w:after="100" w:line="320" w:lineRule="auto"/></w:pPr>'
            '<w:rPr><w:color w:val="334155"/><w:sz w:val="22"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="TableHeader"><w:name w:val="Table Header"/><w:basedOn w:val="BodyText"/>'
            '<w:rPr><w:b/><w:color w:val="141A24"/></w:rPr></w:style>'
            '<w:style w:type="table" w:styleId="AleqTable"><w:name w:val="Aleq Table"/></w:style>'
            "</w:styles>"
        )

        core_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<dc:title>{{escape(title)}}</dc:title>"
            f"<dc:creator>{{escape(author)}}</dc:creator>"
            "<cp:lastModifiedBy>Aleq</cp:lastModifiedBy>"
            '<dcterms:created xsi:type="dcterms:W3CDTF">'
            f"{{timestamp}}</dcterms:created>"
            '<dcterms:modified xsi:type="dcterms:W3CDTF">'
            f"{{timestamp}}</dcterms:modified>"
            "</cp:coreProperties>"
        )

        app_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
            'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            "<Application>Aleq</Application><DocSecurity>0</DocSecurity><Pages>1</Pages>"
            "<Words>0</Words><Characters>0</Characters><Lines>0</Lines><Paragraphs>"
            f"{{paragraph_count}}</Paragraphs></Properties>"
        )

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                '<Override PartName="/word/styles.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                '<Override PartName="/docProps/core.xml" '
                'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                '<Override PartName="/docProps/app.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
                "</Types>",
            )
            archive.writestr(
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="word/document.xml"/>'
                '<Relationship Id="rId2" '
                'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
                'Target="docProps/core.xml"/>'
                '<Relationship Id="rId3" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
                'Target="docProps/app.xml"/>'
                "</Relationships>",
            )
            archive.writestr(
                "word/_rels/document.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                'Target="styles.xml"/>'
                "</Relationships>",
            )
            archive.writestr("word/document.xml", document_xml)
            archive.writestr("word/styles.xml", styles_xml)
            archive.writestr("docProps/core.xml", core_xml)
            archive.writestr("docProps/app.xml", app_xml)

        payload = buffer.getvalue()
        Path(path).write_bytes(payload)
        print(
            json.dumps(
                {{
                    "file_name": file_name,
                    "path": path,
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "size_bytes": len(payload),
                    "section_count": len(sections),
                    "paragraph_count": paragraph_count,
                    "file_content": base64.b64encode(payload).decode("ascii"),
                }}
            )
        )
        """
    ).strip()
