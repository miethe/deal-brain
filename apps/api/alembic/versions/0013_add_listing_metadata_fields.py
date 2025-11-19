"""Add product metadata fields to listings

Revision ID: 0013
Revises: 0012
Create Date: 2025-10-05 00:01:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    # Add product identification columns
    op.add_column("listing", sa.Column("manufacturer", sa.String(64), nullable=True))
    op.add_column("listing", sa.Column("series", sa.String(128), nullable=True))
    op.add_column("listing", sa.Column("model_number", sa.String(128), nullable=True))
    op.add_column("listing", sa.Column("form_factor", sa.String(32), nullable=True))

    # Create indexes for filtering
    op.create_index("idx_listing_manufacturer", "listing", ["manufacturer"])
    op.create_index("idx_listing_form_factor", "listing", ["form_factor"])


def downgrade():
    op.drop_index("idx_listing_form_factor", table_name="listing")
    op.drop_index("idx_listing_manufacturer", table_name="listing")

    op.drop_column("listing", "form_factor")
    op.drop_column("listing", "model_number")
    op.drop_column("listing", "series")
    op.drop_column("listing", "manufacturer")
