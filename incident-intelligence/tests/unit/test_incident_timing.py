from __future__ import annotations

from datetime import datetime, timedelta, timezone

from packages.domain_models.models import (
    Asset,
    AssetDependency,
    CanonicalEvent,
    Customer,
    DataSource,
    DiagnosticEngagement,
    Incident,
    IncidentAsset,
    IncidentLifecycleMarker,
    RawRecord,
    RecoveryMilestone,
    Site,
)
from packages.incident_analysis import dependency_impact, suggest_incident_windows
from packages.incident_engine import calculate_lifecycle_metrics, calculate_metrics
from packages.timeline_engine import TimelineFilters, build_timeline


NOW = datetime(2026, 7, 19, 8, 0, tzinfo=timezone.utc)


def _incident(db_session):
    customer = Customer(name="Synthetic"); db_session.add(customer); db_session.flush()
    site = Site(customer_id=customer.id, name="Lab", timezone="UTC"); db_session.add(site); db_session.flush()
    engagement = DiagnosticEngagement(customer_id=customer.id, site_id=site.id, title="Timing"); db_session.add(engagement); db_session.flush()
    incident = Incident(diagnostic_engagement_id=engagement.id, site_id=site.id, title="Timing", started_at=NOW, recovered_at=NOW + timedelta(minutes=20), created_by="analyst")
    db_session.add(incident); db_session.flush()
    return customer, site, engagement, incident


def test_all_lifecycle_metrics_include_provenance_and_unavailable_state(db_session):
    _, _, _, incident = _incident(db_session)
    db_session.add_all([
        IncidentLifecycleMarker(incident_id=incident.id, marker_type="occurred_at", occurred_at=NOW, source="robot log", derived=False, evidence_links=["raw-1"], analyst="analyst", confidence=1),
        IncidentLifecycleMarker(incident_id=incident.id, marker_type="detected_at", occurred_at=NOW + timedelta(seconds=94), source="operator note", derived=False, evidence_links=["note-1"], analyst="analyst", confidence=1),
        IncidentLifecycleMarker(incident_id=incident.id, marker_type="technical_recovery_at", occurred_at=NOW + timedelta(minutes=10), source="fleet log", derived=True, evidence_links=["raw-2"], analyst="analyst", confidence=.8),
    ]); db_session.commit()
    metrics = {item["metric"]: item for item in calculate_lifecycle_metrics(db_session, incident)}
    assert metrics["time_to_detection"] == {
        "metric": "time_to_detection", "seconds": 94, "start_marker": "incident.occurred_at",
        "end_marker": "incident.detected_at", "calculation_version": "1.0", "status": "measured",
        "limitations": [], "evidence_links": ["note-1", "raw-1"],
    }
    assert metrics["time_to_recovery"]["status"] == "estimated"
    assert metrics["time_to_closure"]["status"] == "unavailable"
    assert metrics["time_to_closure"]["seconds"] is None


def test_technical_and_business_recovery_are_distinct(db_session):
    _, _, _, incident = _incident(db_session)
    db_session.add_all([
        RecoveryMilestone(incident_id=incident.id, milestone_type="technical_recovery", occurred_at=NOW + timedelta(minutes=10), source="fleet log", analyst="analyst", evidence_links=[]),
        RecoveryMilestone(incident_id=incident.id, milestone_type="business_process_recovery", occurred_at=NOW + timedelta(minutes=27), source="throughput report", analyst="analyst", evidence_links=[]),
    ]); db_session.commit()
    milestones = calculate_metrics(db_session, incident)["recovery_milestones"]
    assert milestones[0]["type"] == "technical_recovery"
    assert milestones[1]["type"] == "business_process_recovery"
    assert milestones[0]["occurred_at"] != milestones[1]["occurred_at"]


def test_overlapping_time_intervals_are_labelled_order_uncertain(db_session):
    _, _, engagement, incident = _incident(db_session)
    source = DataSource(engagement_id=engagement.id, name="Export", source_type="log"); db_session.add(source); db_session.flush()
    for index, second in enumerate((5, 6)):
        raw = RawRecord(ingestion_run_id=f"run-{index}", data_source_id=source.id, payload={"i": index}, payload_sha256=f"{index:064d}")
        db_session.add(raw); db_session.flush()
        event = CanonicalEvent(
            raw_record_id=raw.id, event_type="log", event_code=f"E{index}", event_time=NOW + timedelta(seconds=second),
            event_time_earliest=NOW + timedelta(seconds=second - 2), event_time_latest=NOW + timedelta(seconds=second + 2),
            message="event", severity="error",
        )
        db_session.add(event)
    db_session.commit()
    items = build_timeline(db_session, incident, TimelineFilters())
    assert items[1]["order_uncertain_with_previous"] is True


def test_suggestions_are_noncausal_and_dependency_impact_is_context(db_session):
    _, site, engagement, incident = _incident(db_session)
    source = DataSource(engagement_id=engagement.id, name="Export", source_type="log"); db_session.add(source); db_session.flush()
    for index in range(3):
        raw = RawRecord(ingestion_run_id=f"run-{index}", data_source_id=source.id, payload={"i": index}, payload_sha256=f"{index + 10:064d}")
        db_session.add(raw); db_session.flush()
        db_session.add(CanonicalEvent(raw_record_id=raw.id, event_type="log", event_code="REPEATED_ERROR", event_time=NOW + timedelta(seconds=index), message="error", severity="error"))
    affected = Asset(site_id=site.id, name="Robot", asset_type="amr")
    upstream = Asset(site_id=site.id, name="Fleet manager", asset_type="fleet_manager")
    db_session.add_all([affected, upstream]); db_session.flush()
    db_session.add_all([IncidentAsset(incident_id=incident.id, asset_id=affected.id), AssetDependency(source_asset_id=affected.id, target_asset_id=upstream.id, dependency_type="receives_tasks_from")]); db_session.commit()
    suggestion = suggest_incident_windows(db_session, engagement.id)[0]
    assert "Suggestion only" in suggestion.rationale and "does not establish cause" in suggestion.rationale
    impact = dependency_impact(db_session, incident.id)
    assert impact["dependencies"][0]["type"] == "receives_tasks_from"
    assert impact["limitation"] == "Dependency context is not proof of cause."
