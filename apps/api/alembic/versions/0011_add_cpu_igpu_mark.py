"""Add igpu_mark field to CPU table

Revision ID: 0011
Revises: 0010
Create Date: 2025-10-03 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    # Add igpu_mark column to cpu table
    op.add_column('cpu', sa.Column('igpu_mark', sa.Integer(), nullable=True))


def downgrade():
    # Remove igpu_mark column from cpu table
    op.drop_column('cpu', 'igpu_mark')
