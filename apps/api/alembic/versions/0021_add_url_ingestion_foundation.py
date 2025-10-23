"""Add URL ingestion foundation

Revision ID: 0021
Revises: 0020
Create Date: 2025-10-17

Phase 1 of URL Ingestion feature implementation:
- Extends Listing with vendor_item_id, marketplace, provenance, last_seen_at
- Extends ImportSession with source_type, url, adapter_config
- Creates RawPayload table for storing adapter payloads
- Creates IngestionMetric table for telemetry tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade():
    # ========================================================================
    # Listing Table: Add URL ingestion fields
    # ========================================================================
    op.add_column('listing', sa.Column('vendor_item_id', sa.String(128), nullable=True))
    op.add_column('listing', sa.Column('marketplace', sa.String(16), nullable=False, server_default='other'))
    op.add_column('listing', sa.Column('provenance', sa.String(64), nullable=True))
    op.add_column('listing', sa.Column('last_seen_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))

    # Add unique constraint for vendor_item_id + marketplace
    op.create_unique_constraint('uq_listing_vendor_id', 'listing', ['vendor_item_id', 'marketplace'])

    # Add index for deduplication queries
    op.create_index('ix_listing_vendor_marketplace', 'listing', ['vendor_item_id', 'marketplace'])

    # ========================================================================
    # ImportSession Table: Add URL job fields
    # ========================================================================
    op.add_column('import_session', sa.Column('source_type', sa.String(16), nullable=False, server_default='excel'))
    op.add_column('import_session', sa.Column('url', sa.Text(), nullable=True))
    op.add_column('import_session', sa.Column('adapter_config', sa.JSON(), nullable=False, server_default='{}'))

    # ========================================================================
    # RawPayload Table: Create new table for adapter payloads
    # ========================================================================
    op.create_table(
        'raw_payload',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('adapter', sa.String(64), nullable=False),
        sa.Column('source_type', sa.String(16), nullable=False, server_default='json'),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('ttl_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add index for querying payloads by listing and adapter
    op.create_index('ix_raw_payload_listing_adapter', 'raw_payload', ['listing_id', 'adapter'])

    # ========================================================================
    # IngestionMetric Table: Create new table for telemetry
    # ========================================================================
    op.create_table(
        'ingestion_metric',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('adapter', sa.String(64), nullable=False),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('p50_latency_ms', sa.Integer(), nullable=True),
        sa.Column('p95_latency_ms', sa.Integer(), nullable=True),
        sa.Column('field_completeness_pct', sa.Float(), nullable=True),
        sa.Column('measured_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Add index for time-series queries
    op.create_index('ix_ingestion_metric_adapter_measured', 'ingestion_metric', ['adapter', 'measured_at'])


def downgrade():
    # Drop IngestionMetric table and indexes
    op.drop_index('ix_ingestion_metric_adapter_measured', table_name='ingestion_metric')
    op.drop_table('ingestion_metric')

    # Drop RawPayload table and indexes
    op.drop_index('ix_raw_payload_listing_adapter', table_name='raw_payload')
    op.drop_table('raw_payload')

    # Remove ImportSession URL job fields
    op.drop_column('import_session', 'adapter_config')
    op.drop_column('import_session', 'url')
    op.drop_column('import_session', 'source_type')

    # Remove Listing URL ingestion fields
    op.drop_index('ix_listing_vendor_marketplace', table_name='listing')
    op.drop_constraint('uq_listing_vendor_id', 'listing', type_='unique')
    op.drop_column('listing', 'last_seen_at')
    op.drop_column('listing', 'provenance')
    op.drop_column('listing', 'marketplace')
    op.drop_column('listing', 'vendor_item_id')
