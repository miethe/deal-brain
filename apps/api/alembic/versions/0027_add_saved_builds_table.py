"""Add saved_builds table for Deal Builder feature

Revision ID: 0027
Revises: 0026
Create Date: 2025-11-14 00:00:00.000000

This migration creates the saved_builds table for the Deal Builder feature.
Users can create custom PC builds by selecting components and receive real-time
valuation feedback. Builds can be saved and shared via unique share tokens.

Changes:
1. Create saved_builds table with component references and snapshots
2. Add indexes for user_id, share_token, and visibility queries
3. Add unique constraint on share_token for URL sharing
4. Add check constraint to ensure name is not empty
5. Implement soft delete pattern with deleted_at column

Features:
- Component references to CPU, GPU, and other catalog tables
- JSONB snapshots for pricing, metrics, and valuation breakdowns
- Visibility control (private, public, unlisted)
- Shareable URLs via unique share tokens
- Tags for build categorization
- Soft delete pattern for audit trail

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0027'
down_revision: Union[str, Sequence[str], None] = '0026'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create saved_builds table with indexes and constraints.

    Steps:
    1. Create saved_builds table with all fields
    2. Add foreign key constraints to CPU and GPU tables
    3. Create indexes for efficient querying
    4. Add unique constraint on share_token
    5. Add check constraint for non-empty name
    """

    # Step 1: Create saved_builds table
    op.create_table(
        'saved_builds',
        # Primary key
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),

        # Ownership
        sa.Column('user_id', sa.Integer(), nullable=True),

        # Build metadata
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),

        # Visibility & sharing
        sa.Column('visibility', sa.String(length=16), nullable=False, server_default='private'),
        sa.Column('share_token', sa.String(length=64), nullable=False),

        # Component references
        sa.Column('cpu_id', sa.Integer(), nullable=True),
        sa.Column('gpu_id', sa.Integer(), nullable=True),
        sa.Column('ram_spec_id', sa.Integer(), nullable=True),
        sa.Column('storage_spec_id', sa.Integer(), nullable=True),
        sa.Column('psu_spec_id', sa.Integer(), nullable=True),
        sa.Column('case_spec_id', sa.Integer(), nullable=True),

        # Snapshot fields (JSONB for efficient storage and queryability)
        sa.Column('pricing_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('metrics_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('valuation_breakdown', postgresql.JSONB(), nullable=True),

        # Timestamps (via TimestampMixin)
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),

        # Soft delete
        sa.Column('deleted_at', sa.DateTime(), nullable=True),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['cpu_id'], ['cpu.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['gpu_id'], ['gpu.id'], ondelete='SET NULL'),

        # Check constraints
        sa.CheckConstraint("name != ''", name='ck_saved_builds_name_not_empty'),
    )

    # Step 2: Create index on id (primary key index)
    op.create_index(
        'ix_saved_builds_id',
        'saved_builds',
        ['id'],
    )

    # Step 3: Create composite index on user_id and deleted_at
    # For querying active builds by user
    op.create_index(
        'idx_user_builds',
        'saved_builds',
        ['user_id', 'deleted_at'],
    )

    # Step 4: Create unique index on share_token
    # For efficient share URL lookups
    op.create_index(
        'ix_saved_builds_share_token',
        'saved_builds',
        ['share_token'],
        unique=True,
    )

    # Step 5: Create composite index on visibility and deleted_at
    # For querying public/unlisted builds
    op.create_index(
        'idx_visibility',
        'saved_builds',
        ['visibility', 'deleted_at'],
    )


def downgrade() -> None:
    """Remove saved_builds table and all associated indexes.

    Steps:
    1. Drop indexes
    2. Drop table (foreign keys are dropped automatically)
    """

    # Drop indexes first
    op.drop_index('idx_visibility', table_name='saved_builds')
    op.drop_index('ix_saved_builds_share_token', table_name='saved_builds')
    op.drop_index('idx_user_builds', table_name='saved_builds')
    op.drop_index('ix_saved_builds_id', table_name='saved_builds')

    # Drop table (foreign keys and check constraints are dropped automatically)
    op.drop_table('saved_builds')
