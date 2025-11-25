"""Add locking flag to custom field definitions"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_custom_field_locking"
down_revision = "0006_custom_field_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "custom_field_definition",
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("custom_field_definition", "is_locked", server_default=None)

    op.create_table(
        "custom_field_attribute_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "field_id",
            sa.Integer(),
            sa.ForeignKey("custom_field_definition.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=False),
        sa.Column("attribute_key", sa.String(length=64), nullable=False),
        sa.Column("previous_value", sa.JSON(), nullable=True),
        sa.Column("reason", sa.String(length=64), nullable=False, server_default="archived"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_custom_field_attribute_history_field",
        "custom_field_attribute_history",
        ["field_id", "created_at"],
    )
    op.create_index(
        "ix_custom_field_attribute_history_entity_record",
        "custom_field_attribute_history",
        ["entity", "record_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_custom_field_attribute_history_entity_record",
        table_name="custom_field_attribute_history",
    )
    op.drop_index(
        "ix_custom_field_attribute_history_field", table_name="custom_field_attribute_history"
    )
    op.drop_table("custom_field_attribute_history")
    op.drop_column("custom_field_definition", "is_locked")
