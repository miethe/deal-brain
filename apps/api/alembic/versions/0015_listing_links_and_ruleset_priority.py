"""Rename listing URL column, add supplemental links, and extend rulesets with priority/conditions

Revision ID: 0015
Revises: 0014
Create Date: 2025-10-08 09:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade():
    # Rename listings.url to listings.listing_url
    op.alter_column("listing", "url", new_column_name="listing_url")

    # Add supplemental links and static ruleset assignment columns
    op.add_column(
        "listing",
        sa.Column(
            "other_urls",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column("listing", sa.Column("ruleset_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_listing_ruleset_id",
        "listing",
        "valuation_ruleset",
        ["ruleset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_listing_ruleset_id", "listing", ["ruleset_id"])

    # Extend valuation_ruleset with priority/condition metadata
    op.add_column(
        "valuation_ruleset",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="10"),
    )
    op.add_column(
        "valuation_ruleset",
        sa.Column(
            "conditions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.create_index(
        "ix_valuation_ruleset_active_priority",
        "valuation_ruleset",
        ["is_active", "priority"],
    )

    # Ensure existing rows have defaults applied before dropping server defaults
    op.execute("UPDATE valuation_ruleset SET priority = 10 WHERE priority IS NULL")
    op.execute(
        "UPDATE valuation_ruleset SET conditions_json = '{}'::jsonb WHERE conditions_json IS NULL"
    )

    # Remove server defaults so application-level defaults take over
    op.alter_column("valuation_ruleset", "priority", server_default=None)
    op.alter_column("valuation_ruleset", "conditions_json", server_default=None)
    op.alter_column("listing", "other_urls", server_default=None)


def downgrade():
    # Drop ruleset metadata columns and indexes
    op.alter_column("listing", "other_urls", server_default="[]")
    op.drop_index("ix_listing_ruleset_id", table_name="listing")
    op.drop_constraint("fk_listing_ruleset_id", "listing", type_="foreignkey")
    op.drop_column("listing", "ruleset_id")
    op.drop_column("listing", "other_urls")
    op.alter_column("listing", "listing_url", new_column_name="url")

    op.drop_index("ix_valuation_ruleset_active_priority", table_name="valuation_ruleset")
    op.drop_column("valuation_ruleset", "conditions_json")
    op.drop_column("valuation_ruleset", "priority")
