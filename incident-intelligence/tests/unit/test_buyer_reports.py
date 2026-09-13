from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from packages.domain_models.models import (
    Customer, DiagnosticEngagement, DowntimeSegment, EvidenceLink, Incident,
    ReportArtifact, RootCauseHypothesis, Site,
)
from packages.report_generation import generate_report_bundle
from packages.report_generation.redaction import redact


def _reportable_case(db_session):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    customer = Customer(name="Synthetic"); db_session.add(customer); db_session.flush()
    site = Site(customer_id=customer.id, name="Lab", timezone="UTC"); db_session.add(site); db_session.flush()
    engagement = DiagnosticEngagement(customer_id=customer.id, site_id=site.id, title="Report"); db_session.add(engagement); db_session.flush()
    incident = Incident(diagnostic_engagement_id=engagement.id, site_id=site.id, title="Door interruption", description="A prepared synthetic interruption for report verification.", started_at=start, recovered_at=start + timedelta(minutes=2), business_impact="Contact ops@example.com; station 10.1.2.3 paused.", created_by="analyst")
    db_session.add(incident); db_session.flush()
    db_session.add(DowntimeSegment(incident_id=incident.id, started_at=start, ended_at=start + timedelta(seconds=30), duration_seconds=30, segment_type="complete_stop", analyst_approved=True))
    hypothesis = RootCauseHypothesis(incident_id=incident.id, title="Door interlock delayed", failure_domain="PLC/control", analyst_owner="analyst", hypothesis_role="primary")
    db_session.add(hypothesis); db_session.flush()
    db_session.add(EvidenceLink(incident_id=incident.id, hypothesis_id=hypothesis.id, relation="supports", analyst_note="Door state overlapped stop", strength="strong_indirect", evidence_origin_group="door-log", created_by="analyst"))
    db_session.commit()
    return incident


def test_redaction_masks_network_identifiers_and_selected_fields():
    snapshot = {"email": "ops@example.com", "ip": "10.1.2.3", "mac": "AA:BB:CC:DD:EE:FF", "customer": {"secret": "token-123"}}
    result, counts = redact(snapshot, {"emails": True, "ipv4": True, "mac": True, "customer_secrets": ["token-123"], "selected_fields": ["customer.secret"]})
    assert "example.com" not in json.dumps(result)
    assert "10.1.2.3" not in json.dumps(result)
    assert counts["emails"] == counts["ipv4"] == counts["mac"] == 1


@pytest.mark.parametrize("profile", ["executive", "technical", "vendor_support"])
def test_each_profile_generates_cited_structured_pdf(db_session, tmp_path, profile):
    incident = _reportable_case(db_session)
    result = generate_report_bundle(db_session, incident, tmp_path / "reports", actor="analyst", included_raw_record_ids=[], profile=profile, redaction_rules={"emails": True, "ipv4": True})
    assert result["profile"] == profile
    artifacts = {item["format"]: item for item in result["artifacts"]}
    pdf_path = Path(db_session.get(ReportArtifact, artifacts["pdf"]["id"]).storage_path)
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")
    json_path = Path(db_session.get(ReportArtifact, artifacts["json"]["id"]).storage_path)
    report = json.loads(json_path.read_text())
    assert report["template"]["profile"] == profile
    assert report["hypotheses"][0]["evidence_reference"].startswith("HYP-")
    assert report["evidence_reference_appendix"][0]["reference"].startswith("EV-")
    assert "ops@example.com" not in json_path.read_text()


def test_quality_checks_block_unsupported_certainty(db_session, tmp_path):
    incident = _reportable_case(db_session); incident.description = "This definitely proves the cause."; db_session.commit()
    with pytest.raises(ValueError, match="unsupported_certainty_language"):
        generate_report_bundle(db_session, incident, tmp_path / "reports", actor="analyst", included_raw_record_ids=[])
