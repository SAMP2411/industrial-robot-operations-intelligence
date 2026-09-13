from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, event, inspect
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


SCHEMA_VERSION = "1.0"


def new_id() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EntityMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    schema_version: Mapped[str] = mapped_column(String(16), default=SCHEMA_VERSION)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Customer(EntityMixin, Base):
    __tablename__ = "customers"
    name: Mapped[str] = mapped_column(String(200))


class Site(EntityMixin, Base):
    __tablename__ = "sites"
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")


class Area(EntityMixin, Base):
    __tablename__ = "areas"
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))


class System(EntityMixin, Base):
    __tablename__ = "systems"
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    system_type: Mapped[str] = mapped_column(String(80))
    external_system_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)


class Asset(EntityMixin, Base):
    __tablename__ = "assets"
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    system_id: Mapped[str | None] = mapped_column(ForeignKey("systems.id"), nullable=True)
    area_id: Mapped[str | None] = mapped_column(ForeignKey("areas.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    asset_type: Mapped[str] = mapped_column(String(80))
    external_asset_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class AssetDependency(EntityMixin, Base):
    __tablename__ = "asset_dependencies"
    source_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    target_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    dependency_type: Mapped[str] = mapped_column(String(80))


class DiagnosticEngagement(EntityMixin, Base):
    __tablename__ = "diagnostic_engagements"
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(40), default="draft")
    description: Mapped[str] = mapped_column(Text, default="")
    intake_checklist: Mapped[dict] = mapped_column(JSON, default=dict)
    handling_basis: Mapped[str] = mapped_column(String(120), default="synthetic_or_permitted_export")
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False)


class DataSource(EntityMixin, Base):
    __tablename__ = "data_sources"
    engagement_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_engagements.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(80))
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    clock_offset_ms: Mapped[int] = mapped_column(Integer, default=0)
    expected: Mapped[bool] = mapped_column(Boolean, default=True)


class Connector(EntityMixin, Base):
    __tablename__ = "connectors"
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(40))
    source_type: Mapped[str] = mapped_column(String(80))
    maturity: Mapped[str] = mapped_column(String(40), default="experimental")
    read_only: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class IngestionRun(EntityMixin, Base):
    __tablename__ = "ingestion_runs"
    data_source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    source_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    file_sha256: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(40), default="previewed")
    mapping_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    mapping_profile_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    mapping_profile_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    detected_encoding: Mapped[str | None] = mapped_column(String(40), nullable=True)
    selected_encoding: Mapped[str | None] = mapped_column(String(40), nullable=True)
    encoding_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    replacement_character_count: Mapped[int] = mapped_column(Integer, default=0)
    decoding_warnings: Mapped[list] = mapped_column(JSON, default=list)
    encrypted_at_rest: Mapped[bool] = mapped_column(Boolean, default=False)
    encryption_key_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)


class MappingProfileVersion(EntityMixin, Base):
    __tablename__ = "mapping_profile_versions"
    __table_args__ = (UniqueConstraint("name", "version"),)
    name: Mapped[str] = mapped_column(String(160), index=True)
    version: Mapped[str] = mapped_column(String(40))
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    author: Mapped[str] = mapped_column(String(120))
    profile: Mapped[dict] = mapped_column(JSON)
    test_fixture: Mapped[str | None] = mapped_column(Text, nullable=True)
    compatibility_notes: Mapped[str] = mapped_column(Text, default="")


class Job(EntityMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("job_type", "idempotency_key"),)
    job_type: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    error_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)


class JobAttempt(EntityMixin, Base):
    __tablename__ = "job_attempts"
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40))
    worker_id: Mapped[str] = mapped_column(String(160))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)


