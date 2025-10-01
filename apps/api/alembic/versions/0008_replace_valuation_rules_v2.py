"""Replace valuation rules with v2 system

Revision ID: 0008
Revises: 0007
Create Date: 2025-10-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007_custom_field_locking'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old table and relationships
    op.drop_table('listing_component')
    op.drop_table('valuation_rule')

    # Create valuation_ruleset
    op.create_table(
        'valuation_ruleset',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=32), nullable=False, server_default='1.0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.String(length=128), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_ruleset_active', 'valuation_ruleset', ['is_active'])
    op.create_index('idx_ruleset_created_by', 'valuation_ruleset', ['created_by'])

    # Create valuation_rule_group
    op.create_table(
        'valuation_rule_group',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ruleset_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('weight', sa.Numeric(precision=5, scale=4), nullable=True, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['ruleset_id'], ['valuation_ruleset.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ruleset_id', 'name', name='uq_rule_group_ruleset_name')
    )
    op.create_index('idx_rule_group_ruleset', 'valuation_rule_group', ['ruleset_id'])
    op.create_index('idx_rule_group_category', 'valuation_rule_group', ['category'])

    # Create valuation_rule_v2
    op.create_table(
        'valuation_rule_v2',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('evaluation_order', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_by', sa.String(length=128), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['valuation_rule_group.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'name', name='uq_rule_v2_group_name')
    )
    op.create_index('idx_rule_v2_group', 'valuation_rule_v2', ['group_id'])
    op.create_index('idx_rule_v2_active', 'valuation_rule_v2', ['is_active'])
    op.create_index('idx_rule_v2_eval_order', 'valuation_rule_v2', ['group_id', 'evaluation_order'])

    # Create valuation_rule_condition
    op.create_table(
        'valuation_rule_condition',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('parent_condition_id', sa.Integer(), nullable=True),
        sa.Column('field_name', sa.String(length=128), nullable=False),
        sa.Column('field_type', sa.String(length=32), nullable=False),
        sa.Column('operator', sa.String(length=32), nullable=False),
        sa.Column('value_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('logical_operator', sa.String(length=8), nullable=True),
        sa.Column('group_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['valuation_rule_v2.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_condition_id'], ['valuation_rule_condition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_condition_rule', 'valuation_rule_condition', ['rule_id'])
    op.create_index('idx_condition_parent', 'valuation_rule_condition', ['parent_condition_id'])

    # Create valuation_rule_action
    op.create_table(
        'valuation_rule_action',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=32), nullable=False),
        sa.Column('metric', sa.String(length=32), nullable=True),
        sa.Column('value_usd', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('unit_type', sa.String(length=32), nullable=True),
        sa.Column('formula', sa.Text(), nullable=True),
        sa.Column('modifiers_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['valuation_rule_v2.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_action_rule', 'valuation_rule_action', ['rule_id'])

    # Create valuation_rule_version
    op.create_table(
        'valuation_rule_version',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('snapshot_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['valuation_rule_v2.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_id', 'version_number', name='uq_rule_version')
    )
    op.create_index('idx_version_rule', 'valuation_rule_version', ['rule_id'])

    # Create valuation_rule_audit
    op.create_table(
        'valuation_rule_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('actor', sa.String(length=128), nullable=True),
        sa.Column('changes_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('impact_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['valuation_rule_v2.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_rule', 'valuation_rule_audit', ['rule_id'])
    op.create_index('idx_audit_created', 'valuation_rule_audit', ['created_at'])

    # Recreate listing_component without valuation_rule foreign key
    op.create_table(
        'listing_component',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('component_type', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('adjustment_value_usd', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop new tables
    op.drop_table('listing_component')
    op.drop_table('valuation_rule_audit')
    op.drop_table('valuation_rule_version')
    op.drop_table('valuation_rule_action')
    op.drop_table('valuation_rule_condition')
    op.drop_table('valuation_rule_v2')
    op.drop_table('valuation_rule_group')
    op.drop_table('valuation_ruleset')

    # Recreate old valuation_rule table
    op.create_table(
        'valuation_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('component_type', sa.String(length=32), nullable=False),
        sa.Column('metric', sa.String(length=16), nullable=False),
        sa.Column('unit_value_usd', sa.Float(), nullable=False),
        sa.Column('condition_new', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('condition_refurb', sa.Float(), nullable=False, server_default='0.75'),
        sa.Column('condition_used', sa.Float(), nullable=False, server_default='0.6'),
        sa.Column('age_curve_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('attributes_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Recreate old listing_component table
    op.create_table(
        'listing_component',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=True),
        sa.Column('component_type', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('adjustment_value_usd', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['valuation_rule.id']),
        sa.PrimaryKeyConstraint('id')
    )
