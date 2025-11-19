"""add application settings table

Revision ID: 0010
Revises: 0009
Create Date: 2025-10-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    # Create application_settings table
    op.create_table(
        "application_settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    # Seed default valuation thresholds
    op.execute(
        """
        INSERT INTO application_settings (key, value_json, description)
        VALUES (
            'valuation_thresholds',
            '{"good_deal": 15.0, "great_deal": 25.0, "premium_warning": 10.0}'::json,
            'Thresholds for valuation color coding and visual indicators'
        )
    """
    )


def downgrade():
    op.drop_table("application_settings")
