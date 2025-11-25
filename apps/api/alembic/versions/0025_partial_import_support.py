"""Add partial import support to Listing model

Revision ID: 0025
Revises: 0024
Create Date: 2025-11-08 00:00:00.000000

This migration enables partial imports where price_usd may be missing,
and adds quality/provenance tracking fields for extraction metadata.

Changes:
1. Make listing.price_usd nullable (currently NOT NULL)
2. Add listing.quality column (String(20), default='full')
3. Add listing.extraction_metadata column (JSON, tracks field provenance)
4. Add listing.missing_fields column (JSON, lists fields needing manual entry)

Downgrade Strategy:
- Deletes partial imports (where price_usd IS NULL)
- Drops new columns
- Restores price_usd NOT NULL constraint
- WARNING: Data loss on downgrade for partial imports

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0025"
down_revision: Union[str, Sequence[str], None] = "0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add partial import support to Listing model.

    Steps:
    1. Make price_usd nullable to allow partial imports
    2. Add quality column with 'full' default
    3. Add extraction_metadata for field provenance tracking
    4. Add missing_fields for manual entry tracking

    All existing listings get quality='full' and empty metadata by default.
    """

    # Step 1: Make price_usd nullable
    # Drop NOT NULL constraint on price_usd to allow partial imports
    op.alter_column(
        "listing",
        "price_usd",
        existing_type=sa.Float(),
        nullable=True,
        existing_nullable=False,
    )

    # Step 2: Add quality column
    # Tracks data completeness: 'full' (all required fields) or 'partial' (missing fields)
    op.add_column(
        "listing",
        sa.Column(
            "quality",
            sa.String(length=20),
            nullable=False,
            server_default="full",
        ),
    )

    # Step 3: Add extraction_metadata column
    # Tracks field provenance: {field_name: 'extracted'|'manual'|'extraction_failed'}
    op.add_column(
        "listing",
        sa.Column(
            "extraction_metadata",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )

    # Step 4: Add missing_fields column
    # Tracks fields requiring manual entry: ['price', 'cpu', ...]
    op.add_column(
        "listing",
        sa.Column(
            "missing_fields",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )

    # Create index on quality for efficient filtering
    op.create_index(
        "idx_listing_quality",
        "listing",
        ["quality"],
    )

    # Create composite index on quality + created_at for sorting partial imports
    op.create_index(
        "idx_listing_quality_created",
        "listing",
        ["quality", "created_at"],
    )


def downgrade() -> None:
    """Remove partial import support from Listing model.

    WARNING: This will DELETE all partial imports (listings with price_usd IS NULL).

    Steps:
    1. Delete partial imports (price_usd IS NULL)
    2. Drop indexes
    3. Drop new columns
    4. Restore price_usd NOT NULL constraint
    """

    # Drop indexes first
    op.drop_index("idx_listing_quality_created", table_name="listing")
    op.drop_index("idx_listing_quality", table_name="listing")

    # Delete partial imports before restoring NOT NULL constraint
    # WARNING: Data loss - partial imports will be permanently deleted
    op.execute(
        """
        DELETE FROM listing
        WHERE price_usd IS NULL
    """
    )

    # Drop new columns
    op.drop_column("listing", "missing_fields")
    op.drop_column("listing", "extraction_metadata")
    op.drop_column("listing", "quality")

    # Restore NOT NULL constraint on price_usd
    op.alter_column(
        "listing",
        "price_usd",
        existing_type=sa.Float(),
        nullable=False,
        existing_nullable=True,
    )
