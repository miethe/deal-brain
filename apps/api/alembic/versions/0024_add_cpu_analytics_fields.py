"""Add CPU analytics fields for performance metrics and price targets

Revision ID: 0024
Revises: 0023
Create Date: 2025-11-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0024'
down_revision: Union[str, Sequence[str], None] = '0023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add analytics fields to CPU table for price targets and performance value metrics.

    Price Target Fields:
    - Computed from listing analytics (adjusted prices)
    - Use standard deviation to calculate good/great/fair thresholds
    - Track confidence levels and sample sizes
    - Include timestamp for freshness checks

    Performance Value Fields:
    - Dollar per PassMark score metrics (single and multi-thread)
    - Percentile ranking for performance value
    - Human-readable rating (excellent/good/fair/poor)
    - Timestamp for calculation tracking

    All columns are nullable since existing CPUs have no pre-computed values.
    Indexes support efficient filtering and sorting by these analytics fields.
    """

    # Price Target Fields
    op.add_column('cpu', sa.Column('price_target_good', sa.Float(), nullable=True))
    op.add_column('cpu', sa.Column('price_target_great', sa.Float(), nullable=True))
    op.add_column('cpu', sa.Column('price_target_fair', sa.Float(), nullable=True))
    op.add_column('cpu', sa.Column('price_target_sample_size', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('cpu', sa.Column('price_target_confidence', sa.String(length=16), nullable=True))
    op.add_column('cpu', sa.Column('price_target_stddev', sa.Float(), nullable=True))
    op.add_column('cpu', sa.Column('price_target_updated_at', sa.DateTime(), nullable=True))

    # Performance Value Fields
    op.add_column('cpu', sa.Column('dollar_per_mark_single', sa.Float(), nullable=True))
    op.add_column('cpu', sa.Column('dollar_per_mark_multi', sa.Float(), nullable=True))
    op.add_column('cpu', sa.Column('performance_value_percentile', sa.Float(), nullable=True))
    op.add_column('cpu', sa.Column('performance_value_rating', sa.String(length=16), nullable=True))
    op.add_column('cpu', sa.Column('performance_metrics_updated_at', sa.DateTime(), nullable=True))

    # Create indexes for efficient querying
    # Index for filtering by price targets with confidence
    op.create_index(
        'idx_cpu_price_targets',
        'cpu',
        ['price_target_good', 'price_target_confidence'],
    )

    # Index for sorting by performance value metrics
    op.create_index(
        'idx_cpu_performance_value',
        'cpu',
        ['dollar_per_mark_single', 'dollar_per_mark_multi'],
    )

    # Index for filtering by manufacturer
    op.create_index(
        'idx_cpu_manufacturer',
        'cpu',
        ['manufacturer'],
    )

    # Index for filtering by socket type
    op.create_index(
        'idx_cpu_socket',
        'cpu',
        ['socket'],
    )

    # Index for filtering by core count
    op.create_index(
        'idx_cpu_cores',
        'cpu',
        ['cores'],
    )


def downgrade() -> None:
    """Remove CPU analytics fields and indexes."""
    # Drop indexes first
    op.drop_index('idx_cpu_cores', table_name='cpu')
    op.drop_index('idx_cpu_socket', table_name='cpu')
    op.drop_index('idx_cpu_manufacturer', table_name='cpu')
    op.drop_index('idx_cpu_performance_value', table_name='cpu')
    op.drop_index('idx_cpu_price_targets', table_name='cpu')

    # Drop performance value fields
    op.drop_column('cpu', 'performance_metrics_updated_at')
    op.drop_column('cpu', 'performance_value_rating')
    op.drop_column('cpu', 'performance_value_percentile')
    op.drop_column('cpu', 'dollar_per_mark_multi')
    op.drop_column('cpu', 'dollar_per_mark_single')

    # Drop price target fields
    op.drop_column('cpu', 'price_target_updated_at')
    op.drop_column('cpu', 'price_target_stddev')
    op.drop_column('cpu', 'price_target_confidence')
    op.drop_column('cpu', 'price_target_sample_size')
    op.drop_column('cpu', 'price_target_fair')
    op.drop_column('cpu', 'price_target_great')
    op.drop_column('cpu', 'price_target_good')
