"""Add notifications table for in-app notifications

Revision ID: 0029
Revises: 0028
Create Date: 2025-11-18 00:00:00.000000

This migration creates the notification table for in-app user notifications:
- Notification: User notifications for share events, collection updates, and system alerts

Changes:
1. Create notification table with user_id, type, title, message, and timestamps
2. Add indexes for efficient querying (user_id, type, read_at)
3. Add foreign key constraint to user table
4. Add optional foreign key to user_share table for share-related notifications
5. Support for read/unread status tracking

Features:
- Notification types: share_received, share_imported, collection_updated, system
- Read/unread status with read_at timestamp
- Link to related share for context
- Cascade delete when user is deleted
- Efficient querying with composite index on (user_id, read_at)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0029'
down_revision: Union[str, Sequence[str], None] = '0028'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notification table with indexes and constraints.

    Steps:
    1. Create notification table
    2. Create indexes for efficient querying
    3. Add foreign key constraints
    """

    # ========================================================================
    # Step 1: Create notification table
    # ========================================================================
    op.create_table(
        'notification',
        # Primary key
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),

        # Foreign keys
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('share_id', sa.Integer(), nullable=True),

        # Notification content
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),

        # Status tracking
        sa.Column('read_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
            name='fk_notification_user_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['share_id'],
            ['user_share.id'],
            name='fk_notification_share_id',
            ondelete='CASCADE'
        ),
    )

    # ========================================================================
    # Step 2: Create indexes for efficient querying
    # ========================================================================

    # Index on user_id for user inbox queries
    op.create_index(
        'ix_notification_user_id',
        'notification',
        ['user_id'],
    )

    # Index on type for filtering by notification type
    op.create_index(
        'ix_notification_type',
        'notification',
        ['type'],
    )

    # Index on read_at for unread filtering
    op.create_index(
        'ix_notification_read_at',
        'notification',
        ['read_at'],
    )

    # Composite index for user inbox with unread filter (most common query)
    op.create_index(
        'ix_notification_user_read',
        'notification',
        ['user_id', 'read_at'],
    )


def downgrade() -> None:
    """Drop notification table and indexes."""

    # Drop indexes
    op.drop_index('ix_notification_user_read', table_name='notification')
    op.drop_index('ix_notification_read_at', table_name='notification')
    op.drop_index('ix_notification_type', table_name='notification')
    op.drop_index('ix_notification_user_id', table_name='notification')

    # Drop table
    op.drop_table('notification')
