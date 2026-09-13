from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class VersionedResponse(BaseModel):
    schema_version: str = "1.0"


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class SiteCreate(BaseModel):
    customer_id: str
    name: str = Field(min_length=1, max_length=200)
    timezone: str = "UTC"


class SystemCreate(BaseModel):
    site_id: str
    name: str
    system_type: str
    external_system_id: str | None = None
    aliases: list[str] = Field(default_factory=list)


class AssetCreate(BaseModel):
    site_id: str
    system_id: str | None = None
    name: str
    asset_type: str
    external_asset_id: str | None = None
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssetDependencyCreate(BaseModel):
    source_asset_id: str
    target_asset_id: str
    dependency_type: Literal[
        "depends_on", "controlled_by", "communicates_with", "supplies", "receives_tasks_from",
        "located_in", "blocks", "triggers", "monitored_by", "maintained_by"
    ]


class EngagementCreate(BaseModel):
    customer_id: str
    site_id: str
    title: str
    description: str = ""
    intake_checklist: dict[str, Any] = Field(default_factory=dict)
    handling_basis: str = "synthetic_or_permitted_export"
    retention_until: datetime | None = None


class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    timezone: str = "UTC"
    clock_offset_ms: int = 0
    expected: bool = True


class AssetMappingDecisionCreate(BaseModel):
    engagement_id: str
    external_identifier: str = Field(min_length=1)
    target_type: Literal["asset", "system", "unresolved"] = "asset"
    asset_id: str | None = None
    system_id: str | None = None
    match_method: Literal["exact", "alias", "configured_rule", "analyst_confirmation", "unresolved"]
    rationale: str = Field(min_length=1)


class MappingProfileCreate(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    profile: dict[str, Any]
    test_fixture: str | None = None
    compatibility_notes: str = ""


class JobCreate(BaseModel):
    job_type: Literal[
        "file_profile", "preview", "preserve", "ingest", "normalize",
        "recalculate_timeline", "generate_report", "build_vendor_package", "retention_cleanup",
    ]
    idempotency_key: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=20)


class IncidentCreate(BaseModel):
    diagnostic_engagement_id: str
    site_id: str
    title: str
    description: str = ""
    started_at: datetime
    recovered_at: datetime | None = None
    business_impact: str | None = None
    severity: Literal["low", "medium", "high", "critical"] = "low"


class IncidentPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Literal["draft", "open", "investigating", "review", "resolved", "closed"] | None = None
    started_at: datetime | None = None
    recovered_at: datetime | None = None
    business_impact: str | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None


class BoundaryUpdate(BaseModel):
    started_at: datetime
    recovered_at: datetime | None = None
    reason: str = Field(min_length=1)


class ClockOffsetUpdate(BaseModel):
    data_source_id: str
    clock_offset_ms: int
    uncertainty_ms: int = Field(default=0, ge=0)
    method: Literal["shared_event", "ntp_log", "manual_action", "matched_request_response", "customer_provided", "analyst_estimate"] = "analyst_estimate"
    evidence_links: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)


class LifecycleMarkerCreate(BaseModel):
    marker_type: Literal[
        "occurred_at", "detected_at", "acknowledged_at", "investigation_started_at",
        "initial_hypothesis_at", "cause_identified_at", "escalated_at", "vendor_contacted_at",
        "technical_recovery_at", "business_recovery_at", "resolved_at", "closed_at",
    ]
    occurred_at: datetime
    source: str = Field(min_length=1)
    derived: bool = False
    evidence_links: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1, ge=0, le=1)
    reason: str = ""


class RecoveryMilestoneCreate(BaseModel):
    milestone_type: Literal["technical_recovery", "partial_recovery", "business_process_recovery", "temporary_workaround", "durable_resolution"]
    occurred_at: datetime
    evidence_links: list[str] = Field(default_factory=list)
    source: str = Field(min_length=1)
    note: str = ""


class EventGroupCreate(BaseModel):
    title: str = Field(min_length=1)
    group_type: Literal["retry_cycle", "door_interaction", "network_interruption", "recovery_sequence", "task_handshake", "other"]
    event_ids: list[str] = Field(min_length=1)
    analyst_note: str = ""


class AnnotationCreate(BaseModel):
    occurred_at: datetime
    title: str
    annotation: str = ""


class DowntimeCreate(BaseModel):
    started_at: datetime
    ended_at: datetime
    segment_type: Literal[
        "complete_stop", "degraded_operation", "blocked_robot", "manual_intervention",
        "waiting_for_vendor", "planned", "excluded"
    ]
    affected_asset_ids: list[str] = Field(default_factory=list)
    business_impact: str = ""
    evidence_links: list[str] = Field(default_factory=list)
    analyst_approved: bool = False


