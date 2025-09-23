"""Add custom field definitions and attributes columns"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_importer_custom_fields"
down_revision = "0003_enum_to_string"
branch_labels = None
depends_on = None


ENTITY_TABLES = [
    "cpu",
    "gpu",
    "ports_profile",
    "valuation_rule",
    "listing",
]


def upgrade() -> None:
    op.create_table(
        "custom_field_definition",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("data_type", sa.String(length=32), nullable=False, server_default="string"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("default_value", sa.JSON(), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="public"),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("entity", "key", name="uq_custom_field_entity_key"),
    )
    op.create_index("ix_custom_field_definition_entity", "custom_field_definition", ["entity"])

    for table in ENTITY_TABLES:
        op.add_column(
            table,
            sa.Column(
                "attributes_json",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        )

    op.add_column(
        "import_session",
        sa.Column(
            "declared_entities_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("import_session", "declared_entities_json")

    for table in ENTITY_TABLES:
        op.drop_column(table, "attributes_json")

    op.drop_index("ix_custom_field_definition_entity", table_name="custom_field_definition")
    op.drop_table("custom_field_definition")

