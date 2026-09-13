"""Create the complete version 1 incident-intelligence schema."""
from alembic import op

from packages.domain_models.database import Base
from packages.domain_models import models  # noqa: F401


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())
    # Base metadata evolves with the application. Strip post-v1 additions here so a
    # clean install follows the same incremental revisions as an existing v1 database.
    for table in (
        "import_effort_records", "dataset_registrations", "deletion_receipts", "deletion_requests", "redaction_audits", "hypothesis_reviews",
        "incident_suggestions", "event_groups", "clock_alignments", "recovery_milestones",
        "incident_lifecycle_markers", "job_events", "job_attempts", "jobs",
        "mapping_profile_versions", "asset_mapping_decisions",
    ):
        op.drop_table(table)
    future_columns = {
        "diagnostic_engagements": ["intake_checklist", "handling_basis", "retention_until", "legal_hold"],
        "ingestion_runs": [
            "mapping_profile_name", "mapping_profile_version", "detected_encoding", "selected_encoding",
            "encoding_confidence", "replacement_character_count", "decoding_warnings",
            "encrypted_at_rest", "encryption_key_id",
        ],
        "canonical_events": ["event_time_earliest", "event_time_latest"],
        "recurring_failure_patterns": ["features", "rationale", "method_version"],
        "incidents": ["severity"],
        "root_cause_hypotheses": ["hypothesis_role", "confidence_policy_version"],
        "evidence_links": ["strength", "evidence_origin_group", "strength_override_note", "review_status", "contradiction_resolution"],
        "report_artifacts": ["template_profile", "template_version", "data_snapshot_sha256", "generator_version"],
    }
    op.drop_index("ix_audit_events_customer_id", table_name="audit_events")
    for table, columns in future_columns.items():
        for column in columns:
            op.drop_column(table, column)
    with op.batch_alter_table("audit_events") as batch:
        batch.drop_column("customer_id")


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
