"""Add activation flag to valuation rule groups

Revision ID: 0016
Revises: 0015
Create Date: 2025-10-09 09:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "valuation_rule_group",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_valuation_rule_group_is_active",
        "valuation_rule_group",
        ["is_active"],
    )

    op.execute("UPDATE valuation_rule_group SET is_active = TRUE WHERE is_active IS NULL")
    op.alter_column("valuation_rule_group", "is_active", server_default=None)


def downgrade():
    op.drop_index("ix_valuation_rule_group_is_active", table_name="valuation_rule_group")
    op.drop_column("valuation_rule_group", "is_active")

