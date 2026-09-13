from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from packages.audit import audit
from packages.domain_models.models import (
    CanonicalEvent, DataSource, DeletionReceipt, DeletionRequest, DiagnosticEngagement,
    Incident, IngestionRun, RawRecord, ReportArtifact,
)


def preview_deletion(session: Session, engagement: DiagnosticEngagement, *, actor: str, reason: str) -> DeletionRequest:
    now = datetime.now(timezone.utc)
    retention_until = engagement.retention_until
    if retention_until and retention_until.tzinfo is None: retention_until = retention_until.replace(tzinfo=timezone.utc)
    if engagement.legal_hold: raise ValueError("engagement is under legal hold")
    if not retention_until or retention_until > now: raise ValueError("engagement retention period has not expired")
    source_ids = session.scalars(select(DataSource.id).where(DataSource.engagement_id == engagement.id)).all()
    run_ids = session.scalars(select(IngestionRun.id).where(IngestionRun.data_source_id.in_(source_ids))).all() if source_ids else []
    incident_ids = session.scalars(select(Incident.id).where(Incident.diagnostic_engagement_id == engagement.id)).all()
    manifest = {
        "sources": len(source_ids), "ingestion_runs": len(run_ids),
        "raw_records": len(session.scalars(select(RawRecord.id).where(RawRecord.ingestion_run_id.in_(run_ids))).all()) if run_ids else 0,
        "incidents": len(incident_ids),
        "report_artifacts": len(session.scalars(select(ReportArtifact.id).where(ReportArtifact.incident_id.in_(incident_ids))).all()) if incident_ids else 0,
    }
    request = DeletionRequest(engagement_id=engagement.id, customer_id=engagement.customer_id, requested_by=actor, dry_run_manifest=manifest, reason=reason)
    session.add(request); session.flush(); audit(session, actor=actor, action="retention_deletion_preview", entity_type="diagnostic_engagement", entity_id=engagement.id, details=manifest); session.commit()
    return request


def approve_deletion(session: Session, request: DeletionRequest, *, actor: str) -> DeletionRequest:
    if request.requested_by == actor: raise ValueError("deletion requires independent approval")
    request.approved_by = actor; request.status = "approved"; session.commit(); return request


def execute_deletion(session: Session, request: DeletionRequest, storage_root: Path, *, actor: str) -> DeletionReceipt:
    if request.status != "approved" or not request.approved_by: raise ValueError("deletion request is not approved")
    engagement = session.get(DiagnosticEngagement, request.engagement_id)
    if not engagement or engagement.legal_hold: raise ValueError("engagement unavailable or under legal hold")
    source_ids = session.scalars(select(DataSource.id).where(DataSource.engagement_id == engagement.id)).all()
    runs = session.scalars(select(IngestionRun).where(IngestionRun.data_source_id.in_(source_ids))).all() if source_ids else []
    run_ids = [row.id for row in runs]
    raw_ids = session.scalars(select(RawRecord.id).where(RawRecord.ingestion_run_id.in_(run_ids))).all() if run_ids else []
    incident_ids = session.scalars(select(Incident.id).where(Incident.diagnostic_engagement_id == engagement.id)).all()
    artifacts = session.scalars(select(ReportArtifact).where(ReportArtifact.incident_id.in_(incident_ids))).all() if incident_ids else []
    paths = sorted({str(Path(row.storage_path).parent) for row in runs} | {str(Path(row.storage_path).parent) for row in artifacts})
    if raw_ids: session.execute(delete(CanonicalEvent).where(CanonicalEvent.raw_record_id.in_(raw_ids))); session.execute(delete(RawRecord).where(RawRecord.id.in_(raw_ids)))
    if run_ids: session.execute(delete(IngestionRun).where(IngestionRun.id.in_(run_ids)))
    if artifacts: session.execute(delete(ReportArtifact).where(ReportArtifact.id.in_([row.id for row in artifacts])))
    for path_text in paths:
        path = Path(path_text)
        if storage_root in path.parents: shutil.rmtree(path, ignore_errors=True)
    engagement.status = "deleted"; request.status = "executed"
    counts = {**request.dry_run_manifest, "canonical_events": len(raw_ids)}
    receipt = DeletionReceipt(engagement_id=engagement.id, customer_id=engagement.customer_id, deletion_request_id=request.id, executed_by=actor, deleted_counts=counts, storage_paths_removed=paths, reason=request.reason)
    session.add(receipt); session.flush(); audit(session, actor=actor, action="retention_deletion_execute", entity_type="diagnostic_engagement", entity_id=engagement.id, details={"receipt_id": receipt.id, "counts": counts}); session.commit()
    return receipt
