from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import yaml

from packages.domain_models.models import CanonicalEvent, DataQualityIssue, DataSource, EvidenceLink, Incident, RawRecord, RootCauseHypothesis


ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def expected_source_templates() -> dict:
    return yaml.safe_load((ROOT / "config/expected_source_templates.yaml").read_text())


def assess_incident(session: Session, incident: Incident) -> dict:
    sources = session.scalars(select(DataSource).where(DataSource.engagement_id == incident.diagnostic_engagement_id)).all()
    events = session.scalars(
        select(CanonicalEvent).join(RawRecord).join(DataSource).where(DataSource.engagement_id == incident.diagnostic_engagement_id)
    ).all()
    existing = session.scalars(select(DataQualityIssue).where(DataQualityIssue.incident_id == incident.id)).all()
    hypotheses = session.scalars(select(RootCauseHypothesis).where(RootCauseHypothesis.incident_id == incident.id)).all()
    evidence = session.scalars(select(EvidenceLink).where(EvidenceLink.incident_id == incident.id)).all()
    detected: list[tuple[str, str, str, str | None]] = []
    for source in sources:
        source_event_count = session.scalar(select(CanonicalEvent).join(RawRecord).where(RawRecord.data_source_id == source.id).count()) if False else sum(1 for event in events if session.get(RawRecord, event.raw_record_id).data_source_id == source.id)
        if source.expected and source_event_count == 0:
            detected.append(("missing_expected_source", "critical", f"Expected source {source.name} contains no events", source.id))
        if source.clock_offset_ms:
            detected.append(("clock_drift", "warning", f"Source {source.name} uses analyst offset {source.clock_offset_ms} ms", source.id))
    if any(event.event_time is None for event in events):
        detected.append(("unparseable_timestamp", "warning", "One or more events have no normalized timestamp", None))
    codes = Counter((event.event_time, event.event_code, event.asset_id, event.message) for event in events)
    if any(count > 1 for count in codes.values()):
        detected.append(("duplicate_event", "warning", "Canonical event duplicates are present", None))
    source_text = " ".join(f"{source.name} {source.source_type}" for source in sources).casefold()
    templates = expected_source_templates()["templates"]
    for domain in sorted({item.failure_domain for item in hypotheses}):
        template = templates.get(domain)
        if template and not any(keyword.casefold() in source_text for keyword in template["source_keywords"]):
            detected.append(("missing_expected_source", "critical", f"Suggested evidence for {domain} is unavailable: {', '.join(template['suggested'])}", None))
    existing_keys = {(row.issue_type, row.description) for row in existing}
    for issue_type, severity, description, source_id in detected:
        if (issue_type, description) not in existing_keys:
            session.add(DataQualityIssue(engagement_id=incident.diagnostic_engagement_id, incident_id=incident.id, issue_type=issue_type, severity=severity, description=description, source_id=source_id))
    session.commit()
    issues = session.scalars(select(DataQualityIssue).where(DataQualityIssue.incident_id == incident.id)).all()
    open_issues = [issue for issue in issues if issue.resolution_status == "open"]
    dimension_penalties = {
        "source_completeness": sum(25 for issue in open_issues if issue.issue_type in {"missing_expected_source", "incomplete_export"}),
        "time_reliability": sum(20 for issue in open_issues if issue.issue_type in {"clock_drift", "unparseable_timestamp"}),
        "asset_identity_reliability": sum(20 for issue in open_issues if issue.issue_type == "ambiguous_asset_mapping"),
        "normalization_coverage": sum(15 for issue in open_issues if issue.issue_type in {"unknown_event_code", "normalization_error"}),
        "critical_interval_coverage": 20 if not events else 0,
        "record_integrity": sum(10 for issue in open_issues if issue.issue_type in {"duplicate_event", "hash_mismatch"}),
        "evidence_independence": max(0, len(evidence) - len({item.id if item.evidence_origin_group == "independent" else item.evidence_origin_group for item in evidence})) * 10,
        "contradiction_status": sum(20 for item in evidence if item.relation == "contradicts" and item.review_status == "unreviewed"),
    }
    dimensions = []
    for name, penalty in dimension_penalties.items():
        value = max(0, 100 - penalty)
        dimensions.append({"dimension": name, "score": value, "category": "good" if value >= 80 else "limited" if value >= 50 else "poor", "derivation": {"penalty": penalty, "rubric_version": "data-quality.v1"}, "limitations": [] if penalty == 0 else ["Open issues reduce this dimension"]})
    score = round(sum(item["score"] for item in dimensions) / len(dimensions))
    return {
        "score": score,
        "grade": "good" if score >= 80 else "limited" if score >= 50 else "poor",
        "source_coverage": {"registered": len(sources), "with_events": len({session.get(RawRecord, event.raw_record_id).data_source_id for event in events})},
        "issue_counts": dict(Counter(issue.issue_type for issue in issues)),
        "issues": [{"id": issue.id, "type": issue.issue_type, "severity": issue.severity, "description": issue.description, "status": issue.resolution_status} for issue in issues],
        "confidence_limitations": [issue.description for issue in issues if issue.severity in {"error", "critical"}],
        "rubric_version": "data-quality.v1",
        "dimensions": dimensions,
        "expected_source_template_version": expected_source_templates()["version"],
        "schema_version": "1.0",
    }
