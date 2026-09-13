#!/usr/bin/env python3
"""Generate the committed synthetic buyer sample from one structured snapshot."""
from __future__ import annotations

import csv
from hashlib import sha256
import html
import io
import json
from pathlib import Path
import sys
import zipfile

LABEL = "SYNTHETIC DEMONSTRATION — NOT CUSTOMER DATA"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/sample_diagnostic"
sys.path.insert(0, str(ROOT))

from packages.report_generation.pdf import structured_report_pdf


REPORT = {
    "schema_version": "diagnostic_report.v1",
    "version": 1,
    "template": {"profile": "technical", "version": "report.v1", "generator_version": "rfii-sample.v1"},
    "status": "demonstration",
    "incident": {
        "id": "SYN-DOOR-001", "title": "Door interlock delayed robot route recovery",
        "description": "A synthetic robot stopped at a controlled door after the fleet route request preceded the door-open confirmation. The available evidence supports an interlock delay as the leading hypothesis, while a Wi-Fi interruption remains an explicitly reviewed alternative.",
        "business_impact": "One synthetic transport task paused for 214 seconds; no safety event or customer production impact is represented.",
        "started_at": "2026-01-15T10:02:11Z", "recovered_at": "2026-01-15T10:05:45Z",
    },
    "metrics": {"unplanned_downtime_seconds": 214, "technical_recovery_seconds": 151, "business_recovery_seconds": 214},
    "hypotheses": [
        {"evidence_reference": "HYP-SYN-001", "title": "Door interlock response delay", "confidence": 0.74, "status": "analyst-supported"},
        {"evidence_reference": "HYP-SYN-002", "title": "Wi-Fi roaming interruption", "confidence": 0.28, "status": "alternative"},
    ],
    "timeline": [
        {"occurred_at": "2026-01-15T10:02:11Z", "event_code": "BLOCKED_PATH", "message": "Robot stopped before Door D-17", "source": "robot export", "raw_evidence": {"raw_record_id": "RAW-SYN-001"}},
        {"occurred_at": "2026-01-15T10:02:13Z", "event_code": "DOOR_RELEASE", "message": "Fleet requested door release", "source": "fleet export", "raw_evidence": {"raw_record_id": "RAW-SYN-002"}},
        {"occurred_at": "2026-01-15T10:02:31Z", "event_code": "DOOR_OPEN", "message": "PLC confirmed open state", "source": "door PLC export", "raw_evidence": {"raw_record_id": "RAW-SYN-003"}},
        {"occurred_at": "2026-01-15T10:04:42Z", "event_code": "MISSION_RESUMED", "message": "Robot navigation resumed", "source": "robot export", "raw_evidence": {"raw_record_id": "RAW-SYN-004"}},
        {"occurred_at": "2026-01-15T10:05:45Z", "event_code": "TASK_RESUMED", "message": "Synthetic transport workflow recovered", "source": "WCS export", "raw_evidence": {"raw_record_id": "RAW-SYN-005"}},
    ],
    "evidence": [
        {"reference": "EV-SYN-001", "relation": "supports", "note": "18-second release-to-open interval overlaps the stop."},
        {"reference": "EV-SYN-002", "relation": "contradicts", "note": "No packet-loss record exists in the available synthetic Wi-Fi window."},
        {"reference": "EV-SYN-003", "relation": "missing_expected", "note": "Door controller diagnostic trace was intentionally omitted from the fixture."},
    ],
    "data_quality": {"issues": [
        {"description": "The synthetic PLC clock has a reviewed +850 ms offset; close ordering is marked uncertain."},
        {"description": "The controller diagnostic trace is missing, limiting causal certainty."},
    ]},
    "provenance": {"generated_by": "sample-generator", "generated_at": "2026-07-19T00:00:00Z"},
}


