from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
import html
import io
import json
from pathlib import Path
import re
import zipfile
import yaml

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.audit import audit
from packages.data_quality import assess_incident
from packages.domain_models.models import (
    Asset,
    CanonicalEvent,
    DataSource,
    DowntimeSegment,
    EvidenceLink,
    Incident,
    HypothesisReview,
    RawRecord,
    RedactionAudit,
    RecoveryAction,
    ReportArtifact,
    RootCauseHypothesis,
)
from packages.incident_engine import calculate_metrics
from packages.timeline_engine import TimelineFilters, build_timeline
from .pdf import structured_report_pdf
from .redaction import redact


ROOT = Path(__file__).resolve().parents[2]
REPORT_PROFILE_CONFIG = yaml.safe_load((ROOT / "config/report_profiles.yaml").read_text())


REPORT_SECTIONS = [
    "Executive summary", "Incident scope", "Operational impact", "Systems and assets involved",
    "Source inventory", "Reconstructed timeline", "Downtime and recovery metrics", "Most likely cause",
    "Alternative hypotheses", "Supporting evidence", "Contradicting evidence", "Missing evidence",
    "Data-quality limitations", "Corrective actions", "Recurrence risk", "Vendor-support recommendations",
    "Appendix", "Audit and provenance",
]


def _json_safe(value):
    if isinstance(value, datetime): return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict): return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list): return [_json_safe(item) for item in value]
    return value


def _digest(content: bytes) -> str:
    return sha256(content).hexdigest()


