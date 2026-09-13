"""Add engagement intake fields and audited mapping decisions."""
from alembic import op
import sqlalchemy as sa


revision = "0002_console_workflow"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("diagnostic_engagements", sa.Column("intake_checklist", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("diagnostic_engagements", sa.Column("handling_basis", sa.String(length=120), nullable=False, server_default="synthetic_or_permitted_export"))
    op.add_column("diagnostic_engagements", sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("diagnostic_engagements", sa.Column("legal_hold", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "asset_mapping_decisions",
        sa.Column("engagement_id", sa.String(length=36), sa.ForeignKey("diagnostic_engagements.id"), nullable=False),
        sa.Column("external_identifier", sa.String(length=240), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("asset_id", sa.String(length=36), sa.ForeignKey("assets.id"), nullable=True),
        sa.Column("system_id", sa.String(length=36), sa.ForeignKey("systems.id"), nullable=True),
        sa.Column("match_method", sa.String(length=60), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_asset_mapping_decisions_engagement_id", "asset_mapping_decisions", ["engagement_id"])
    op.create_index("ix_asset_mapping_decisions_external_identifier", "asset_mapping_decisions", ["external_identifier"])


def downgrade() -> None:
    op.drop_table("asset_mapping_decisions")
    op.drop_column("diagnostic_engagements", "legal_hold")
    op.drop_column("diagnostic_engagements", "retention_until")
    op.drop_column("diagnostic_engagements", "handling_basis")
    op.drop_column("diagnostic_engagements", "intake_checklist")
