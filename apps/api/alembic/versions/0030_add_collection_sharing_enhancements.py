"""Add collection sharing enhancements for Phase 2a

Revision ID: 0030
Revises: 5dc4b78ba7c1
Create Date: 2025-11-19 00:00:00.000000

This migration implements Phase 2a database schema changes for shareable collections:
- Add discovery indexes to collection table for visibility-based queries
- Create collection_share_token table for shareable collection links

Changes:
1. Add composite index on collection (user_id, visibility) for user collection filtering
2. Add index on collection (visibility, created_at) for recent public collection discovery
3. Add index on collection (visibility, updated_at) for trending collection discovery
4. Create collection_share_token table with token-based sharing support
5. Add indexes for efficient collection share token lookups

Features:
- Visibility-based collection discovery (private, unlisted, public)
- Shareable collection tokens with view count tracking
- Optional expiry for share tokens
- Cascade delete when parent collection is removed
- Efficient querying for public/unlisted collection discovery
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0030'
down_revision: Union[str, Sequence[str], None] = '5dc4b78ba7c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add collection sharing enhancements.

    Steps:
    1. Add discovery indexes to collection table
    2. Create collection_share_token table
    3. Add indexes for efficient token lookups
    """

    # ========================================================================
    # Task 2a-db-1: Add discovery indexes to collection table
    # ========================================================================
    # Note: The visibility column already exists with CHECK constraint from migration 0028
    # We're adding indexes to optimize visibility-based queries

    # Composite index for user's collections filtered by visibility
    # Used for queries like: "Get all my public collections"
    op.create_index(
        'idx_collection_user_visibility',
        'collection',
        ['user_id', 'visibility'],
    )

    # Index for recent public/unlisted collections discovery
    # Used for queries like: "Show recent public collections"
    op.create_index(
        'idx_collection_visibility_created',
        'collection',
        ['visibility', 'created_at'],
    )

    # Index for trending collections (recently updated public collections)
    # Used for queries like: "Show recently active public collections"
    op.create_index(
        'idx_collection_visibility_updated',
        'collection',
        ['visibility', 'updated_at'],
    )

    # ========================================================================
    # Task 2a-db-2: Create collection_share_token table
    # ========================================================================
    op.create_table(
        'collection_share_token',
        # Primary key
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),

        # Foreign key to collection
        sa.Column('collection_id', sa.Integer(), nullable=False),

        # Share token for URL generation
        sa.Column('token', sa.Text(), nullable=False),

        # View tracking
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),

        # Optional expiry (soft-delete via expires_at timestamp)
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign key constraint with CASCADE delete
        sa.ForeignKeyConstraint(
            ['collection_id'],
            ['collection.id'],
            name='fk_collection_share_token_collection_id',
            ondelete='CASCADE'
        ),

        # Unique constraint on token
        sa.UniqueConstraint('token', name='uq_collection_share_token_token'),
    )

    # ========================================================================
    # Task 2a-db-3: Create indexes for collection_share_token
    # ========================================================================

    # Primary key index (automatically created, but explicit for documentation)
    op.create_index(
        'ix_collection_share_token_id',
        'collection_share_token',
        ['id'],
    )

    # Index on token for share URL lookups (most common query)
    # Note: Already has UNIQUE constraint, but explicit index helps with lookups
    op.create_index(
        'ix_collection_share_token_token',
        'collection_share_token',
        ['token'],
        unique=True,
    )

    # Index on collection_id for finding all share tokens for a collection
    op.create_index(
        'idx_collection_share_token_collection',
        'collection_share_token',
        ['collection_id'],
    )

    # Index on expires_at for cleanup queries
    # Used for queries like: "Find all expired share tokens"
    op.create_index(
        'idx_collection_share_token_expires',
        'collection_share_token',
        ['expires_at'],
    )


def downgrade() -> None:
    """Remove collection sharing enhancements.

    Steps:
    1. Drop collection_share_token table and indexes
    2. Drop collection discovery indexes
    """

    # Drop collection_share_token indexes
    op.drop_index('idx_collection_share_token_expires', table_name='collection_share_token')
    op.drop_index('idx_collection_share_token_collection', table_name='collection_share_token')
    op.drop_index('ix_collection_share_token_token', table_name='collection_share_token')
    op.drop_index('ix_collection_share_token_id', table_name='collection_share_token')

    # Drop collection_share_token table
    op.drop_table('collection_share_token')

    # Drop collection discovery indexes
    op.drop_index('idx_collection_visibility_updated', table_name='collection')
    op.drop_index('idx_collection_visibility_created', table_name='collection')
    op.drop_index('idx_collection_user_visibility', table_name='collection')
