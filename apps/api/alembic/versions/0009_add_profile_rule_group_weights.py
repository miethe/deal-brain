"""add profile rule group weights

Revision ID: 0009
Revises: 0008
Create Date: 2025-10-01 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    # Add rule_group_weights column to profile table
    op.add_column(
        "profile",
        sa.Column("rule_group_weights", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Set default empty dict for existing rows
    op.execute(
        "UPDATE profile SET rule_group_weights = '{}'::jsonb WHERE rule_group_weights IS NULL"
    )

    # Make it non-nullable after setting defaults
    op.alter_column(
        "profile", "rule_group_weights", nullable=False, server_default=sa.text("'{}'::jsonb")
    )


def downgrade():
    op.drop_column("profile", "rule_group_weights")
