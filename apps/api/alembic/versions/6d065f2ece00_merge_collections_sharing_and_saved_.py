"""Merge collections/sharing and saved builds branches

Revision ID: 6d065f2ece00
Revises: 0027, 0028
Create Date: 2025-11-18 13:09:52.411874

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6d065f2ece00"
down_revision: Union[str, Sequence[str], None] = ("0027", "0028")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
