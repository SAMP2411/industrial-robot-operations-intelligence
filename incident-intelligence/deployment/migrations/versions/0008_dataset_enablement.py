"""Add non-sensitive dataset fingerprints and import-effort tracking."""
from alembic import op
import sqlalchemy as sa


revision = "0008_dataset_enablement"
down_revision = "0007_security_operations"
branch_labels = None
depends_on = None


def entity_columns():
    return (
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "dataset_registrations",
        sa.Column("dataset_id", sa.String(120), nullable=False, unique=True),
        sa.Column("engagement_id", sa.String(36), sa.ForeignKey("diagnostic_engagements.id"), nullable=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("file_count", sa.Integer(), nullable=False), sa.Column("source_categories", sa.JSON(), nullable=False),
        sa.Column("hashes", sa.JSON(), nullable=False), sa.Column("time_range", sa.JSON(), nullable=False),
        sa.Column("customer_pseudonym", sa.String(160), nullable=False), sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_list", sa.JSON(), nullable=False), sa.Column("private_workspace_reference", sa.Text(), nullable=False),
        sa.Column("registered_by", sa.String(120), nullable=False), *entity_columns(),
    )
    op.create_index("ix_dataset_registrations_dataset_id", "dataset_registrations", ["dataset_id"], unique=True)
    op.create_index("ix_dataset_registrations_engagement_id", "dataset_registrations", ["engagement_id"])
    op.create_index("ix_dataset_registrations_customer_id", "dataset_registrations", ["customer_id"])
    op.create_table(
        "import_effort_records",
        sa.Column("dataset_registration_id", sa.String(36), sa.ForeignKey("dataset_registrations.id"), nullable=False),
        sa.Column("source_category", sa.String(120), nullable=False), sa.Column("mapping_minutes", sa.Integer(), nullable=False),
        sa.Column("code_change_minutes", sa.Integer(), nullable=False), sa.Column("manual_cleanup_minutes", sa.Integer(), nullable=False),
        sa.Column("unknown_fields", sa.JSON(), nullable=False), sa.Column("reusable_percentage", sa.Float(), nullable=False),
        sa.Column("blocked_fields", sa.JSON(), nullable=False), sa.Column("analyst_minutes", sa.Integer(), nullable=False),
        sa.Column("developer_minutes", sa.Integer(), nullable=False), sa.Column("note", sa.Text(), nullable=False), *entity_columns(),
    )
    op.create_index("ix_import_effort_records_dataset_registration_id", "import_effort_records", ["dataset_registration_id"])


def downgrade() -> None:
    op.drop_table("import_effort_records"); op.drop_table("dataset_registrations")
