# ruff: noqa: E501
"""Pure-Python PDF builders that run inside an E2B sandbox."""

from __future__ import annotations

import base64
import json
from textwrap import dedent
from typing import Any


def _encode_spec(spec: dict[str, Any]) -> str:
    payload = json.dumps(spec, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return base64.b64encode(payload).decode("ascii")


def build_pdf_script(spec: dict[str, Any]) -> str:
    encoded = _encode_spec(spec)
    return dedent(
        f"""
        import base64
        import json
        import textwrap
        from datetime import datetime, timezone
        from pathlib import Path

        SPEC = json.loads(base64.b64decode("{encoded}").decode("utf-8"))


        PAGE_WIDTH = 612
        PAGE_HEIGHT = 792
        LEFT_MARGIN = 54
        RIGHT_MARGIN = 54
        TOP_MARGIN = 54
        BOTTOM_MARGIN = 54
        CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


        def pdf_escape(text):
            value = "" if text is None else str(text)
            return (
                value.replace("\\\\", "\\\\\\\\")
                .replace("(", "\\\\(")
                .replace(")", "\\\\)")
            )


        def wrap_text(text, font_size):
            value = "" if text is None else str(text).strip()
            if not value:
                return [""]
            approx_chars = max(28, int(CONTENT_WIDTH / max(font_size * 0.52, 1)))
            wrapped = textwrap.wrap(
                value,
                width=approx_chars,
                break_long_words=False,
                break_on_hyphens=False,
            )
            return wrapped or [value]


        def push_line(items, text, *, font="body", size=12, leading=18, gap_before=0, gap_after=0):
            items.append(
                {{
                    "kind": "text",
                    "text": "" if text is None else str(text),
                    "font": font,
                    "size": size,
                    "leading": leading,
                    "gap_before": gap_before,
                    "gap_after": gap_after,
                }}
            )


        file_name = str(SPEC.get("file_name") or "aleq-report.pdf")
        if not file_name.lower().endswith(".pdf"):
            file_name += ".pdf"
        path = str(SPEC.get("path") or f"/workspace/{{file_name}}")
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        title = str(SPEC.get("title") or "Aleq report")
        subtitle = str(SPEC.get("subtitle") or "")
        author = str(SPEC.get("author") or "Aleq")
        sections = [section for section in SPEC.get("sections") or [] if isinstance(section, dict)]
        if not sections:
            raise ValueError("sections are required")

        items = []
        push_line(items, title, font="bold", size=24, leading=30, gap_after=4)
        if subtitle:
            push_line(items, subtitle, size=13, leading=19, gap_after=10)

        paragraph_count = 1 + (1 if subtitle else 0)
        for section in sections:
            heading = str(section.get("heading") or "Section")
            level = int(section.get("level") or 1)
            heading_size = 18 if level <= 1 else 16 if level == 2 else 14
            push_line(items, heading, font="bold", size=heading_size, leading=22, gap_before=8, gap_after=2)
            paragraph_count += 1

            for paragraph in section.get("paragraphs") or []:
                push_line(items, paragraph, size=12, leading=17, gap_after=4)
                paragraph_count += 1

            for bullet in section.get("bullets") or []:
                push_line(items, f"• {{bullet}}", size=12, leading=17, gap_after=2)
                paragraph_count += 1

            table = section.get("table")
            if isinstance(table, dict):
                columns = [str(column) for column in table.get("columns") or []]
                rows = list(table.get("rows") or [])
                if not columns and rows and isinstance(rows[0], dict):
                    columns = [str(key) for key in rows[0].keys()]
                if columns:
                    push_line(items, " | ".join(columns), font="bold", size=11, leading=15, gap_before=4)
                    paragraph_count += 1
                for row in rows:
                    if isinstance(row, dict):
                        values = [row.get(column, "") for column in columns]
                    elif isinstance(row, list):
                        values = row
                    else:
                        values = [row]
                    push_line(
                        items,
                        " | ".join("" if value is None else str(value) for value in values),
                        size=11,
                        leading=15,
                    )
                    paragraph_count += 1
                push_line(items, "", size=8, leading=10, gap_after=2)

        pages = []
        current_page = []
        current_y = PAGE_HEIGHT - TOP_MARGIN


        for item in items:
            current_y -= item.get("gap_before", 0)
            lines = wrap_text(item["text"], item["size"])
            required_height = len(lines) * item["leading"] + item.get("gap_after", 0)
            if current_y - required_height < BOTTOM_MARGIN:
                if current_page:
                    pages.append(current_page)
                current_page = []
                current_y = PAGE_HEIGHT - TOP_MARGIN
            for line in lines:
                current_page.append(
                    {{
                        "text": line,
                        "font": item["font"],
                        "size": item["size"],
                        "x": LEFT_MARGIN,
                        "y": current_y,
                    }}
                )
                current_y -= item["leading"]
            current_y -= item.get("gap_after", 0)

        if current_page:
            pages.append(current_page)

        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


        def build_content_stream(page_lines):
            commands = ["BT"]
            for line in page_lines:
                font_key = "/F2" if line["font"] == "bold" else "/F1"
                commands.append(f"{{font_key}} {{line['size']}} Tf")
                commands.append(f"1 0 0 1 {{line['x']}} {{line['y']}} Tm")
                commands.append(f"({{pdf_escape(line['text'])}}) Tj")
            commands.append("ET")
            return "\\n".join(commands).encode("latin-1", errors="replace")


        objects = []

        def add_object(payload):
            objects.append(payload)
            return len(objects)


        catalog_id = add_object(None)
        pages_id = add_object(None)
        font_body_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        font_bold_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

        page_ids = []
        for page in pages:
            content = build_content_stream(page)
            content_id = add_object(
                b"<< /Length "
                + str(len(content)).encode("ascii")
                + b" >>\\nstream\\n"
                + content
                + b"\\nendstream"
            )
            page_id = add_object(
                (
                    f"<< /Type /Page /Parent {{pages_id}} 0 R "
                    f"/MediaBox [0 0 {{PAGE_WIDTH}} {{PAGE_HEIGHT}}] "
                    f"/Resources << /Font << /F1 {{font_body_id}} 0 R /F2 {{font_bold_id}} 0 R >> >> "
                    f"/Contents {{content_id}} 0 R >>"
                ).encode("ascii")
            )
            page_ids.append(page_id)

        kids = " ".join(f"{{page_id}} 0 R" for page_id in page_ids)
        objects[pages_id - 1] = (
            f"<< /Type /Pages /Count {{len(page_ids)}} /Kids [{{kids}}] >>"
        ).encode("ascii")
        objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {{pages_id}} 0 R >>".encode("ascii")

        info_id = add_object(
            (
                f"<< /Title ({{pdf_escape(title)}}) /Author ({{pdf_escape(author)}}) "
                f"/Creator (Aleq) /Producer (Aleq) /CreationDate (D:{{timestamp.replace('-', '').replace(':', '').replace('T', '').replace('Z', 'Z')}}) >>"
            ).encode("latin-1", errors="replace")
        )

        output = bytearray(b"%PDF-1.4\\n%\\xe2\\xe3\\xcf\\xd3\\n")
        offsets = []
        for idx, payload in enumerate(objects, start=1):
            offsets.append(len(output))
            output.extend(f"{{idx}} 0 obj\\n".encode("ascii"))
            output.extend(payload)
            output.extend(b"\\nendobj\\n")

        xref_offset = len(output)
        output.extend(f"xref\\n0 {{len(objects) + 1}}\\n".encode("ascii"))
        output.extend(b"0000000000 65535 f \\n")
        for offset in offsets:
            output.extend(f"{{offset:010d}} 00000 n \\n".encode("ascii"))
        output.extend(
            (
                f"trailer\\n<< /Size {{len(objects) + 1}} /Root {{catalog_id}} 0 R /Info {{info_id}} 0 R >>\\n"
                f"startxref\\n{{xref_offset}}\\n%%EOF\\n"
            ).encode("ascii")
        )

        Path(path).write_bytes(bytes(output))

        payload = {{
            "file_name": file_name,
            "path": path,
            "mime_type": "application/pdf",
            "size_bytes": len(output),
            "page_count": len(page_ids),
            "section_count": len(sections),
            "paragraph_count": paragraph_count,
            "file_content": base64.b64encode(bytes(output)).decode("ascii"),
        }}
        print(json.dumps(payload))
        """
    )
