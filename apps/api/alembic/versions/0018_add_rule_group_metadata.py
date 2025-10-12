"""Add metadata_json column to valuation_rule_group

Revision ID: 0018
Revises: 0017
Create Date: 2025-10-12 12:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "valuation_rule_group",
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_index(
        "ix_rule_group_entity_key",
        "valuation_rule_group",
        [sa.text("(metadata_json ->> 'entity_key')")],
        unique=False,
        postgresql_using="btree",
    )

    op.alter_column(
        "valuation_rule_group",
        "metadata_json",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_index("ix_rule_group_entity_key", table_name="valuation_rule_group")
    op.drop_column("valuation_rule_group", "metadata_json")
