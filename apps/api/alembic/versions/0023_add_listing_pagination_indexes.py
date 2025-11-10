"""Add indexes for listing pagination performance

Revision ID: 0023
Revises: 0022
Create Date: 2025-10-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0023'
down_revision: Union[str, Sequence[str], None] = '0022'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for cursor-based pagination on sortable columns.

    These indexes support keyset pagination with composite key (sort_column, id)
    for optimal performance (<100ms for 500-row pages).

    Indexes are created for commonly sorted columns:
    - updated_at (default sort)
    - created_at
    - price_usd
    - adjusted_price_usd
    - manufacturer
    - form_factor
    - dollar_per_cpu_mark_multi
    - dollar_per_cpu_mark_single

    Each index includes the id column for stable pagination and to support
    the keyset WHERE clause efficiently.
    """
    # Index for updated_at DESC (default sort)
    op.create_index(
        'ix_listing_updated_at_id_desc',
        'listing',
        [sa.text('updated_at DESC'), sa.text('id DESC')],
        postgresql_where=None,
    )

    # Index for created_at DESC
    op.create_index(
        'ix_listing_created_at_id_desc',
        'listing',
        [sa.text('created_at DESC'), sa.text('id DESC')],
        postgresql_where=None,
    )

    # Index for price_usd ASC/DESC
    op.create_index(
        'ix_listing_price_usd_id',
        'listing',
        ['price_usd', 'id'],
    )

    # Index for adjusted_price_usd ASC/DESC
    op.create_index(
        'ix_listing_adjusted_price_usd_id',
        'listing',
        ['adjusted_price_usd', 'id'],
    )

    # Index for manufacturer (for filtering and sorting)
    op.create_index(
        'ix_listing_manufacturer_id',
        'listing',
        ['manufacturer', 'id'],
    )

    # Index for form_factor (for filtering and sorting)
    op.create_index(
        'ix_listing_form_factor_id',
        'listing',
        ['form_factor', 'id'],
    )

    # Index for dollar_per_cpu_mark_multi (performance metric)
    op.create_index(
        'ix_listing_dollar_per_cpu_mark_multi_id',
        'listing',
        ['dollar_per_cpu_mark_multi', 'id'],
    )

    # Index for dollar_per_cpu_mark_single (performance metric)
    op.create_index(
        'ix_listing_dollar_per_cpu_mark_single_id',
        'listing',
        ['dollar_per_cpu_mark_single', 'id'],
    )


def downgrade() -> None:
    """Remove pagination indexes."""
    op.drop_index('ix_listing_dollar_per_cpu_mark_single_id', table_name='listing')
    op.drop_index('ix_listing_dollar_per_cpu_mark_multi_id', table_name='listing')
    op.drop_index('ix_listing_form_factor_id', table_name='listing')
    op.drop_index('ix_listing_manufacturer_id', table_name='listing')
    op.drop_index('ix_listing_adjusted_price_usd_id', table_name='listing')
    op.drop_index('ix_listing_price_usd_id', table_name='listing')
    op.drop_index('ix_listing_created_at_id_desc', table_name='listing')
    op.drop_index('ix_listing_updated_at_id_desc', table_name='listing')