class JobEvent(EntityMixin, Base):
    __tablename__ = "job_events"
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class RawRecord(EntityMixin, Base):
    __tablename__ = "raw_records"
    __table_args__ = (UniqueConstraint("ingestion_run_id", "payload_sha256"),)
    ingestion_run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.id"), index=True)
    data_source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), index=True)
    source_record_id: Mapped[str | None] = mapped_column(String(240), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_timestamp_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    payload_sha256: Mapped[str] = mapped_column(String(64), index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CanonicalEvent(EntityMixin, Base):
    __tablename__ = "canonical_events"
    raw_record_id: Mapped[str] = mapped_column(ForeignKey("raw_records.id"), unique=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    event_code: Mapped[str] = mapped_column(String(120), index=True)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    event_time_earliest: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_time_latest: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_time_original: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_quality: Mapped[str] = mapped_column(String(40), default="unknown")
    clock_offset_ms: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[str] = mapped_column(String(40), default="unknown")
    system_id: Mapped[str | None] = mapped_column(ForeignKey("systems.id"), nullable=True, index=True)
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    state_from: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state_to: Mapped[str | None] = mapped_column(String(120), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    normalizer_version: Mapped[str] = mapped_column(String(40), default="generic.v1")


class Incident(EntityMixin, Base):
    __tablename__ = "incidents"
    diagnostic_engagement_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_engagements.id"), index=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="open")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    downtime_seconds: Mapped[int] = mapped_column(Integer, default=0)
    business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(120))
    approved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(40), default="low")


class IncidentLifecycleMarker(EntityMixin, Base):
    __tablename__ = "incident_lifecycle_markers"
    __table_args__ = (UniqueConstraint("incident_id", "marker_type"),)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    marker_type: Mapped[str] = mapped_column(String(80), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(200))
    derived: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_links: Mapped[list] = mapped_column(JSON, default=list)
    analyst: Mapped[str] = mapped_column(String(120))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    reason: Mapped[str] = mapped_column(Text, default="")


class RecoveryMilestone(EntityMixin, Base):
    __tablename__ = "recovery_milestones"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    milestone_type: Mapped[str] = mapped_column(String(80), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evidence_links: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(200))
    analyst: Mapped[str] = mapped_column(String(120))
    note: Mapped[str] = mapped_column(Text, default="")


class IncidentAsset(EntityMixin, Base):
    __tablename__ = "incident_assets"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    role: Mapped[str] = mapped_column(String(60), default="affected")


class TimelineEntry(EntityMixin, Base):
    __tablename__ = "timeline_entries"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    canonical_event_id: Mapped[str | None] = mapped_column(ForeignKey("canonical_events.id"), nullable=True)
    entry_type: Mapped[str] = mapped_column(String(60), default="event")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    title: Mapped[str] = mapped_column(String(240))
    annotation: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(120), default="system")


class ClockAlignment(EntityMixin, Base):
    __tablename__ = "clock_alignments"
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), index=True)
    offset_ms: Mapped[int] = mapped_column(Integer)
    uncertainty_ms: Mapped[int] = mapped_column(Integer, default=0)
    method: Mapped[str] = mapped_column(String(100))
    evidence_links: Mapped[list] = mapped_column(JSON, default=list)
    analyst: Mapped[str] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(40), default="1.0")
    reason: Mapped[str] = mapped_column(Text, default="")


class EventGroup(EntityMixin, Base):
    __tablename__ = "event_groups"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    group_type: Mapped[str] = mapped_column(String(80))
    event_ids: Mapped[list] = mapped_column(JSON, default=list)
    analyst_note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(120))


class IncidentSuggestion(EntityMixin, Base):
    __tablename__ = "incident_suggestions"
    engagement_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_engagements.id"), index=True)
    rule_id: Mapped[str] = mapped_column(String(120))
    earliest_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latest_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rationale: Mapped[str] = mapped_column(Text)
    supporting_event_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(40), default="suggested")
    dismissed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)


class DowntimeSegment(EntityMixin, Base):
    __tablename__ = "downtime_segments"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    segment_type: Mapped[str] = mapped_column(String(60))
    affected_asset_ids: Mapped[list] = mapped_column(JSON, default=list)
    business_impact: Mapped[str] = mapped_column(Text, default="")
    evidence_links: Mapped[list] = mapped_column(JSON, default=list)
    analyst_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    derivation: Mapped[dict] = mapped_column(JSON, default=dict)


class RecoveryAction(EntityMixin, Base):
    __tablename__ = "recovery_actions"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(80))
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    performed_by: Mapped[str] = mapped_column(String(120))
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(200), default="analyst")
    outcome: Mapped[str] = mapped_column(Text, default="")
    evidence_links: Mapped[list] = mapped_column(JSON, default=list)


class RootCauseHypothesis(EntityMixin, Base):
    __tablename__ = "root_cause_hypotheses"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    failure_domain: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="proposed")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    assumptions: Mapped[list] = mapped_column(JSON, default=list)
    analyst_owner: Mapped[str] = mapped_column(String(120))
    approval_status: Mapped[str] = mapped_column(String(40), default="unreviewed")
    confidence_derivation: Mapped[dict] = mapped_column(JSON, default=dict)
    hypothesis_role: Mapped[str] = mapped_column(String(40), default="primary")
    confidence_policy_version: Mapped[str] = mapped_column(String(40), default="confidence.v1")


