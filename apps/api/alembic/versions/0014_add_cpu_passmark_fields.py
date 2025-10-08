"""Add PassMark metadata columns to CPU table

Revision ID: 0014
Revises: 0013
Create Date: 2025-10-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade():
    # Add PassMark metadata columns to cpu table
    op.add_column('cpu', sa.Column('passmark_slug', sa.String(length=512), nullable=True))
    op.add_column('cpu', sa.Column('passmark_category', sa.String(length=64), nullable=True))
    op.add_column('cpu', sa.Column('passmark_id', sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column('cpu', 'passmark_id')
    op.drop_column('cpu', 'passmark_category')
    op.drop_column('cpu', 'passmark_slug')