def _timeline_csv(timeline: list[dict]) -> bytes:
    output = io.StringIO(newline="")
    fields = ["occurred_at", "entry_type", "source", "asset_id", "severity", "event_code", "message", "time_quality", "raw_record_id"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for item in timeline:
        writer.writerow({key: _csv_safe(value) for key, value in {
            "occurred_at": _json_safe(item.get("occurred_at")),
            "entry_type": item.get("entry_type", ""),
            "source": (item.get("source") or {}).get("name", ""),
            "asset_id": item.get("asset_id", ""),
            "severity": item.get("severity", ""),
            "event_code": item.get("event_code", ""),
            "message": item.get("message", item.get("annotation", "")),
            "time_quality": item.get("time_quality", ""),
            "raw_record_id": (item.get("raw_evidence") or {}).get("raw_record_id", ""),
        }.items()})
    return output.getvalue().encode()


def _csv_safe(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _markdown(report: dict) -> str:
    hypotheses = report["hypotheses"]
    primary = hypotheses[0] if hypotheses else None
    lines = [f"# Diagnostic report: {report['incident']['title']}", "", f"Report version: {report['version']}", "", "## 1. Executive summary", "", report["incident"]["description"] or "Historical incident reconstructed from the available evidence.", "", "## 2. Incident scope", "", f"Window: {report['incident']['started_at']} to {report['incident']['recovered_at'] or 'open'}", "", "## 3. Operational impact", "", report["incident"]["business_impact"] or "Not quantified by the analyst.", "", "## 4. Systems and assets involved", ""]
    lines.extend(f"- {item['name']} ({item['asset_type']})" for item in report["assets"] or [{"name": "No mapped assets", "asset_type": "unknown"}])
    lines.extend(["", "## 5. Source inventory", ""])
    lines.extend(f"- {item['name']}: {item['source_type']}" for item in report["sources"])
    lines.extend(["", "## 6. Reconstructed timeline", "", f"{len(report['timeline'])} entries; see `timeline.csv`.", "", "## 7. Downtime and recovery metrics", "", f"Unplanned downtime: {report['metrics']['unplanned_downtime_seconds']} seconds", "", "## 8. Most likely cause", ""])
    lines.append(f"[{primary['evidence_reference']}] {primary['title']} (confidence {primary['confidence']:.2f}, status {primary['status']})" if primary else "No analyst hypothesis has been recorded.")
    lines.extend(["", "## 9. Alternative hypotheses", ""])
    lines.extend(f"- [{item['evidence_reference']}] {item['title']} ({item['status']}, {item['confidence']:.2f})" for item in hypotheses[1:] or [])
    for number, title, relation in [(10, "Supporting evidence", "supports"), (11, "Contradicting evidence", "contradicts"), (12, "Missing evidence", "missing_expected")]:
        lines.extend(["", f"## {number}. {title}", ""])
        lines.extend(f"- [EV-{item['id']}] {item['analyst_note'] or item['id']}" for item in report["evidence"] if item["relation"] == relation)
    lines.extend(["", "## 13. Data-quality limitations", ""])
    lines.extend(f"- {item['description']}" for item in report["data_quality"]["issues"] or [{"description": "No open automated issues."}])
    lines.extend(["", "## 14. Corrective actions", ""])
    lines.extend(f"- {item['action_type']}: {item['outcome']}" for item in report["recovery_actions"] or [{"action_type": "None recorded", "outcome": ""}])
    lines.extend(["", "## 15. Recurrence risk", "", "Requires analyst review against incident history.", "", "## 16. Vendor-support recommendations", "", "Ask the vendor to validate the event sequence and provide records identified as missing.", "", "## 17. Appendix", "", "Structured details are available in `diagnostic_report.json`.", "", "## 18. Audit and provenance", "", "Every timeline event retains a raw-record identifier, source filename, and source line number.", ""])
    return "\n".join(lines)


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (2024, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, files[name])
    return output.getvalue()


def report_quality_checks(session: Session, incident: Incident) -> list[dict]:
    hypotheses = session.scalars(select(RootCauseHypothesis).where(RootCauseHypothesis.incident_id == incident.id)).all()
    evidence = session.scalars(select(EvidenceLink).where(EvidenceLink.incident_id == incident.id)).all()
    metrics = calculate_metrics(session, incident)
    checks = []
    if not incident.description.strip(): checks.append({"code": "missing_executive_summary", "blocking": True})
    if not incident.started_at: checks.append({"code": "missing_incident_boundary", "blocking": True})
    if metrics["segment_count"] == 0: checks.append({"code": "missing_downtime_result", "blocking": True})
    primary_ids = {item.id for item in hypotheses if item.hypothesis_role == "primary"}
    if primary_ids and not any(item.hypothesis_id in primary_ids and item.relation == "supports" for item in evidence):
        checks.append({"code": "primary_hypothesis_without_support", "blocking": True})
    if any(item.relation == "contradicts" and not item.contradiction_resolution for item in evidence):
        checks.append({"code": "contradiction_not_discussed", "blocking": True})
    if any(item.status == "confirmed" and item.approval_status not in {"accepted", "approved"} for item in hypotheses):
        checks.append({"code": "unapproved_confirmed_hypothesis", "blocking": True})
    if re.search(r"\b(definitely|certainly|proves?|guaranteed)\b", f"{incident.title} {incident.description}", re.I):
        checks.append({"code": "unsupported_certainty_language", "blocking": True})
    quality = assess_incident(session, incident)
    if any(item["type"] == "pii_warning" and item["status"] == "open" for item in quality["issues"]):
        checks.append({"code": "unresolved_pii_warning", "blocking": True})
    return checks


def generate_report_bundle(
    session: Session,
    incident: Incident,
    report_root: Path,
    *,
    actor: str,
    included_raw_record_ids: list[str],
    profile: str = "technical",
    redaction_rules: dict | None = None,
) -> dict:
    if profile not in REPORT_PROFILE_CONFIG["profiles"]:
        raise ValueError(f"unknown report profile: {profile}")
    checks = report_quality_checks(session, incident)
    blocking = [item for item in checks if item["blocking"]]
    if blocking:
        raise ValueError("report quality checks failed: " + ", ".join(item["code"] for item in blocking))
    version = int(session.scalar(select(func.max(ReportArtifact.version)).where(ReportArtifact.incident_id == incident.id)) or 0) + 1
    timeline = build_timeline(session, incident, TimelineFilters())
    metrics = calculate_metrics(session, incident)
    hypotheses = session.scalars(select(RootCauseHypothesis).where(RootCauseHypothesis.incident_id == incident.id).order_by(RootCauseHypothesis.confidence.desc())).all()
    evidence = session.scalars(select(EvidenceLink).where(EvidenceLink.incident_id == incident.id)).all()
    recovery = session.scalars(select(RecoveryAction).where(RecoveryAction.incident_id == incident.id)).all()
    sources = session.scalars(select(DataSource).where(DataSource.engagement_id == incident.diagnostic_engagement_id)).all()
    asset_ids = {item.get("asset_id") for item in timeline if item.get("asset_id")}
    assets = session.scalars(select(Asset).where(Asset.id.in_(asset_ids))).all() if asset_ids else []
    quality = assess_incident(session, incident)
    report = _json_safe({
        "schema_version": "diagnostic_report.v1", "version": version,
        "template": {"profile": profile, "version": REPORT_PROFILE_CONFIG["version"], "generator_version": "rfii-report.v1"},
        "status": "draft", "analyst_approval_required": True,
        "incident": {"id": incident.id, "title": incident.title, "description": incident.description, "status": incident.status, "started_at": incident.started_at, "recovered_at": incident.recovered_at, "business_impact": incident.business_impact},
        "sections": REPORT_SECTIONS,
        "assets": [{"id": row.id, "name": row.name, "asset_type": row.asset_type, "external_asset_id": row.external_asset_id} for row in assets],
        "sources": [{"id": row.id, "name": row.name, "source_type": row.source_type, "clock_offset_ms": row.clock_offset_ms} for row in sources],
        "timeline": timeline, "metrics": metrics,
        "hypotheses": [{"id": row.id, "evidence_reference": f"HYP-{row.id}", "title": row.title, "failure_domain": row.failure_domain, "role": row.hypothesis_role, "status": row.status, "confidence": row.confidence, "confidence_derivation": row.confidence_derivation, "approval_status": row.approval_status} for row in hypotheses],
        "evidence": [{"id": row.id, "evidence_reference": f"EV-{row.id}", "hypothesis_id": row.hypothesis_id, "canonical_event_id": row.canonical_event_id, "raw_record_id": row.raw_record_id, "relation": row.relation, "strength": row.strength, "origin_group": row.evidence_origin_group, "analyst_note": row.analyst_note, "weight": row.weight, "review_status": row.review_status, "contradiction_resolution": row.contradiction_resolution} for row in evidence],
        "recovery_actions": [{"id": row.id, "action_type": row.action_type, "performed_at": row.performed_at, "performed_by": row.performed_by, "outcome": row.outcome} for row in recovery],
        "data_quality": quality,
        "quality_checks": checks,
        "evidence_reference_appendix": [{"reference": f"EV-{row.id}", "raw_record_id": row.raw_record_id, "canonical_event_id": row.canonical_event_id} for row in evidence],
        "provenance": {"generated_by": actor, "generated_at": datetime.now(timezone.utc), "raw_records_selected_for_vendor_package": included_raw_record_ids},
    })
    snapshot_sha256 = _digest(json.dumps(report, sort_keys=True).encode())
    redaction_counts = {}
    if redaction_rules:
        report, redaction_counts = redact(report, redaction_rules)
        session.add(RedactionAudit(incident_id=incident.id, report_version=version, actor=actor, rules=redaction_rules, replacement_counts=redaction_counts, preview_only=False))
    timeline_csv = _timeline_csv(timeline)
    report_json = json.dumps(report, indent=2, sort_keys=True).encode()
    report_md = _markdown(report).encode()
    report_html = ("<!doctype html><meta charset='utf-8'><title>Diagnostic report</title><style>body{font:16px system-ui;max-width:1000px;margin:2rem auto;line-height:1.5}h1,h2{color:#183153}</style><body>" + "\n".join(f"<p>{html.escape(line)}</p>" if line and not line.startswith("#") else f"<h{min(line.count('#'),2)}>{html.escape(line.lstrip('# '))}</h{min(line.count('#'),2)}>" for line in report_md.decode().splitlines()) + "</body>").encode()
    report_pdf = structured_report_pdf(report, confidentiality=REPORT_PROFILE_CONFIG["profiles"][profile]["confidentiality"])
    manifest: list[dict] = []
    selected_raw: dict[str, bytes] = {}
    for raw_id in sorted(set(included_raw_record_ids)):
        raw = session.get(RawRecord, raw_id)
        if raw is None:
            continue
        payload = json.dumps(raw.payload, indent=2, sort_keys=True).encode()
        name = f"selected_raw_logs/{raw.id}.json"
        selected_raw[name] = payload
        source = session.get(DataSource, raw.data_source_id)
        manifest.append({"file_name": name, "sha256": _digest(payload), "source": source.name if source else raw.data_source_id, "original_timestamp": raw.source_timestamp_raw, "export_timestamp": report["provenance"]["generated_at"], "included_by": actor, "reason": "Explicit analyst selection"})
    manifest_bytes = json.dumps({"schema_version": "evidence_manifest.v1", "files": manifest}, indent=2, sort_keys=True).encode()
    zip_files = {
        "incident_summary.md": report_md,
        "timeline.csv": timeline_csv,
        "affected_assets.json": json.dumps(report["assets"], indent=2, sort_keys=True).encode(),
        "evidence_manifest.json": manifest_bytes,
        "questions_for_vendor.md": b"# Questions for vendor\n\n1. Does your event history corroborate the supplied sequence?\n2. Can you provide the missing evidence listed in the diagnostic?\n3. Which recovery action is recommended and why?\n",
        "data_quality_notes.md": ("# Data-quality notes\n\n" + "\n".join(f"- {item['description']}" for item in quality["issues"])).encode(),
        **selected_raw,
    }
    package = _zip_bytes(zip_files)
    output_dir = report_root / incident.id / f"v{version:04d}"
    output_dir.mkdir(parents=True, exist_ok=False)
    contents = {"json": report_json, "markdown": report_md, "html": report_html, "pdf": report_pdf, "timeline_csv": timeline_csv, "vendor_zip": package}
    names = {"json": "diagnostic_report.json", "markdown": "diagnostic_report.md", "html": "diagnostic_report.html", "pdf": "diagnostic_report.pdf", "timeline_csv": "timeline.csv", "vendor_zip": "vendor_support_package.zip"}
    artifacts: list[ReportArtifact] = []
    for format_name, content in contents.items():
        path = output_dir / names[format_name]
        path.write_bytes(content)
        artifact = ReportArtifact(incident_id=incident.id, version=version, format=format_name, storage_path=str(path), sha256=_digest(content), template_profile=profile, template_version=REPORT_PROFILE_CONFIG["version"], data_snapshot_sha256=snapshot_sha256, generator_version="rfii-report.v1")
        session.add(artifact); artifacts.append(artifact)
    session.flush(); audit(session, actor=actor, action="report_generation", entity_type="incident", entity_id=incident.id, details={"version": version, "artifact_ids": [item.id for item in artifacts]}); session.commit()
    return {"version": version, "profile": profile, "quality_checks": checks, "redaction_counts": redaction_counts, "artifacts": [{"id": item.id, "format": item.format, "sha256": item.sha256} for item in artifacts], "schema_version": "1.0"}


def approve_report_version(session: Session, incident: Incident, version: int, *, actor: str, note: str) -> list[ReportArtifact]:
    artifacts = session.scalars(select(ReportArtifact).where(ReportArtifact.incident_id == incident.id, ReportArtifact.version == version)).all()
    if not artifacts:
        raise KeyError(version)
    hypotheses = session.scalars(select(RootCauseHypothesis).where(RootCauseHypothesis.incident_id == incident.id)).all()
    evidence = session.scalars(select(EvidenceLink).where(EvidenceLink.incident_id == incident.id)).all()
    if incident.severity in {"medium", "high", "critical"}:
        primary = [item for item in hypotheses if item.hypothesis_role == "primary"]
        alternatives = [item for item in hypotheses if item.hypothesis_role == "alternative"]
        hypothesis_ids = [item.id for item in primary]
        justification = session.scalar(
            select(HypothesisReview).where(
                HypothesisReview.hypothesis_id.in_(hypothesis_ids),
                HypothesisReview.decision == "no_alternative_justified",
                HypothesisReview.note != "",
            )
        ) if hypothesis_ids else None
        if not primary or (not alternatives and not justification):
            raise ValueError("medium/high severity approval requires a primary and alternative hypothesis or reviewer justification")
    unresolved = [item for item in evidence if item.relation == "contradicts" and item.review_status == "unreviewed"]
    if unresolved:
        raise ValueError("all contradicting evidence must be reviewed before report approval")
    checks = report_quality_checks(session, incident)
    if any(item["blocking"] for item in checks):
        raise ValueError("report quality checks failed: " + ", ".join(item["code"] for item in checks if item["blocking"]))
    now = datetime.now(timezone.utc)
    for artifact in artifacts:
        artifact.approved_by = actor
        artifact.approved_at = now
    session.flush()
    for artifact in artifacts:
        artifact.immutable = True
    incident.approved_by = actor
    if incident.status == "review": incident.status = "resolved"
    audit(session, actor=actor, action="report_approval", entity_type="incident", entity_id=incident.id, details={"version": version, "note": note})
    session.commit()
    return artifacts