class EvidenceLink(EntityMixin, Base):
    __tablename__ = "evidence_links"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    hypothesis_id: Mapped[str | None] = mapped_column(ForeignKey("root_cause_hypotheses.id"), nullable=True)
    canonical_event_id: Mapped[str | None] = mapped_column(ForeignKey("canonical_events.id"), nullable=True)
    raw_record_id: Mapped[str | None] = mapped_column(ForeignKey("raw_records.id"), nullable=True)
    report_artifact_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    relation: Mapped[str] = mapped_column(String(40))
    analyst_note: Mapped[str] = mapped_column(Text, default="")
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    strength: Mapped[str] = mapped_column(String(40), default="contextual")
    evidence_origin_group: Mapped[str] = mapped_column(String(160), default="independent")
    strength_override_note: Mapped[str] = mapped_column(Text, default="")
    review_status: Mapped[str] = mapped_column(String(40), default="unreviewed")
    contradiction_resolution: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(120))


class HypothesisReview(EntityMixin, Base):
    __tablename__ = "hypothesis_reviews"
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("root_cause_hypotheses.id"), index=True)
    reviewer: Mapped[str] = mapped_column(String(120))
    decision: Mapped[str] = mapped_column(String(60))
    analyst_confidence: Mapped[float] = mapped_column(Float)
    reviewer_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    disagreement: Mapped[bool] = mapped_column(Boolean, default=False)


class DataQualityIssue(EntityMixin, Base):
    __tablename__ = "data_quality_issues"
    engagement_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_engagements.id"), index=True)
    incident_id: Mapped[str | None] = mapped_column(ForeignKey("incidents.id"), nullable=True, index=True)
    issue_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(40), default="warning")
    description: Mapped[str] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("data_sources.id"), nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(40), default="open")


class AssetMappingDecision(EntityMixin, Base):
    __tablename__ = "asset_mapping_decisions"
    engagement_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_engagements.id"), index=True)
    external_identifier: Mapped[str] = mapped_column(String(240), index=True)
    target_type: Mapped[str] = mapped_column(String(40), default="asset")
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    system_id: Mapped[str | None] = mapped_column(ForeignKey("systems.id"), nullable=True)
    match_method: Mapped[str] = mapped_column(String(60))
    rationale: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(120))


class Finding(EntityMixin, Base):
    __tablename__ = "findings"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(40), default="unknown")
    status: Mapped[str] = mapped_column(String(40), default="open")


class CorrectiveAction(EntityMixin, Base):
    __tablename__ = "corrective_actions"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    description: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="proposed")


class MaintenanceWorkOrder(EntityMixin, Base):
    __tablename__ = "maintenance_work_orders"
    incident_id: Mapped[str | None] = mapped_column(ForeignKey("incidents.id"), nullable=True)
    external_id: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(60))
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Vendor(EntityMixin, Base):
    __tablename__ = "vendors"
    name: Mapped[str] = mapped_column(String(200))
    contact: Mapped[dict] = mapped_column(JSON, default=dict)


class SupportCase(EntityMixin, Base):
    __tablename__ = "support_cases"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    vendor_id: Mapped[str | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(60), default="draft")


class RecurringFailurePattern(EntityMixin, Base):
    __tablename__ = "recurring_failure_patterns"
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    incident_ids: Mapped[list] = mapped_column(JSON, default=list)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    rationale: Mapped[str] = mapped_column(Text, default="")
    method_version: Mapped[str] = mapped_column(String(40), default="transparent-sequence.v1")


class AnalysisRun(EntityMixin, Base):
    __tablename__ = "analysis_runs"
    engagement_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_engagements.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="queued")
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)


class ReportArtifact(EntityMixin, Base):
    __tablename__ = "report_artifacts"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    format: Mapped[str] = mapped_column(String(40))
    storage_path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    approved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    immutable: Mapped[bool] = mapped_column(Boolean, default=False)
    template_profile: Mapped[str] = mapped_column(String(80), default="technical")
    template_version: Mapped[str] = mapped_column(String(40), default="report.v1")
    data_snapshot_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generator_version: Mapped[str] = mapped_column(String(40), default="rfii-report.v1")


