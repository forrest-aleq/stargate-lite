# ruff: noqa: E501
"""Pure-Python PPTX builders that run inside an E2B sandbox."""

from __future__ import annotations

import base64
import json
from textwrap import dedent
from typing import Any


def _encode_spec(spec: dict[str, Any]) -> str:
    payload = json.dumps(spec, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return base64.b64encode(payload).decode("ascii")


def build_pptx_script(spec: dict[str, Any]) -> str:
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

        file_name = str(SPEC.get("file_name") or "aleq-deck.pptx")
        if not file_name.lower().endswith(".pptx"):
            file_name += ".pptx"
        path = str(SPEC.get("path") or f"/workspace/{{file_name}}")
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        title = str(SPEC.get("title") or "Aleq presentation")
        author = str(SPEC.get("author") or "Aleq")
        slides = [slide for slide in SPEC.get("slides") or [] if isinstance(slide, dict)]
        if not slides:
            raise ValueError("slides are required")


        def run_paragraph(text, level=0, *, bold=False, size=2400, color="2B3445"):
            content = escape("" if text is None else str(text))
            return (
                f'<a:p><a:pPr lvl="{{level}}"/>'
                f'<a:r><a:rPr lang="en-US" dirty="0" sz="{{size}}" b="{{1 if bold else 0}}">'
                f'<a:solidFill><a:srgbClr val="{{color}}"/></a:solidFill></a:rPr>'
                f'<a:t>{{content}}</a:t></a:r></a:p>'
            )


        def text_body(paragraphs):
            return (
                '<p:txBody><a:bodyPr/><a:lstStyle/>'
                + "".join(paragraphs)
                + "</p:txBody>"
            )


        def title_shape(text):
            paragraphs = [run_paragraph(text or "", bold=True, size=2800, color="141A24")]
            return (
                '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/>'
                '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                '<p:spPr><a:xfrm><a:off x="685800" y="457200"/>'
                '<a:ext cx="10922000" cy="914400"/></a:xfrm></p:spPr>'
                + text_body(paragraphs)
                + "</p:sp>"
            )


        def body_shape(paragraphs, shape_id):
            return (
                f'<p:sp><p:nvSpPr><p:cNvPr id="{{shape_id}}" name="Content {{shape_id}}"/>'
                '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                '<p:spPr><a:xfrm><a:off x="685800" y="1600200"/>'
                '<a:ext cx="7810500" cy="4114800"/></a:xfrm>'
                '<a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>'
                '<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
                '<a:ln w="12700"><a:solidFill><a:srgbClr val="E2E8F0"/></a:solidFill></a:ln>'
                '</p:spPr>'
                + text_body(paragraphs)
                + "</p:sp>"
            )


        def accent_shape(lines, shape_id):
            return (
                f'<p:sp><p:nvSpPr><p:cNvPr id="{{shape_id}}" name="Accent {{shape_id}}"/>'
                '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                '<p:spPr><a:xfrm><a:off x="8839200" y="1600200"/>'
                '<a:ext cx="2336800" cy="4114800"/></a:xfrm>'
                '<a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>'
                '<a:solidFill><a:srgbClr val="F6F8FC"/></a:solidFill>'
                '<a:ln w="12700"><a:solidFill><a:srgbClr val="D7DEEF"/></a:solidFill></a:ln>'
                '</p:spPr>'
                + text_body(lines)
                + "</p:sp>"
            )


        def slide_xml(slide, index):
            slide_title = str(slide.get("title") or f"Slide {{index}}")
            bullets = [str(item) for item in slide.get("bullets") or []]
            paragraphs = [str(item) for item in slide.get("paragraphs") or []]
            metrics = [item for item in slide.get("metrics") or [] if isinstance(item, dict)]
            body_lines = []
            for text in paragraphs:
                body_lines.append(run_paragraph(text))
            for bullet in bullets:
                body_lines.append(run_paragraph("• " + bullet, level=0))
            if not body_lines:
                body_lines.append(run_paragraph(" "))

            accent_lines = []
            subtitle = str(slide.get("subtitle") or "")
            if subtitle:
                accent_lines.append(run_paragraph(subtitle, bold=True, size=1800, color="3F51B5"))
            for metric in metrics[:4]:
                label = str(metric.get("label") or "Metric")
                value = str(metric.get("value") or "")
                accent_lines.append(run_paragraph(label, bold=True, size=1700, color="6A7285"))
                accent_lines.append(run_paragraph(value, bold=True, size=2400, color="141A24"))
            if not accent_lines:
                accent_lines.append(run_paragraph("Aleq", bold=True, size=1800, color="3F51B5"))
                accent_lines.append(run_paragraph("Generated in sandbox", size=1700, color="6A7285"))

            return (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                '<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
                '</p:bgPr></p:bg><p:spTree>'
                '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
                '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
                + title_shape(slide_title)
                + body_shape(body_lines, 3)
                + accent_shape(accent_lines, 4)
                + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
            )


        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        slide_payloads = [slide_xml(slide, idx) for idx, slide in enumerate(slides, start=1)]

        presentation_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
            '<p:sldIdLst>'
            + "".join(
                f'<p:sldId id="{{256 + idx}}" r:id="rId{{idx + 1}}"/>'
                for idx in range(1, len(slide_payloads) + 1)
            )
            + '</p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>'
        )

        presentation_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
            'Target="slideMasters/slideMaster1.xml"/>'
            + "".join(
                f'<Relationship Id="rId{{idx + 1}}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
                f'Target="slides/slide{{idx}}.xml"/>'
                for idx in range(1, len(slide_payloads) + 1)
            )
            + "</Relationships>"
        )

        slide_master_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld name="Aleq Master"><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
            '</p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
            '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
            '</a:xfrm></p:grpSpPr></p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
            'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            '<p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst>'
            '<p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>'
        )

        slide_master_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
            'Target="../slideLayouts/slideLayout1.xml"/>'
            '<Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" '
            'Target="../theme/theme1.xml"/>'
            "</Relationships>"
        )

        slide_layout_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="titleAndContent" preserve="1">'
            '<p:cSld name="Aleq Layout"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
            '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
            '</a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/>'
            '</p:clrMapOvr></p:sldLayout>'
        )

        slide_layout_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
            'Target="../slideMasters/slideMaster1.xml"/>'
            "</Relationships>"
        )

        theme_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Aleq Theme">'
            '<a:themeElements><a:clrScheme name="Aleq Colors">'
            '<a:dk1><a:srgbClr val="141A24"/></a:dk1>'
            '<a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
            '<a:dk2><a:srgbClr val="243040"/></a:dk2>'
            '<a:lt2><a:srgbClr val="F7F8FC"/></a:lt2>'
            '<a:accent1><a:srgbClr val="3F51B5"/></a:accent1>'
            '<a:accent2><a:srgbClr val="00A896"/></a:accent2>'
            '<a:accent3><a:srgbClr val="FF7A59"/></a:accent3>'
            '<a:accent4><a:srgbClr val="6C5CE7"/></a:accent4>'
            '<a:accent5><a:srgbClr val="118AB2"/></a:accent5>'
            '<a:accent6><a:srgbClr val="EF476F"/></a:accent6>'
            '<a:hlink><a:srgbClr val="3F51B5"/></a:hlink>'
            '<a:folHlink><a:srgbClr val="6C5CE7"/></a:folHlink></a:clrScheme>'
            '<a:fontScheme name="Aleq Fonts"><a:majorFont><a:latin typeface="Aptos Display"/>'
            '</a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme>'
            '<a:fmtScheme name="Aleq Format"/></a:themeElements></a:theme>'
        )

        core_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<dc:title>{{escape(title)}}</dc:title><dc:creator>{{escape(author)}}</dc:creator>"
            "<cp:lastModifiedBy>Aleq</cp:lastModifiedBy>"
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{{timestamp}}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{{timestamp}}</dcterms:modified>'
            "</cp:coreProperties>"
        )

        app_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
            'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            "<Application>Aleq</Application><Slides>"
            f"{{len(slide_payloads)}}"
            "</Slides><Notes>0</Notes><HiddenSlides>0</HiddenSlides></Properties>"
        )

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/ppt/presentation.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
                '<Override PartName="/ppt/slideMasters/slideMaster1.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
                '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
                '<Override PartName="/ppt/theme/theme1.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
                + "".join(
                    f'<Override PartName="/ppt/slides/slide{{idx}}.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
                    for idx in range(1, len(slide_payloads) + 1)
                )
                + '<Override PartName="/docProps/core.xml" '
                'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                + '<Override PartName="/docProps/app.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
                + "</Types>",
            )
            archive.writestr(
                "_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="ppt/presentation.xml"/>'
                '<Relationship Id="rId2" '
                'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
                'Target="docProps/core.xml"/>'
                '<Relationship Id="rId3" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
                'Target="docProps/app.xml"/>'
                "</Relationships>",
            )
            archive.writestr("ppt/presentation.xml", presentation_xml)
            archive.writestr("ppt/_rels/presentation.xml.rels", presentation_rels)
            archive.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml)
            archive.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels)
            archive.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout_xml)
            archive.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels)
            archive.writestr("ppt/theme/theme1.xml", theme_xml)
            archive.writestr("docProps/core.xml", core_xml)
            archive.writestr("docProps/app.xml", app_xml)
            for idx, slide_xml_payload in enumerate(slide_payloads, start=1):
                archive.writestr(f"ppt/slides/slide{{idx}}.xml", slide_xml_payload)
                archive.writestr(
                    f"ppt/slides/_rels/slide{{idx}}.xml.rels",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    '<Relationship Id="rId1" '
                    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
                    'Target="../slideLayouts/slideLayout1.xml"/>'
                    "</Relationships>",
                )

        payload = buffer.getvalue()
        Path(path).write_bytes(payload)
        print(
            json.dumps(
                {{
                    "file_name": file_name,
                    "path": path,
                    "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    "size_bytes": len(payload),
                    "slide_count": len(slides),
                    "file_content": base64.b64encode(payload).decode("ascii"),
                }}
            )
        )
        """
    ).strip()
