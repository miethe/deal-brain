"""Add bulk job tracking to ImportSession

Revision ID: 0026
Revises: 0025
Create Date: 2025-11-08 00:00:00.000000

This migration enables tracking individual URLs within bulk import jobs
by linking ImportSessions to bulk_job_id and tracking completion status.

Changes:
1. Add import_session.bulk_job_id column (String(36), indexed)
2. Add import_session.quality column (String(20), nullable)
3. Add import_session.listing_id column (Integer, ForeignKey)
4. Add import_session.completed_at column (DateTime(timezone=True))

These fields enable:
- Grouping multiple URL imports under a single bulk job ID
- Tracking data quality per import (full/partial)
- Linking import sessions directly to created listings
- Recording completion timestamps for status polling

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0026"
down_revision: Union[str, Sequence[str], None] = "0025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add bulk job tracking fields to ImportSession.

    Steps:
    1. Add bulk_job_id to group multiple imports under one bulk job
    2. Add quality to track data completeness per import
    3. Add listing_id to link import sessions to created listings
    4. Add completed_at to track when import finished
    5. Create index on bulk_job_id for efficient bulk job queries
    """

    # Step 1: Add bulk_job_id column
    # Groups multiple URL imports under a single bulk job (UUID format)
    op.add_column(
        "import_session",
        sa.Column(
            "bulk_job_id",
            sa.String(length=36),
            nullable=True,
        ),
    )

    # Step 2: Add quality column
    # Tracks data completeness for this import: 'full' or 'partial'
    op.add_column(
        "import_session",
        sa.Column(
            "quality",
            sa.String(length=20),
            nullable=True,
        ),
    )

    # Step 3: Add listing_id column
    # Links import session to the created listing (if successful)
    op.add_column(
        "import_session",
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listing.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Step 4: Add completed_at column
    # Tracks when import finished processing (success, partial, or failure)
    op.add_column(
        "import_session",
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Create index on bulk_job_id for efficient bulk job status queries
    op.create_index(
        "idx_import_session_bulk_job_id",
        "import_session",
        ["bulk_job_id"],
    )

    # Create composite index on bulk_job_id + status for filtering
    op.create_index(
        "idx_import_session_bulk_job_status",
        "import_session",
        ["bulk_job_id", "status"],
    )

    # Create index on listing_id for reverse lookups
    op.create_index(
        "idx_import_session_listing_id",
        "import_session",
        ["listing_id"],
    )


def downgrade() -> None:
    """Remove bulk job tracking fields from ImportSession.

    Steps:
    1. Drop indexes
    2. Drop new columns
    """

    # Drop indexes first
    op.drop_index("idx_import_session_listing_id", table_name="import_session")
    op.drop_index("idx_import_session_bulk_job_status", table_name="import_session")
    op.drop_index("idx_import_session_bulk_job_id", table_name="import_session")

    # Drop columns
    op.drop_column("import_session", "completed_at")
    op.drop_column("import_session", "listing_id")
    op.drop_column("import_session", "quality")
    op.drop_column("import_session", "bulk_job_id")
