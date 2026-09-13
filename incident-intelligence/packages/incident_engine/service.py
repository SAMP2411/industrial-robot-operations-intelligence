from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.audit import audit
from packages.domain_models.models import DowntimeSegment, Incident, IncidentLifecycleMarker, RecoveryAction, RecoveryMilestone


LIFECYCLE_METRICS = {
    "time_to_detection": "detected_at",
    "time_to_acknowledgement": "acknowledged_at",
    "time_to_investigation": "investigation_started_at",
    "time_to_initial_hypothesis": "initial_hypothesis_at",
    "time_to_cause_identification": "cause_identified_at",
    "time_to_escalation": "escalated_at",
    "time_to_vendor_contact": "vendor_contacted_at",
    "time_to_recovery": "technical_recovery_at",
    "time_to_resolution": "resolved_at",
    "time_to_closure": "closed_at",
}


def calculate_lifecycle_metrics(session: Session, incident: Incident) -> list[dict]:
    markers = {
        item.marker_type: item
        for item in session.scalars(select(IncidentLifecycleMarker).where(IncidentLifecycleMarker.incident_id == incident.id)).all()
    }
    start = markers.get("occurred_at")
    results = []
    for metric, marker_name in LIFECYCLE_METRICS.items():
        end = markers.get(marker_name)
        limitations = []
        seconds = None
        status = "unavailable"
        if not start:
            limitations.append("occurred_at marker is unavailable")
        if not end:
            limitations.append(f"{marker_name} marker is unavailable")
        if start and end:
            seconds = max(0, int((end.occurred_at - start.occurred_at).total_seconds()))
            status = "estimated" if start.derived or end.derived or min(start.confidence, end.confidence) < 1 else "measured"
        results.append({
            "metric": metric,
            "seconds": seconds,
            "start_marker": "incident.occurred_at",
            "end_marker": f"incident.{marker_name}",
            "calculation_version": "1.0",
            "status": status,
            "limitations": limitations,
            "evidence_links": sorted(set((start.evidence_links if start else []) + (end.evidence_links if end else []))),
        })
    return results


def calculate_metrics(session: Session, incident: Incident) -> dict:
    segments = session.scalars(select(DowntimeSegment).where(DowntimeSegment.incident_id == incident.id)).all()
    included = [row for row in segments if row.segment_type not in {"planned", "excluded"}]
    complete = sum(row.duration_seconds for row in included if row.segment_type in {"complete_stop", "blocked_robot", "manual_intervention", "waiting_for_vendor"})
    degraded = sum(row.duration_seconds for row in included if row.segment_type == "degraded_operation")
    gross = max(0, int(((incident.recovered_at or incident.started_at) - incident.started_at).total_seconds()))
    metrics = {
        "gross_incident_duration_seconds": gross,
        "unplanned_downtime_seconds": complete,
        "degraded_operation_seconds": degraded,
        "excluded_planned_seconds": sum(row.duration_seconds for row in segments if row.segment_type in {"planned", "excluded"}),
        "segment_count": len(segments),
        "derivation": {"method": "sum_of_analyst_defined_segments", "segment_ids": [row.id for row in segments], "schema_version": "1.0"},
        "lifecycle": calculate_lifecycle_metrics(session, incident),
        "recovery_milestones": [
            {"type": row.milestone_type, "occurred_at": row.occurred_at, "evidence_links": row.evidence_links, "source": row.source}
            for row in session.scalars(select(RecoveryMilestone).where(RecoveryMilestone.incident_id == incident.id).order_by(RecoveryMilestone.occurred_at)).all()
        ],
    }
    incident.downtime_seconds = complete
    session.commit()
    return metrics


def create_downtime_segment(session: Session, incident: Incident, values: dict, *, actor: str) -> DowntimeSegment:
    if values["ended_at"] < values["started_at"]:
        raise ValueError("downtime end must not precede start")
    duration = int((values["ended_at"] - values["started_at"]).total_seconds())
    entity = DowntimeSegment(**values, incident_id=incident.id, duration_seconds=duration, derivation={"method": "ended_at_minus_started_at", "actor": actor})
    session.add(entity); session.flush(); audit(session, actor=actor, action="downtime_segment_change", entity_type="downtime_segment", entity_id=entity.id); session.commit()
    calculate_metrics(session, incident)
    return entity


def create_recovery_action(session: Session, incident: Incident, values: dict, *, actor: str) -> RecoveryAction:
    entity = RecoveryAction(**values, incident_id=incident.id)
    session.add(entity); session.flush(); audit(session, actor=actor, action="recovery_action_create", entity_type="recovery_action", entity_id=entity.id); session.commit()
    return entity
