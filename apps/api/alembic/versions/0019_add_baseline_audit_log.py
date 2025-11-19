"""Add baseline audit log table

Revision ID: 0019
Revises: 0018_add_rule_group_metadata
Create Date: 2025-01-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade():
    # Create baseline_audit_log table
    op.create_table(
        "baseline_audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("actor_name", sa.String(length=128), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("result", sa.String(length=16), nullable=False, server_default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ruleset_id", sa.Integer(), nullable=True),
        sa.Column("source_hash", sa.String(length=64), nullable=True),
        sa.Column("version", sa.String(length=32), nullable=True),
        sa.Column("entity_key", sa.String(length=128), nullable=True),
        sa.Column("field_name", sa.String(length=128), nullable=True),
        sa.Column("affected_listings_count", sa.Integer(), nullable=True),
        sa.Column("total_adjustment_change", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for efficient querying
    op.create_index(
        "ix_baseline_audit_log_operation",
        "baseline_audit_log",
        ["operation"],
        unique=False,
    )
    op.create_index(
        "ix_baseline_audit_log_actor_id",
        "baseline_audit_log",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_baseline_audit_log_timestamp",
        "baseline_audit_log",
        ["timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_baseline_audit_log_ruleset_id",
        "baseline_audit_log",
        ["ruleset_id"],
        unique=False,
    )
    op.create_index(
        "ix_baseline_audit_log_source_hash",
        "baseline_audit_log",
        ["source_hash"],
        unique=False,
    )


def downgrade():
    # Drop indexes
    op.drop_index("ix_baseline_audit_log_source_hash", table_name="baseline_audit_log")
    op.drop_index("ix_baseline_audit_log_ruleset_id", table_name="baseline_audit_log")
    op.drop_index("ix_baseline_audit_log_timestamp", table_name="baseline_audit_log")
    op.drop_index("ix_baseline_audit_log_actor_id", table_name="baseline_audit_log")
    op.drop_index("ix_baseline_audit_log_operation", table_name="baseline_audit_log")

    # Drop table
    op.drop_table("baseline_audit_log")
