"""Add collections and sharing tables for Phase 1

Revision ID: 0028
Revises: 0bfccac265c8
Create Date: 2025-11-17 00:00:00.000000

This migration creates the foundation for Deal Brain's collections and sharing features:
- ListingShare: Public shareable deal pages via unique tokens
- UserShare: User-to-user deal sharing with expiry and import tracking
- Collection: User-defined groups of deals with visibility control
- CollectionItem: Individual deals within collections with status and notes

Changes:
1. Create listing_share table for public deal sharing (FR-A1)
2. Create user_share table for user-to-user sharing (FR-A3)
3. Create collection table for private collections (FR-B1)
4. Create collection_item table for collection items (FR-B2)
5. Add indexes for performance optimization
6. Add check constraints for data validation

Features:
- Share tokens for secure, unique URL generation
- Expiry management for shares (default 180 days for public, 30 days for user shares)
- View count tracking for public shares
- Message support for user-to-user shares
- Viewed/imported timestamp tracking
- Collection visibility control (private, unlisted, public)
- Item status tracking (undecided, shortlisted, rejected, bought)
- Position-based ordering for drag-and-drop support
- Cascade delete on parent record removal
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0028'
down_revision: Union[str, Sequence[str], None] = '0bfccac265c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create collections and sharing tables with indexes and constraints.

    Steps:
    1. Create user table (minimal auth foundation)
    2. Create listing_share table for public deal sharing
    3. Create user_share table for user-to-user sharing
    4. Create collection table for private collections
    5. Create collection_item table for collection items
    6. Create indexes for efficient querying
    7. Add check constraints for data validation
    """

    # ========================================================================
    # Step 1: Create user table (minimal foundation for authentication)
    # ========================================================================
    # Note: This is a minimal user table to support foreign keys for collections
    # and sharing. Full authentication (passwords, OAuth, etc.) will be added later.
    op.create_table(
        'user',
        # Primary key
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),

        # User identification
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=True),
        sa.Column('display_name', sa.String(length=255), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Indexes for user
    op.create_index(
        'ix_user_id',
        'user',
        ['id'],
    )
    op.create_index(
        'ix_user_username',
        'user',
        ['username'],
        unique=True,
    )
    op.create_index(
        'ix_user_email',
        'user',
        ['email'],
        unique=True,
    )

    # ========================================================================
    # Step 2: Create listing_share table (FR-A1: Shareable Deal Pages)
    # ========================================================================
    op.create_table(
        'listing_share',
        # Primary key
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),

        # Foreign keys
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),

        # Share management
        sa.Column('share_token', sa.String(length=64), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
    )

    # Indexes for listing_share
    op.create_index(
        'ix_listing_share_id',
        'listing_share',
        ['id'],
    )
    op.create_index(
        'ix_listing_share_token',
        'listing_share',
        ['share_token'],
        unique=True,
    )
    op.create_index(
        'idx_listing_share_listing',
        'listing_share',
        ['listing_id'],
    )
    op.create_index(
        'idx_listing_share_expires',
        'listing_share',
        ['expires_at'],
    )

    # ========================================================================
    # Step 2: Create user_share table (FR-A3: User-to-User Sharing)
    # ========================================================================
    op.create_table(
        'user_share',
        # Primary key
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),

        # Foreign keys
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),

        # Share management
        sa.Column('share_token', sa.String(length=64), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('shared_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False,
                  server_default=sa.text("(NOW() + INTERVAL '30 days')")),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipient_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ondelete='CASCADE'),
    )

    # Indexes for user_share
    op.create_index(
        'ix_user_share_id',
        'user_share',
        ['id'],
    )
    op.create_index(
        'ix_user_share_token',
        'user_share',
        ['share_token'],
        unique=True,
    )
    op.create_index(
        'idx_user_share_recipient_expires',
        'user_share',
        ['recipient_id', 'expires_at'],
    )
    op.create_index(
        'idx_user_share_sender',
        'user_share',
        ['sender_id'],
    )

    # ========================================================================
    # Step 3: Create collection table (FR-B1: Private Collections)
    # ========================================================================
    op.create_table(
        'collection',
        # Primary key
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),

        # Foreign keys
        sa.Column('user_id', sa.Integer(), nullable=False),

        # Collection metadata
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default='private'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),

        # Check constraints
        sa.CheckConstraint(
            "visibility IN ('private', 'unlisted', 'public')",
            name='ck_collection_visibility'
        ),
    )

    # Indexes for collection
    op.create_index(
        'ix_collection_id',
        'collection',
        ['id'],
    )
    op.create_index(
        'idx_collection_user',
        'collection',
        ['user_id'],
    )

    # ========================================================================
    # Step 4: Create collection_item table (FR-B2: Collection Items)
    # ========================================================================
    op.create_table(
        'collection_item',
        # Primary key
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),

        # Foreign keys
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),

        # Item metadata
        sa.Column('status', sa.String(length=20), nullable=False, server_default='undecided'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('added_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['collection_id'], ['collection.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ondelete='CASCADE'),

        # Unique constraint (can't add same deal twice to a collection)
        sa.UniqueConstraint('collection_id', 'listing_id', name='uq_collection_item'),

        # Check constraints
        sa.CheckConstraint(
            "status IN ('undecided', 'shortlisted', 'rejected', 'bought')",
            name='ck_collection_item_status'
        ),
    )

    # Indexes for collection_item
    op.create_index(
        'ix_collection_item_id',
        'collection_item',
        ['id'],
    )
    op.create_index(
        'idx_collection_item_collection',
        'collection_item',
        ['collection_id'],
    )
    op.create_index(
        'idx_collection_item_listing',
        'collection_item',
        ['listing_id'],
    )


def downgrade() -> None:
    """Remove collections and sharing tables and all associated indexes.

    Steps:
    1. Drop collection_item table and indexes
    2. Drop collection table and indexes
    3. Drop user_share table and indexes
    4. Drop listing_share table and indexes
    5. Drop user table and indexes
    """

    # Drop collection_item table and indexes
    op.drop_index('idx_collection_item_listing', table_name='collection_item')
    op.drop_index('idx_collection_item_collection', table_name='collection_item')
    op.drop_index('ix_collection_item_id', table_name='collection_item')
    op.drop_table('collection_item')

    # Drop collection table and indexes
    op.drop_index('idx_collection_user', table_name='collection')
    op.drop_index('ix_collection_id', table_name='collection')
    op.drop_table('collection')

    # Drop user_share table and indexes
    op.drop_index('idx_user_share_sender', table_name='user_share')
    op.drop_index('idx_user_share_recipient_expires', table_name='user_share')
    op.drop_index('ix_user_share_token', table_name='user_share')
    op.drop_index('ix_user_share_id', table_name='user_share')
    op.drop_table('user_share')

    # Drop listing_share table and indexes
    op.drop_index('idx_listing_share_expires', table_name='listing_share')
    op.drop_index('idx_listing_share_listing', table_name='listing_share')
    op.drop_index('ix_listing_share_token', table_name='listing_share')
    op.drop_index('ix_listing_share_id', table_name='listing_share')
    op.drop_table('listing_share')

    # Drop user table and indexes
    op.drop_index('ix_user_email', table_name='user')
    op.drop_index('ix_user_username', table_name='user')
    op.drop_index('ix_user_id', table_name='user')
    op.drop_table('user')
