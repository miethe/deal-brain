"""fix_collection_item_timestamps

Fix CollectionItem timestamp mismatch between model and migration.

The CollectionItem model inherits from TimestampMixin (which provides created_at and updated_at)
but the original migration 0028 only created added_at and updated_at columns. This migration
adds the missing created_at column to align with the model definition.

Revision ID: 5dc4b78ba7c1
Revises: 6d065f2ece00
Create Date: 2025-11-18 13:13:53.132106

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5dc4b78ba7c1"
down_revision: Union[str, Sequence[str], None] = "6d065f2ece00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add created_at column to collection_item table.

    The CollectionItem model inherits from TimestampMixin which provides created_at,
    but the original migration only created added_at. We add created_at and populate
    it with the value from added_at for existing rows.
    """
    # Add created_at column, initially nullable
    op.add_column("collection_item", sa.Column("created_at", sa.DateTime(), nullable=True))

    # Populate created_at with added_at values for existing rows
    op.execute(
        """
        UPDATE collection_item
        SET created_at = added_at
        WHERE created_at IS NULL
        """
    )

    # Make created_at non-nullable now that it's populated
    op.alter_column("collection_item", "created_at", nullable=False, server_default=sa.func.now())


def downgrade() -> None:
    """Remove created_at column from collection_item table."""
    op.drop_column("collection_item", "created_at")
