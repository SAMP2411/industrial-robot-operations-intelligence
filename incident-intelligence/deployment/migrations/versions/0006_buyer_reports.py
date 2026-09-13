"""Add report template snapshots and redaction audit records."""
from alembic import op
import sqlalchemy as sa


revision = "0006_buyer_reports"
down_revision = "0005_evidence_methodology"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("report_artifacts", sa.Column("template_profile", sa.String(80), nullable=False, server_default="technical"))
    op.add_column("report_artifacts", sa.Column("template_version", sa.String(40), nullable=False, server_default="report.v1"))
    op.add_column("report_artifacts", sa.Column("data_snapshot_sha256", sa.String(64), nullable=True))
    op.add_column("report_artifacts", sa.Column("generator_version", sa.String(40), nullable=False, server_default="rfii-report.v1"))
    op.create_table(
        "redaction_audits",
        sa.Column("incident_id", sa.String(36), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("report_version", sa.Integer(), nullable=True),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("replacement_counts", sa.JSON(), nullable=False),
        sa.Column("preview_only", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_redaction_audits_incident_id", "redaction_audits", ["incident_id"])


def downgrade() -> None:
    op.drop_table("redaction_audits")
    for name in ("generator_version", "data_snapshot_sha256", "template_version", "template_profile"):
        op.drop_column("report_artifacts", name)
