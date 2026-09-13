"""Add tenant-aware jobs/audits, encrypted evidence metadata, and deletion receipts."""
from alembic import op
import sqlalchemy as sa


revision = "0007_security_operations"
down_revision = "0006_buyer_reports"
branch_labels = None
depends_on = None


def entity_columns():
    return (
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.add_column("ingestion_runs", sa.Column("encrypted_at_rest", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("ingestion_runs", sa.Column("encryption_key_id", sa.String(120), nullable=True))
    with op.batch_alter_table("jobs") as batch:
        batch.add_column(sa.Column("customer_id", sa.String(36), nullable=True))
        batch.create_foreign_key("fk_jobs_customer_id", "customers", ["customer_id"], ["id"])
        batch.create_index("ix_jobs_customer_id", ["customer_id"])
    with op.batch_alter_table("audit_events") as batch:
        batch.add_column(sa.Column("customer_id", sa.String(36), nullable=True))
        batch.create_foreign_key("fk_audit_events_customer_id", "customers", ["customer_id"], ["id"])
        batch.create_index("ix_audit_events_customer_id", ["customer_id"])
    op.create_table(
        "deletion_requests",
        sa.Column("engagement_id", sa.String(36), nullable=False), sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("requested_by", sa.String(120), nullable=False), sa.Column("approved_by", sa.String(120), nullable=True),
        sa.Column("status", sa.String(40), nullable=False), sa.Column("dry_run_manifest", sa.JSON(), nullable=False), sa.Column("reason", sa.Text(), nullable=False),
        *entity_columns(),
    )
    op.create_index("ix_deletion_requests_engagement_id", "deletion_requests", ["engagement_id"])
    op.create_index("ix_deletion_requests_customer_id", "deletion_requests", ["customer_id"])
    op.create_table(
        "deletion_receipts",
        sa.Column("engagement_id", sa.String(36), nullable=False), sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("deletion_request_id", sa.String(36), nullable=False), sa.Column("executed_by", sa.String(120), nullable=False),
        sa.Column("deleted_counts", sa.JSON(), nullable=False), sa.Column("storage_paths_removed", sa.JSON(), nullable=False), sa.Column("reason", sa.Text(), nullable=False),
        *entity_columns(),
    )
    op.create_index("ix_deletion_receipts_engagement_id", "deletion_receipts", ["engagement_id"])
    op.create_index("ix_deletion_receipts_customer_id", "deletion_receipts", ["customer_id"])
    op.create_index("ix_deletion_receipts_deletion_request_id", "deletion_receipts", ["deletion_request_id"])


def downgrade() -> None:
    op.drop_table("deletion_receipts"); op.drop_table("deletion_requests")
    with op.batch_alter_table("audit_events") as batch:
        batch.drop_index("ix_audit_events_customer_id"); batch.drop_constraint("fk_audit_events_customer_id", type_="foreignkey"); batch.drop_column("customer_id")
    with op.batch_alter_table("jobs") as batch:
        batch.drop_index("ix_jobs_customer_id"); batch.drop_constraint("fk_jobs_customer_id", type_="foreignkey"); batch.drop_column("customer_id")
    op.drop_column("ingestion_runs", "encryption_key_id"); op.drop_column("ingestion_runs", "encrypted_at_rest")