def markdown() -> str:
    lines = [f"# {LABEL}", "", f"# Diagnostic report: {REPORT['incident']['title']}", "", "## Executive summary", "", REPORT["incident"]["description"], "", "## Operational impact", "", REPORT["incident"]["business_impact"], "", "## Downtime and recovery", "", "- Unplanned downtime: 214 seconds", "- Technical recovery: 151 seconds", "- Business recovery: 214 seconds", "", "## Hypotheses"]
    lines += [f"- [{item['evidence_reference']}] {item['title']}: {item['confidence']:.2f} ({item['status']})" for item in REPORT["hypotheses"]]
    lines += ["", "## Evidence and limitations"]
    lines += [f"- [{item['reference']}] {item['relation']}: {item['note']}" for item in REPORT["evidence"]]
    lines += ["", "## Reconstructed timeline", "", "See `timeline.csv`; every row cites synthetic raw evidence.", "", "## Provenance", "", "Generated deterministically from `scripts/generate_sample_diagnostic.py`. This artifact demonstrates product format and is not a validated customer outcome.", ""]
    return "\n".join(lines)


def timeline_csv() -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["demonstration_label", "occurred_at", "source", "event_code", "message", "raw_record_id"])
    for row in REPORT["timeline"]:
        writer.writerow([LABEL, row["occurred_at"], row["source"], row["event_code"], row["message"], row["raw_evidence"]["raw_record_id"]])
    return output.getvalue().encode()


def zip_bytes(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    return output.getvalue()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report_json = {"demonstration_label": LABEL, **REPORT}
    md = markdown().encode()
    body = "\n".join(f"<h2>{html.escape(line.lstrip('# '))}</h2>" if line.startswith("##") else f"<h1>{html.escape(line.lstrip('# '))}</h1>" if line.startswith("#") else f"<p>{html.escape(line)}</p>" for line in md.decode().splitlines() if line)
    html_bytes = f"<!doctype html><meta charset='utf-8'><title>Synthetic diagnostic</title><style>body{{font:16px system-ui;max-width:960px;margin:2rem auto;line-height:1.55}}h1,h2{{color:#17365d}}body:before{{content:'{LABEL}';display:block;background:#fff3cd;padding:1rem;font-weight:700}}</style><body>{body}</body>".encode()
    timeline = timeline_csv()
    manifest = {"demonstration_label": LABEL, "schema_version": "evidence_manifest.v1", "files": [{"id": row["raw_evidence"]["raw_record_id"], "source": row["source"], "synthetic": True} for row in REPORT["timeline"]]}
    package = zip_bytes({"README.txt": (LABEL + "\nSelected synthetic evidence only.\n").encode(), "incident_summary.md": md, "timeline.csv": timeline, "evidence_manifest.json": json.dumps(manifest, indent=2).encode(), "questions_for_vendor.md": (f"# {LABEL}\n\n1. Does the synthetic chronology match expected door behavior?\n2. Which missing controller trace would confirm or reject the leading hypothesis?\n").encode()})
    artifacts = {
        "diagnostic_report.json": json.dumps(report_json, indent=2, sort_keys=True).encode(),
        "diagnostic_report.md": md, "diagnostic_report.html": html_bytes,
        "diagnostic_report.pdf": structured_report_pdf(REPORT, confidentiality=LABEL),
        "timeline.csv": timeline, "evidence_manifest.json": json.dumps(manifest, indent=2, sort_keys=True).encode(),
        "vendor_support_package.zip": package,
        "walkthrough.md": (f"# {LABEL}\n\nOpen `diagnostic_report.html` for the buyer-facing view, inspect `timeline.csv` for event provenance, compare the leading and alternative hypotheses, review missing evidence, then inspect the minimal vendor ZIP. All names, timestamps, events, and impacts are synthetic.\n").encode(),
    }
    hashes = []
    for name, content in artifacts.items():
        (OUTPUT / name).write_bytes(content); hashes.append(f"{sha256(content).hexdigest()}  {name}")
    (OUTPUT / "SHA256SUMS").write_text("\n".join(hashes) + "\n")


if __name__ == "__main__":
    main()
