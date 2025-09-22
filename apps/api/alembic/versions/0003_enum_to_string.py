"""Convert enum columns to strings"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_enum_to_string"
down_revision = "0002_import_sessions"
branch_labels = None
depends_on = None


ENUM_TYPES = [
    "component_type",
    "component_metric",
    "condition",
    "listing_status",
    "port_type",
]


def upgrade() -> None:
    # Drop enum defaults before altering types
    op.execute("ALTER TABLE listing ALTER COLUMN condition DROP DEFAULT")
    op.execute("ALTER TABLE listing ALTER COLUMN status DROP DEFAULT")

    op.alter_column(
        "valuation_rule",
        "component_type",
        existing_type=sa.Enum(name="component_type"),
        type_=sa.String(length=32),
        existing_nullable=False,
        postgresql_using="component_type::text",
    )
    op.alter_column(
        "valuation_rule",
        "metric",
        existing_type=sa.Enum(name="component_metric"),
        type_=sa.String(length=16),
        existing_nullable=False,
        postgresql_using="metric::text",
    )

    op.alter_column(
        "listing_component",
        "component_type",
        existing_type=sa.Enum(name="component_type"),
        type_=sa.String(length=32),
        existing_nullable=False,
        postgresql_using="component_type::text",
    )

    op.alter_column(
        "listing",
        "condition",
        existing_type=sa.Enum(name="condition"),
        type_=sa.String(length=16),
        existing_nullable=False,
        postgresql_using="condition::text",
        server_default=sa.text("'used'"),
    )
    op.alter_column(
        "listing",
        "status",
        existing_type=sa.Enum(name="listing_status"),
        type_=sa.String(length=16),
        existing_nullable=False,
        postgresql_using="status::text",
        server_default=sa.text("'active'"),
    )

    op.alter_column(
        "port",
        "type",
        existing_type=sa.Enum(name="port_type"),
        type_=sa.String(length=32),
        existing_nullable=False,
        postgresql_using="type::text",
    )

    for enum_name in ENUM_TYPES:
        op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))


def downgrade() -> None:
    component_type = sa.Enum(
        "ram",
        "ssd",
        "hdd",
        "os_license",
        "wifi",
        "gpu",
        "misc",
        name="component_type",
    )
    component_metric = sa.Enum("per_gb", "per_tb", "flat", name="component_metric")
    condition = sa.Enum("new", "refurb", "used", name="condition")
    listing_status = sa.Enum("active", "archived", "pending", name="listing_status")
    port_type = sa.Enum(
        "usb_a",
        "usb_c",
        "thunderbolt",
        "hdmi",
        "displayport",
        "rj45_1g",
        "rj45_2_5g",
        "rj45_10g",
        "audio",
        "sdxc",
        "pcie_x16",
        "pcie_x8",
        "m2_slot",
        "sata_bay",
        "other",
        name="port_type",
    )

    bind = op.get_bind()
    for enum in [component_type, component_metric, condition, listing_status, port_type]:
        enum.create(bind, checkfirst=True)

    op.alter_column(
        "valuation_rule",
        "component_type",
        existing_type=sa.String(length=32),
        type_=component_type,
        existing_nullable=False,
        postgresql_using="component_type::component_type",
    )
    op.alter_column(
        "valuation_rule",
        "metric",
        existing_type=sa.String(length=16),
        type_=component_metric,
        existing_nullable=False,
        postgresql_using="metric::component_metric",
    )

    op.alter_column(
        "listing_component",
        "component_type",
        existing_type=sa.String(length=32),
        type_=component_type,
        existing_nullable=False,
        postgresql_using="component_type::component_type",
    )

    op.alter_column(
        "listing",
        "condition",
        existing_type=sa.String(length=16),
        type_=condition,
        existing_nullable=False,
        postgresql_using="condition::condition",
        server_default=sa.text("'used'::condition"),
    )
    op.alter_column(
        "listing",
        "status",
        existing_type=sa.String(length=16),
        type_=listing_status,
        existing_nullable=False,
        postgresql_using="status::listing_status",
        server_default=sa.text("'active'::listing_status"),
    )

    op.alter_column(
        "port",
        "type",
        existing_type=sa.String(length=32),
        type_=port_type,
        existing_nullable=False,
        postgresql_using="type::port_type",
    )
