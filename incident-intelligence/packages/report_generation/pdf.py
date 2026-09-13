from __future__ import annotations

from datetime import datetime, timezone
import textwrap


def structured_report_pdf(report: dict, *, confidentiality: str) -> bytes:
    """Create a deterministic, dependency-free PDF from the structured report snapshot."""
    lines = [
        f"{confidentiality}",
        f"Incident Diagnostic — {report['incident']['title']}",
        f"Report version {report['version']} | Template {report['template']['profile']} {report['template']['version']}",
        f"Generated {report['provenance']['generated_at']}", "",
        "Executive summary", report['incident']['description'] or "No executive summary supplied.", "",
        f"Impact: {report['incident']['business_impact'] or 'Not quantified.'}",
        f"Unplanned downtime: {report['metrics']['unplanned_downtime_seconds']} seconds", "",
        "Hypotheses",
    ]
    for item in report["hypotheses"]:
        lines.append(f"[{item['evidence_reference']}] {item['title']} — confidence {item['confidence']:.2f}")
    lines.extend(["", "Timeline (each row cites immutable evidence)"])
    for item in report["timeline"][:100]:
        citation = (item.get("raw_evidence") or {}).get("raw_record_id", "analyst-entry")
        lines.append(f"{item.get('occurred_at')} [{citation}] {item.get('event_code') or item.get('title','')} {item.get('message') or item.get('annotation','')}")
    lines.extend(["", "Limitations"])
    lines.extend(item["description"] for item in report["data_quality"]["issues"] or [{"description": "No automated issue recorded."}])
    wrapped = [part for line in lines for part in (textwrap.wrap(str(line), width=94) or [""])]
    pages = [wrapped[index:index + 48] for index in range(0, len(wrapped), 48)] or [[]]
    return _pdf_pages(pages, confidentiality)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_pages(pages: list[list[str]], footer: str) -> bytes:
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_ids = [3 + index * 2 for index in range(len(pages))]
    objects.append(f"<< /Type /Pages /Kids [{' '.join(f'{item} 0 R' for item in page_ids)}] /Count {len(pages)} >>".encode())
    font_id = 3 + len(pages) * 2
    for index, lines in enumerate(pages, start=1):
        page_id = page_ids[index - 1]; content_id = page_id + 1
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode())
        commands = ["BT /F1 9 Tf 48 750 Td 12 TL"]
        for line in lines: commands.append(f"({_escape(line)}) Tj T*")
        commands.extend([f"0 -20 Td ({_escape(footer)} — Page {index}/{len(pages)}) Tj", "ET"])
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output)); output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output); output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]: output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(output)