class RedactionAudit(EntityMixin, Base):
    __tablename__ = "redaction_audits"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    report_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor: Mapped[str] = mapped_column(String(120))
    rules: Mapped[dict] = mapped_column(JSON)
    replacement_counts: Mapped[dict] = mapped_column(JSON)
    preview_only: Mapped[bool] = mapped_column(Boolean, default=True)


class DeletionRequest(EntityMixin, Base):
    __tablename__ = "deletion_requests"
    engagement_id: Mapped[str] = mapped_column(String(36), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    requested_by: Mapped[str] = mapped_column(String(120))
    approved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="preview")
    dry_run_manifest: Mapped[dict] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(Text)


class DeletionReceipt(EntityMixin, Base):
    __tablename__ = "deletion_receipts"
    engagement_id: Mapped[str] = mapped_column(String(36), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    deletion_request_id: Mapped[str] = mapped_column(String(36), index=True)
    executed_by: Mapped[str] = mapped_column(String(120))
    deleted_counts: Mapped[dict] = mapped_column(JSON)
    storage_paths_removed: Mapped[list] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(Text)


class DatasetRegistration(EntityMixin, Base):
    __tablename__ = "dataset_registrations"
    dataset_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    engagement_id: Mapped[str | None] = mapped_column(ForeignKey("diagnostic_engagements.id"), nullable=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    file_count: Mapped[int] = mapped_column(Integer)
    source_categories: Mapped[list] = mapped_column(JSON)
    hashes: Mapped[list] = mapped_column(JSON)
    time_range: Mapped[dict] = mapped_column(JSON, default=dict)
    customer_pseudonym: Mapped[str] = mapped_column(String(160))
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_list: Mapped[list] = mapped_column(JSON, default=list)
    private_workspace_reference: Mapped[str] = mapped_column(Text)
    registered_by: Mapped[str] = mapped_column(String(120))


class ImportEffortRecord(EntityMixin, Base):
    __tablename__ = "import_effort_records"
    dataset_registration_id: Mapped[str] = mapped_column(ForeignKey("dataset_registrations.id"), index=True)
    source_category: Mapped[str] = mapped_column(String(120))
    mapping_minutes: Mapped[int] = mapped_column(Integer, default=0)
    code_change_minutes: Mapped[int] = mapped_column(Integer, default=0)
    manual_cleanup_minutes: Mapped[int] = mapped_column(Integer, default=0)
    unknown_fields: Mapped[list] = mapped_column(JSON, default=list)
    reusable_percentage: Mapped[float] = mapped_column(Float, default=0)
    blocked_fields: Mapped[list] = mapped_column(JSON, default=list)
    analyst_minutes: Mapped[int] = mapped_column(Integer, default=0)
    developer_minutes: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")


class AuditEvent(EntityMixin, Base):
    __tablename__ = "audit_events"
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)


class User(EntityMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    role_name: Mapped[str] = mapped_column(String(60), default="viewer")
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    reset_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Role(EntityMixin, Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(60), unique=True)
    permissions: Mapped[list] = mapped_column(JSON, default=list)


class ValidationRecord(EntityMixin, Base):
    __tablename__ = "validation_records"
    record_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(240))
    evidence_reference: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(Text, default="")
    confidence_delta: Mapped[float] = mapped_column(Float, default=0.0)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ValidationDecision(EntityMixin, Base):
    __tablename__ = "validation_decisions"
    decision: Mapped[str] = mapped_column(String(20))
    rationale: Mapped[str] = mapped_column(Text)
    validation_record_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[str] = mapped_column(String(120))


@event.listens_for(RawRecord, "before_update")
def _raw_record_update_forbidden(*_args) -> None:
    raise ValueError("Raw records are immutable")


@event.listens_for(RawRecord, "before_delete")
def _raw_record_delete_forbidden(*_args) -> None:
    raise ValueError("Raw records are immutable")


@event.listens_for(AuditEvent, "before_update")
@event.listens_for(AuditEvent, "before_delete")
def _audit_event_mutation_forbidden(*_args) -> None:
    raise ValueError("Audit events are append-only")


@event.listens_for(ReportArtifact, "before_update")
def _approved_report_mutation_forbidden(_mapper, _connection, target: ReportArtifact) -> None:
    history = inspect(target).attrs.immutable.history
    was_immutable = bool(history.deleted and history.deleted[0]) or (not history.has_changes() and target.immutable)
    if was_immutable:
        raise ValueError("Approved report artifacts are immutable")
