"""Add explainable incident timing, alignment, grouping, and pattern entities."""
from alembic import op
import sqlalchemy as sa


revision = "0004_incident_timing"
down_revision = "0003_ingestion_hardening"
branch_labels = None
depends_on = None


def entity_columns():
    return (
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.add_column("canonical_events", sa.Column("event_time_earliest", sa.DateTime(timezone=True), nullable=True))
    op.add_column("canonical_events", sa.Column("event_time_latest", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "incident_lifecycle_markers",
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("marker_type", sa.String(80), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("derived", sa.Boolean(), nullable=False),
        sa.Column("evidence_links", sa.JSON(), nullable=False),
        sa.Column("analyst", sa.String(120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        *entity_columns(), sa.UniqueConstraint("incident_id", "marker_type"),
    )
    op.create_index("ix_incident_lifecycle_markers_incident_id", "incident_lifecycle_markers", ["incident_id"])
    op.create_index("ix_incident_lifecycle_markers_marker_type", "incident_lifecycle_markers", ["marker_type"])
    op.create_table(
        "recovery_milestones",
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("milestone_type", sa.String(80), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_links", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("analyst", sa.String(120), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        *entity_columns(),
    )
    op.create_index("ix_recovery_milestones_incident_id", "recovery_milestones", ["incident_id"])
    op.create_index("ix_recovery_milestones_milestone_type", "recovery_milestones", ["milestone_type"])
    op.create_table(
        "clock_alignments",
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("offset_ms", sa.Integer(), nullable=False),
        sa.Column("uncertainty_ms", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(100), nullable=False),
        sa.Column("evidence_links", sa.JSON(), nullable=False),
        sa.Column("analyst", sa.String(120), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        *entity_columns(),
    )
    op.create_index("ix_clock_alignments_source_id", "clock_alignments", ["source_id"])
    op.create_table(
        "event_groups",
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("group_type", sa.String(80), nullable=False),
        sa.Column("event_ids", sa.JSON(), nullable=False),
        sa.Column("analyst_note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(120), nullable=False),
        *entity_columns(),
    )
    op.create_index("ix_event_groups_incident_id", "event_groups", ["incident_id"])
    op.create_table(
        "incident_suggestions",
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("diagnostic_engagements.id"), nullable=False),
        sa.Column("rule_id", sa.String(120), nullable=False),
        sa.Column("earliest_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latest_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("supporting_event_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("dismissed_by", sa.String(120), nullable=True),
        *entity_columns(),
    )
    op.create_index("ix_incident_suggestions_engagement_id", "incident_suggestions", ["engagement_id"])
    op.add_column("recurring_failure_patterns", sa.Column("features", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("recurring_failure_patterns", sa.Column("rationale", sa.Text(), nullable=False, server_default=""))
    op.add_column("recurring_failure_patterns", sa.Column("method_version", sa.String(40), nullable=False, server_default="transparent-sequence.v1"))


def downgrade() -> None:
    for table in ("incident_suggestions", "event_groups", "clock_alignments", "recovery_milestones", "incident_lifecycle_markers"):
        op.drop_table(table)
    for column in ("method_version", "rationale", "features"):
        op.drop_column("recurring_failure_patterns", column)
    op.drop_column("canonical_events", "event_time_latest")
    op.drop_column("canonical_events", "event_time_earliest")
