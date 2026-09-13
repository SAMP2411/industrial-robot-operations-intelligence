"""Add evidence strength, independence, policy, and reviewer agreement."""
from alembic import op
import sqlalchemy as sa


revision = "0005_evidence_methodology"
down_revision = "0004_incident_timing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("severity", sa.String(40), nullable=False, server_default="low"))
    op.add_column("root_cause_hypotheses", sa.Column("hypothesis_role", sa.String(40), nullable=False, server_default="primary"))
    op.add_column("root_cause_hypotheses", sa.Column("confidence_policy_version", sa.String(40), nullable=False, server_default="confidence.v1"))
    for name, default in (
        ("strength", "contextual"), ("evidence_origin_group", "independent"),
        ("strength_override_note", ""), ("review_status", "unreviewed"),
        ("contradiction_resolution", ""),
    ):
        op.add_column("evidence_links", sa.Column(name, sa.Text() if name.endswith(("note", "resolution")) else sa.String(160), nullable=False, server_default=default))
    op.create_table(
        "hypothesis_reviews",
        sa.Column("hypothesis_id", sa.String(36), sa.ForeignKey("root_cause_hypotheses.id"), nullable=False),
        sa.Column("reviewer", sa.String(120), nullable=False),
        sa.Column("decision", sa.String(60), nullable=False),
        sa.Column("analyst_confidence", sa.Float(), nullable=False),
        sa.Column("reviewer_confidence", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("disagreement", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_hypothesis_reviews_hypothesis_id", "hypothesis_reviews", ["hypothesis_id"])


def downgrade() -> None:
    op.drop_table("hypothesis_reviews")
    for name in ("contradiction_resolution", "review_status", "strength_override_note", "evidence_origin_group", "strength"):
        op.drop_column("evidence_links", name)
    op.drop_column("root_cause_hypotheses", "confidence_policy_version")
    op.drop_column("root_cause_hypotheses", "hypothesis_role")
    op.drop_column("incidents", "severity")
