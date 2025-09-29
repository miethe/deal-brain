"""Create custom field audit log table and supporting indexes"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_custom_field_audit"
down_revision = "0005_custom_field_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "custom_field_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("field_id", sa.Integer(), sa.ForeignKey("custom_field_definition.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(
        "ix_custom_field_audit_field",
        "custom_field_audit_log",
        ["field_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_custom_field_audit_field", table_name="custom_field_audit_log")
    op.drop_table("custom_field_audit_log")

