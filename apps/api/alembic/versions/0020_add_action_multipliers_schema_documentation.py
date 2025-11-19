"""Add action multipliers schema documentation

Revision ID: 0020
Revises: 0019
Create Date: 2025-10-16

This migration adds comprehensive documentation for the modifiers_json column
in the valuation_rule_action table, describing the expected schema for action
multipliers and condition multipliers.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade():
    """Add database comment documenting the modifiers_json schema structure."""

    # Add comprehensive schema documentation as a database comment
    op.execute(
        """
        COMMENT ON COLUMN valuation_rule_action.modifiers_json IS
        'Action multipliers configuration (JSONB). Supports two formats:

        1. Dynamic Field-Based Multipliers (Primary Format):
        {
            "multipliers": [
                {
                    "name": "RAM Generation Multiplier",
                    "field": "ram_spec.ddr_generation",
                    "conditions": [
                        {"value": "ddr3", "multiplier": 0.7},
                        {"value": "ddr4", "multiplier": 1.0},
                        {"value": "ddr5", "multiplier": 1.3}
                    ]
                }
            ]
        }

        2. Legacy Condition Multipliers (Backward Compatible):
        {
            "condition_multipliers": {
                "new": 1.0,
                "refurb": 0.75,
                "used": 0.6
            }
        }

        Both formats can coexist in the same object. Field paths use dot notation
        (e.g., "ram_spec.ddr_generation") to navigate nested structures. Multipliers
        are applied sequentially in the order defined.

        Empty object {} is valid and indicates no multipliers are applied.'
    """
    )


def downgrade():
    """Remove the database comment."""

    # Remove the column comment
    op.execute(
        """
        COMMENT ON COLUMN valuation_rule_action.modifiers_json IS NULL
    """
    )
