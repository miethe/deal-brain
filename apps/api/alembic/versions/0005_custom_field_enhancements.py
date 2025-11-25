"""Enhance custom field definitions with validation and ordering"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_custom_field_enhancements"
down_revision = "0004_importer_custom_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "custom_field_definition",
        sa.Column("validation_json", sa.JSON(), nullable=True),
    )
    op.add_column(
        "custom_field_definition",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("100")),
    )
    op.add_column(
        "custom_field_definition",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_custom_field_definition_order",
        "custom_field_definition",
        ["entity", "display_order"],
    )
    op.execute("UPDATE custom_field_definition SET display_order = 100 WHERE display_order IS NULL")
    op.alter_column(
        "custom_field_definition",
        "display_order",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_index("ix_custom_field_definition_order", table_name="custom_field_definition")
    op.drop_column("custom_field_definition", "deleted_at")
    op.drop_column("custom_field_definition", "display_order")
    op.drop_column("custom_field_definition", "validation_json")
