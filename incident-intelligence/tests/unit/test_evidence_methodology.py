from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from packages.data_quality import assess_incident
from packages.domain_models.models import (
    Customer, DataSource, DiagnosticEngagement, EvidenceLink, HypothesisReview,
    DowntimeSegment, Incident, ReportArtifact, RootCauseHypothesis, Site,
)
from packages.hypothesis_engine import recalculate_confidence
from packages.report_generation import approve_report_version


def _case(db_session, severity="low"):
    customer = Customer(name="Synthetic"); db_session.add(customer); db_session.flush()
    site = Site(customer_id=customer.id, name="Lab", timezone="UTC"); db_session.add(site); db_session.flush()
    engagement = DiagnosticEngagement(customer_id=customer.id, site_id=site.id, title="Evidence"); db_session.add(engagement); db_session.flush()
    started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    incident = Incident(diagnostic_engagement_id=engagement.id, site_id=site.id, title="Evidence", description="Synthetic evidence-method approval case.", started_at=started_at, created_by="analyst", severity=severity)
    db_session.add(incident); db_session.flush()
    db_session.add(DowntimeSegment(incident_id=incident.id, started_at=started_at, ended_at=started_at + timedelta(seconds=30), duration_seconds=30, segment_type="complete_stop", analyst_approved=True))
    hypothesis = RootCauseHypothesis(incident_id=incident.id, title="Primary", failure_domain="PLC/control", analyst_owner="analyst", hypothesis_role="primary")
    db_session.add(hypothesis); db_session.flush()
    return engagement, incident, hypothesis


def test_duplicate_origin_support_is_capped_and_policy_is_versioned(db_session):
    _, incident, hypothesis = _case(db_session)
    db_session.add_all([
        EvidenceLink(incident_id=incident.id, hypothesis_id=hypothesis.id, relation="supports", analyst_note="alert", weight=1, strength="direct", evidence_origin_group="controller-event-7", created_by="analyst"),
        EvidenceLink(incident_id=incident.id, hypothesis_id=hypothesis.id, relation="supports", analyst_note="dashboard copy", weight=1, strength="direct", evidence_origin_group="controller-event-7", created_by="analyst"),
    ]); db_session.commit()
    score = recalculate_confidence(db_session, hypothesis)
    assert score == .52  # base .30 + one capped direct-origin contribution .22
    assert hypothesis.confidence_policy_version == "confidence.v1"
    assert hypothesis.confidence_derivation["effective_contributions_by_relation"]["supports"] == 1


def test_unreviewed_contradiction_caps_confidence(db_session):
    _, incident, hypothesis = _case(db_session)
    db_session.add_all([
        EvidenceLink(incident_id=incident.id, hypothesis_id=hypothesis.id, relation="supports", analyst_note="direct", weight=5, strength="direct", evidence_origin_group="one", created_by="analyst"),
        EvidenceLink(incident_id=incident.id, hypothesis_id=hypothesis.id, relation="contradicts", analyst_note="counterexample", weight=.1, strength="contextual", evidence_origin_group="two", created_by="analyst"),
    ]); db_session.commit()
    assert recalculate_confidence(db_session, hypothesis) <= .55
    assert any(item["reason"] == "unreviewed contradiction" for item in hypothesis.confidence_derivation["caps"])


def test_report_approval_requires_alternative_and_resolved_contradictions(db_session, tmp_path):
    _, incident, primary = _case(db_session, severity="high")
    artifact = ReportArtifact(incident_id=incident.id, version=1, format="json", storage_path=str(tmp_path / "report.json"), sha256="0" * 64)
    support = EvidenceLink(incident_id=incident.id, hypothesis_id=primary.id, relation="supports", analyst_note="synthetic support", strength="strong_indirect", evidence_origin_group="support", created_by="analyst")
    db_session.add_all([artifact, support]); db_session.commit()
    with pytest.raises(ValueError, match="alternative hypothesis"):
        approve_report_version(db_session, incident, 1, actor="reviewer", note="review")
    alternative = RootCauseHypothesis(incident_id=incident.id, title="Alternative", failure_domain="network/Wi-Fi", analyst_owner="analyst", hypothesis_role="alternative")
    db_session.add(alternative)
    contradiction = EvidenceLink(incident_id=incident.id, hypothesis_id=primary.id, relation="contradicts", analyst_note="counterexample", strength="direct", evidence_origin_group="counter", created_by="analyst")
    db_session.add(contradiction); db_session.commit()
    with pytest.raises(ValueError, match="contradicting evidence"):
        approve_report_version(db_session, incident, 1, actor="reviewer", note="review")
    contradiction.review_status = "reviewed"; contradiction.contradiction_resolution = "Included in report"; db_session.commit()
    assert approve_report_version(db_session, incident, 1, actor="reviewer", note="review")[0].immutable


def test_expected_sources_and_quality_dimensions_are_explainable(db_session):
    engagement, incident, _ = _case(db_session)
    db_session.add(DataSource(engagement_id=engagement.id, name="Generic telemetry", source_type="generic_log", expected=True))
    db_session.commit()
    result = assess_incident(db_session, incident)
    assert result["rubric_version"] == "data-quality.v1"
    assert {item["dimension"] for item in result["dimensions"]} == {
        "source_completeness", "time_reliability", "asset_identity_reliability", "normalization_coverage",
        "critical_interval_coverage", "record_integrity", "evidence_independence", "contradiction_status",
    }
    assert any(issue["type"] == "missing_expected_source" for issue in result["issues"])