class RecoveryCreate(BaseModel):
    action_type: str
    performed_at: datetime
    performed_by: str
    asset_id: str | None = None
    source: str = "analyst"
    outcome: str = ""
    evidence_links: list[str] = Field(default_factory=list)


class HypothesisCreate(BaseModel):
    title: str
    failure_domain: str
    description: str = ""
    assumptions: list[str] = Field(default_factory=list)
    analyst_owner: str
    hypothesis_role: Literal["primary", "alternative"] = "primary"


class HypothesisStatusPatch(BaseModel):
    status: Literal["proposed", "under_review", "supported", "rejected", "inconclusive", "confirmed"]
    approval_status: str | None = None


class EvidenceCreate(BaseModel):
    canonical_event_id: str | None = None
    raw_record_id: str | None = None
    report_artifact_id: str | None = None
    relation: Literal["supports", "contradicts", "contextual", "missing_expected"]
    analyst_note: str = ""
    weight: float = Field(default=1.0, ge=0, le=5)
    strength: Literal["direct", "strong_indirect", "weak_indirect", "contextual"] = "contextual"
    evidence_origin_group: str = Field(default="independent", min_length=1)
    strength_override_note: str = ""


class EvidenceReviewCreate(BaseModel):
    review_status: Literal["reviewed", "resolved", "ignored_with_explanation"]
    contradiction_resolution: str = Field(min_length=1)


class HypothesisReviewCreate(BaseModel):
    decision: Literal["accept", "change_confidence", "reject", "request_evidence", "request_alternative", "inconclusive", "no_alternative_justified"]
    reviewer_confidence: float | None = Field(default=None, ge=0, le=1)
    note: str = ""


class ReportCreate(BaseModel):
    included_raw_record_ids: list[str] = Field(default_factory=list)
    profile: Literal["executive", "technical", "vendor_support"] = "technical"
    redaction_rules: dict[str, Any] = Field(default_factory=dict)


class RedactionPreviewCreate(BaseModel):
    snapshot: dict[str, Any]
    rules: dict[str, Any] = Field(default_factory=dict)


class DeletionPreviewCreate(BaseModel):
    reason: str = Field(min_length=1)


class DatasetRegistrationCreate(BaseModel):
    dataset_id: str = Field(min_length=1)
    engagement_id: str | None = None
    file_count: int = Field(ge=1)
    source_categories: list[str] = Field(min_length=1)
    hashes: list[str] = Field(min_length=1)
    time_range: dict[str, Any] = Field(default_factory=dict)
    customer_pseudonym: str = Field(min_length=1)
    retention_until: datetime | None = None
    access_list: list[str] = Field(default_factory=list)
    private_workspace_reference: str = Field(min_length=1)


class ImportEffortCreate(BaseModel):
    source_category: str = Field(min_length=1)
    mapping_minutes: int = Field(default=0, ge=0)
    code_change_minutes: int = Field(default=0, ge=0)
    manual_cleanup_minutes: int = Field(default=0, ge=0)
    unknown_fields: list[str] = Field(default_factory=list)
    reusable_percentage: float = Field(default=0, ge=0, le=100)
    blocked_fields: list[str] = Field(default_factory=list)
    analyst_minutes: int = Field(default=0, ge=0)
    developer_minutes: int = Field(default=0, ge=0)
    note: str = ""


class ApprovalCreate(BaseModel):
    note: str = ""


class CorrectiveActionCreate(BaseModel):
    description: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    status: Literal["proposed", "accepted", "in_progress", "completed", "rejected"] = "proposed"


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=12)
    role_name: Literal["admin", "analyst", "reviewer", "operator", "partner", "viewer"] = "viewer"
    customer_id: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=12)


class ValidationRecordCreate(BaseModel):
    record_type: Literal[
        "operator_interview", "integrator_interview", "dataset_request", "dataset_received",
        "diagnostic_performed", "actionable_outcome", "proposal_sent", "proposal_accepted",
        "pilot_started", "security_review", "partner_introduction", "commercial_commitment", "confidence_update"
    ]
    title: str
    evidence_reference: str = Field(min_length=1)
    outcome: str = ""
    confidence_delta: float = Field(default=0, ge=-1, le=1)
    synthetic: bool = False


class ValidationDecisionCreate(BaseModel):
    decision: Literal["go", "pivot", "stop"]
    rationale: str = Field(min_length=1)
    validation_record_ids: list[str] = Field(min_length=1)
