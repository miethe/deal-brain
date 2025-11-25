"""Add dual CPU Mark performance metrics to listings

Revision ID: 0012
Revises: 0011
Create Date: 2025-10-05 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    # Add performance metric columns
    op.add_column("listing", sa.Column("dollar_per_cpu_mark_single", sa.Float(), nullable=True))
    op.add_column(
        "listing", sa.Column("dollar_per_cpu_mark_single_adjusted", sa.Float(), nullable=True)
    )
    op.add_column("listing", sa.Column("dollar_per_cpu_mark_multi", sa.Float(), nullable=True))
    op.add_column(
        "listing", sa.Column("dollar_per_cpu_mark_multi_adjusted", sa.Float(), nullable=True)
    )

    # Create indexes for filtering and sorting
    op.create_index("idx_listing_dollar_per_cpu_single", "listing", ["dollar_per_cpu_mark_single"])
    op.create_index("idx_listing_dollar_per_cpu_multi", "listing", ["dollar_per_cpu_mark_multi"])
    op.create_index(
        "idx_listing_dollar_per_cpu_single_adj", "listing", ["dollar_per_cpu_mark_single_adjusted"]
    )
    op.create_index(
        "idx_listing_dollar_per_cpu_multi_adj", "listing", ["dollar_per_cpu_mark_multi_adjusted"]
    )


def downgrade():
    op.drop_index("idx_listing_dollar_per_cpu_multi_adj", table_name="listing")
    op.drop_index("idx_listing_dollar_per_cpu_single_adj", table_name="listing")
    op.drop_index("idx_listing_dollar_per_cpu_multi", table_name="listing")
    op.drop_index("idx_listing_dollar_per_cpu_single", table_name="listing")

    op.drop_column("listing", "dollar_per_cpu_mark_multi_adjusted")
    op.drop_column("listing", "dollar_per_cpu_mark_multi")
    op.drop_column("listing", "dollar_per_cpu_mark_single_adjusted")
    op.drop_column("listing", "dollar_per_cpu_mark_single")
