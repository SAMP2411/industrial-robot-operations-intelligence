"""Add durable jobs, versioned mapping profiles, and decoding provenance."""
from alembic import op
import sqlalchemy as sa


revision = "0003_ingestion_hardening"
down_revision = "0002_console_workflow"
branch_labels = None
depends_on = None


def _entity_columns():
    return (
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    for name, type_ in (
        ("mapping_profile_name", sa.String(160)),
        ("mapping_profile_version", sa.String(40)),
        ("detected_encoding", sa.String(40)),
        ("selected_encoding", sa.String(40)),
    ):
        op.add_column("ingestion_runs", sa.Column(name, type_, nullable=True))
    op.add_column("ingestion_runs", sa.Column("encoding_confidence", sa.Float(), nullable=True))
    op.add_column("ingestion_runs", sa.Column("replacement_character_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ingestion_runs", sa.Column("decoding_warnings", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))

    op.create_table(
        "mapping_profile_versions",
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("author", sa.String(120), nullable=False),
        sa.Column("profile", sa.JSON(), nullable=False),
        sa.Column("test_fixture", sa.Text(), nullable=True),
        sa.Column("compatibility_notes", sa.Text(), nullable=False),
        *_entity_columns(),
        sa.UniqueConstraint("name", "version"),
    )
    op.create_index("ix_mapping_profile_versions_name", "mapping_profile_versions", ["name"])
    op.create_index("ix_mapping_profile_versions_source_type", "mapping_profile_versions", ["source_type"])

    op.create_table(
        "jobs",
        sa.Column("job_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_summary", sa.String(500), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        *_entity_columns(),
        sa.UniqueConstraint("job_type", "idempotency_key"),
    )
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_available_at", "jobs", ["available_at"])
    op.create_table(
        "job_attempts",
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("worker_id", sa.String(160), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        *_entity_columns(),
    )
    op.create_index("ix_job_attempts_job_id", "job_attempts", ["job_id"])
    op.create_table(
        "job_events",
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        *_entity_columns(),
    )
    op.create_index("ix_job_events_job_id", "job_events", ["job_id"])


def downgrade() -> None:
    op.drop_table("job_events")
    op.drop_table("job_attempts")
    op.drop_table("jobs")
    op.drop_table("mapping_profile_versions")
    for name in (
        "decoding_warnings", "replacement_character_count", "encoding_confidence",
        "selected_encoding", "detected_encoding", "mapping_profile_version", "mapping_profile_name",
    ):
        op.drop_column("ingestion_runs", name)
