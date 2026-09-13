from __future__ import annotations

from collections import Counter
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain_models.models import (
    Asset,
    AssetDependency,
    CanonicalEvent,
    DataSource,
    DowntimeSegment,
    EventGroup,
    Incident,
    IncidentAsset,
    IncidentSuggestion,
    RawRecord,
    RecoveryAction,
    RootCauseHypothesis,
)
from packages.incident_engine import calculate_metrics


def suggest_incident_windows(session: Session, engagement_id: str) -> list[IncidentSuggestion]:
    rows = session.execute(
        select(CanonicalEvent, RawRecord)
        .join(RawRecord, CanonicalEvent.raw_record_id == RawRecord.id)
        .join(DataSource, RawRecord.data_source_id == DataSource.id)
        .where(DataSource.engagement_id == engagement_id, CanonicalEvent.event_time.is_not(None))
        .order_by(CanonicalEvent.event_time)
    ).all()
    candidates: list[IncidentSuggestion] = []
    by_code = Counter(event.event_code for event, _ in rows if event.severity in {"error", "critical"})
    for code, count in by_code.items():
        if count < 3:
            continue
        events = [event for event, _ in rows if event.event_code == code]
        candidate = IncidentSuggestion(
            engagement_id=engagement_id,
            rule_id="repeated_error_code.v1",
            earliest_at=events[0].event_time - timedelta(seconds=30),
            latest_at=events[-1].event_time + timedelta(seconds=30),
            rationale=f"Suggestion only: {code} occurred {count} times; this does not establish cause.",
            supporting_event_ids=[event.id for event in events],
        )
        session.add(candidate); candidates.append(candidate)
    session.commit()
    return candidates


def dependency_impact(session: Session, incident_id: str) -> dict:
    links = session.scalars(select(IncidentAsset).where(IncidentAsset.incident_id == incident_id)).all()
    affected_ids = {link.asset_id for link in links}
    dependencies = session.scalars(
        select(AssetDependency).where(
            AssetDependency.source_asset_id.in_(affected_ids) | AssetDependency.target_asset_id.in_(affected_ids)
        )
    ).all() if affected_ids else []
    assets = {item.id: item for item in session.scalars(select(Asset).where(Asset.id.in_(affected_ids | {d.source_asset_id for d in dependencies} | {d.target_asset_id for d in dependencies}))).all()} if affected_ids else {}
    return {
        "affected_assets": [{"id": assets[item].id, "name": assets[item].name} for item in affected_ids if item in assets],
        "dependencies": [{"source": d.source_asset_id, "target": d.target_asset_id, "type": d.dependency_type} for d in dependencies],
        "possible_failure_domains": sorted({assets[item].asset_type for item in assets}),
        "limitation": "Dependency context is not proof of cause.",
        "method_version": "asset-graph-context.v1",
    }


def _features(session: Session, incident: Incident) -> dict:
    hypotheses = session.scalars(select(RootCauseHypothesis).where(RootCauseHypothesis.incident_id == incident.id)).all()
    segments = session.scalars(select(DowntimeSegment).where(DowntimeSegment.incident_id == incident.id)).all()
    recoveries = session.scalars(select(RecoveryAction).where(RecoveryAction.incident_id == incident.id)).all()
    codes = session.scalars(
        select(CanonicalEvent.event_code).join(RawRecord).join(DataSource).where(
            DataSource.engagement_id == incident.diagnostic_engagement_id,
            CanonicalEvent.event_time >= incident.started_at,
            CanonicalEvent.event_time <= (incident.recovered_at or incident.started_at),
        ).order_by(CanonicalEvent.event_time).limit(20)
    ).all()
    return {
        "event_code_sequence": list(codes),
        "failure_domains": sorted({item.failure_domain for item in hypotheses}),
        "downtime_types": sorted({item.segment_type for item in segments}),
        "recovery_actions": sorted({item.action_type for item in recoveries}),
    }


def recurring_matches(session: Session, incident: Incident) -> list[dict]:
    target = _features(session, incident)
    matches = []
    for candidate in session.scalars(select(Incident).where(Incident.site_id == incident.site_id, Incident.id != incident.id)).all():
        other = _features(session, candidate)
        reasons = []
        if target["event_code_sequence"] and target["event_code_sequence"] == other["event_code_sequence"]:
            reasons.append("same ordered event-code sequence")
        for field in ("failure_domains", "downtime_types", "recovery_actions"):
            overlap = sorted(set(target[field]) & set(other[field]))
            if overlap: reasons.append(f"shared {field}: {', '.join(overlap)}")
        if reasons:
            matches.append({"incident_id": candidate.id, "title": candidate.title, "reasons": reasons, "method_version": "transparent-sequence.v1"})
    return matches


def compare_incidents(session: Session, left: Incident, right: Incident) -> dict:
    return {
        "left": {"id": left.id, "title": left.title, "metrics": calculate_metrics(session, left), "features": _features(session, left)},
        "right": {"id": right.id, "title": right.title, "metrics": calculate_metrics(session, right), "features": _features(session, right)},
        "event_groups": {
            "left": [row.title for row in session.scalars(select(EventGroup).where(EventGroup.incident_id == left.id)).all()],
            "right": [row.title for row in session.scalars(select(EventGroup).where(EventGroup.incident_id == right.id)).all()],
        },
        "method_version": "incident-comparison.v1",
    }
