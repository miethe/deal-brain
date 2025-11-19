"""Add progress_pct to ImportSession

Revision ID: 0022
Revises: 0bfccac265c8
Create Date: 2025-10-22 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0022"
down_revision: Union[str, Sequence[str], None] = "0bfccac265c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add progress_pct field to import_session table."""
    op.add_column(
        "import_session", sa.Column("progress_pct", sa.Integer(), nullable=True, server_default="0")
    )


def downgrade() -> None:
    """Remove progress_pct field from import_session table."""
    op.drop_column("import_session", "progress_pct")
