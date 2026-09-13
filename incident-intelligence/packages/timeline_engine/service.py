from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.audit import audit
from packages.domain_models.models import CanonicalEvent, ClockAlignment, DataSource, Incident, RawRecord, RecoveryAction, TimelineEntry


@dataclass(frozen=True)
class TimelineFilters:
    source_id: str | None = None
    system_id: str | None = None
    asset_id: str | None = None
    severity: str | None = None
    event_type: str | None = None


def build_timeline(session: Session, incident: Incident, filters: TimelineFilters) -> list[dict]:
    query = (
        select(CanonicalEvent, RawRecord, DataSource)
        .join(RawRecord, CanonicalEvent.raw_record_id == RawRecord.id)
        .join(DataSource, RawRecord.data_source_id == DataSource.id)
        .where(DataSource.engagement_id == incident.diagnostic_engagement_id)
        .where(CanonicalEvent.event_time.is_not(None))
        .where(CanonicalEvent.event_time >= incident.started_at)
    )
    if incident.recovered_at:
        query = query.where(CanonicalEvent.event_time <= incident.recovered_at)
    if filters.source_id: query = query.where(DataSource.id == filters.source_id)
    if filters.system_id: query = query.where(CanonicalEvent.system_id == filters.system_id)
    if filters.asset_id: query = query.where(CanonicalEvent.asset_id == filters.asset_id)
    if filters.severity: query = query.where(CanonicalEvent.severity == filters.severity)
    if filters.event_type: query = query.where(CanonicalEvent.event_type == filters.event_type)
    items: list[dict] = []
    seen: set[tuple] = set()
    for event, raw, source in session.execute(query.order_by(CanonicalEvent.event_time, CanonicalEvent.id)).all():
        duplicate_key = (event.event_time, event.event_code, event.asset_id, event.message)
        if duplicate_key in seen:
            continue
        seen.add(duplicate_key)
        items.append({
            "id": event.id,
            "entry_type": "event",
            "occurred_at": event.event_time,
            "earliest_at": event.event_time_earliest or event.event_time,
            "latest_at": event.event_time_latest or event.event_time,
            "source": {"id": source.id, "name": source.name, "type": source.source_type},
            "system_id": event.system_id,
            "asset_id": event.asset_id,
            "severity": event.severity,
            "event_type": event.event_type,
            "event_code": event.event_code,
            "message": event.message,
            "time_quality": event.time_quality,
            "clock_offset_ms": event.clock_offset_ms,
            "raw_evidence": {"raw_record_id": raw.id, "source_filename": raw.source_filename, "source_line_number": raw.source_line_number},
            "schema_version": event.schema_version,
        })
    for entry in session.scalars(select(TimelineEntry).where(TimelineEntry.incident_id == incident.id)).all():
        items.append({"id": entry.id, "entry_type": entry.entry_type, "occurred_at": entry.occurred_at, "title": entry.title, "annotation": entry.annotation, "created_by": entry.created_by, "schema_version": entry.schema_version})
    for action in session.scalars(select(RecoveryAction).where(RecoveryAction.incident_id == incident.id)).all():
        items.append({"id": action.id, "entry_type": "recovery", "occurred_at": action.performed_at, "title": action.action_type, "annotation": action.outcome, "asset_id": action.asset_id, "created_by": action.performed_by, "evidence_links": action.evidence_links, "schema_version": action.schema_version})
    def comparable(value):
        return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value).timestamp()

    ordered = sorted(items, key=lambda item: (comparable(item.get("earliest_at", item["occurred_at"])), item["id"]))
    for index, item in enumerate(ordered):
        item["order_uncertain_with_previous"] = False
        if index:
            previous = ordered[index - 1]
            previous_latest = previous.get("latest_at", previous["occurred_at"])
            current_earliest = item.get("earliest_at", item["occurred_at"])
            if comparable(previous_latest) >= comparable(current_earliest):
                item["order_uncertain_with_previous"] = True
    return ordered


def add_annotation(session: Session, incident_id: str, *, occurred_at, title: str, annotation: str, actor: str) -> TimelineEntry:
    entry = TimelineEntry(incident_id=incident_id, entry_type="annotation", occurred_at=occurred_at, title=title, annotation=annotation, created_by=actor)
    session.add(entry); session.flush()
    audit(session, actor=actor, action="timeline_annotation", entity_type="timeline_entry", entity_id=entry.id)
    session.commit()
    return entry


def update_clock_offset(
    session: Session,
    source_id: str,
    offset_ms: int,
    *,
    reason: str,
    actor: str,
    uncertainty_ms: int = 0,
    method: str = "analyst_estimate",
    evidence_links: list[str] | None = None,
) -> int:
    source = session.get(DataSource, source_id)
    if source is None:
        raise KeyError(source_id)
    delta = offset_ms - source.clock_offset_ms
    event_ids = select(CanonicalEvent.id).join(RawRecord).where(RawRecord.data_source_id == source_id)
    events = session.scalars(select(CanonicalEvent).where(CanonicalEvent.id.in_(event_ids))).all()
    for item in events:
        if item.event_time:
            item.event_time += timedelta(milliseconds=delta)
        item.clock_offset_ms = offset_ms
        if item.time_quality == "exact" and offset_ms:
            item.time_quality = "converted"
    source.clock_offset_ms = offset_ms
    session.add(ClockAlignment(
        source_id=source.id,
        offset_ms=offset_ms,
        uncertainty_ms=uncertainty_ms,
        method=method,
        evidence_links=evidence_links or [],
        analyst=actor,
        reason=reason,
        version="1.0",
    ))
    audit(session, actor=actor, action="clock_offset_change", entity_type="data_source", entity_id=source.id, details={"old_offset_ms": offset_ms - delta, "new_offset_ms": offset_ms, "reason": reason, "events_updated": len(events)})
    session.commit()
    return len(events)
