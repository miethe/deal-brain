"""Introduce RAM specs and storage profiles for listing classification

Revision ID: 0017
Revises: 0016
Create Date: 2025-10-11 09:00:00.000000
"""

from __future__ import annotations

from typing import Any

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from dealbrain_core.enums import RamGeneration, StorageMedium

# revision identifiers, used by Alembic.
revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    ram_generation_enum = sa.Enum(RamGeneration, name="ram_generation")
    storage_medium_enum = sa.Enum(StorageMedium, name="storage_medium")
    ram_generation_enum.create(bind, checkfirst=True)
    storage_medium_enum.create(bind, checkfirst=True)

    op.create_table(
        "ram_spec",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(length=128), nullable=True),
        sa.Column(
            "ddr_generation",
            ram_generation_enum,
            nullable=False,
            server_default=RamGeneration.UNKNOWN.value,
        ),
        sa.Column("speed_mhz", sa.Integer(), nullable=True),
        sa.Column("module_count", sa.Integer(), nullable=True),
        sa.Column("capacity_per_module_gb", sa.Integer(), nullable=True),
        sa.Column("total_capacity_gb", sa.Integer(), nullable=True),
        sa.Column(
            "attributes_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "ddr_generation",
            "speed_mhz",
            "module_count",
            "capacity_per_module_gb",
            "total_capacity_gb",
            name="uq_ram_spec_dimensions",
        ),
    )

    op.create_table(
        "storage_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(length=128), nullable=True),
        sa.Column(
            "medium",
            storage_medium_enum,
            nullable=False,
            server_default=StorageMedium.UNKNOWN.value,
        ),
        sa.Column("interface", sa.String(length=64), nullable=True),
        sa.Column("form_factor", sa.String(length=64), nullable=True),
        sa.Column("capacity_gb", sa.Integer(), nullable=True),
        sa.Column("performance_tier", sa.String(length=64), nullable=True),
        sa.Column(
            "attributes_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "medium",
            "interface",
            "form_factor",
            "capacity_gb",
            "performance_tier",
            name="uq_storage_profile_dimensions",
        ),
    )

    op.add_column("listing", sa.Column("ram_spec_id", sa.Integer(), nullable=True))
    op.add_column("listing", sa.Column("primary_storage_profile_id", sa.Integer(), nullable=True))
    op.add_column("listing", sa.Column("secondary_storage_profile_id", sa.Integer(), nullable=True))

    op.create_index("ix_listing_ram_spec_id", "listing", ["ram_spec_id"])
    op.create_index("ix_listing_primary_storage_profile_id", "listing", ["primary_storage_profile_id"])
    op.create_index("ix_listing_secondary_storage_profile_id", "listing", ["secondary_storage_profile_id"])

    op.create_foreign_key(
        "fk_listing_ram_spec_id",
        "listing",
        "ram_spec",
        ["ram_spec_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_listing_primary_storage_profile_id",
        "listing",
        "storage_profile",
        ["primary_storage_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_listing_secondary_storage_profile_id",
        "listing",
        "storage_profile",
        ["secondary_storage_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )

    _backfill_components(bind)

    op.alter_column("ram_spec", "ddr_generation", server_default=None)
    op.alter_column("ram_spec", "attributes_json", server_default=None)
    op.alter_column("storage_profile", "medium", server_default=None)
    op.alter_column("storage_profile", "attributes_json", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_constraint("fk_listing_secondary_storage_profile_id", "listing", type_="foreignkey")
    op.drop_constraint("fk_listing_primary_storage_profile_id", "listing", type_="foreignkey")
    op.drop_constraint("fk_listing_ram_spec_id", "listing", type_="foreignkey")
    op.drop_index("ix_listing_secondary_storage_profile_id", table_name="listing")
    op.drop_index("ix_listing_primary_storage_profile_id", table_name="listing")
    op.drop_index("ix_listing_ram_spec_id", table_name="listing")
    op.drop_column("listing", "secondary_storage_profile_id")
    op.drop_column("listing", "primary_storage_profile_id")
    op.drop_column("listing", "ram_spec_id")

    op.drop_table("storage_profile")
    op.drop_table("ram_spec")

    storage_medium_enum = sa.Enum(StorageMedium, name="storage_medium")
    ram_generation_enum = sa.Enum(RamGeneration, name="ram_generation")
    storage_medium_enum.drop(bind, checkfirst=True)
    ram_generation_enum.drop(bind, checkfirst=True)


def _backfill_components(bind: Any) -> None:
    metadata = sa.MetaData()
    metadata.reflect(bind=bind, only=("listing", "ram_spec", "storage_profile"))

    listing_table = metadata.tables["listing"]
    ram_spec_table = metadata.tables["ram_spec"]
    storage_table = metadata.tables["storage_profile"]

    ram_cache: dict[tuple, int] = {}
    storage_cache: dict[tuple, int] = {}

    listings = list(
        bind.execute(
            sa.select(
                listing_table.c.id,
                listing_table.c.ram_gb,
                listing_table.c.ram_notes,
                listing_table.c.primary_storage_gb,
                listing_table.c.primary_storage_type,
                listing_table.c.secondary_storage_gb,
                listing_table.c.secondary_storage_type,
            )
        )
    )

    def get_or_create_ram_spec(total_capacity_gb: int | None) -> int | None:
        if not total_capacity_gb or total_capacity_gb <= 0:
            return None
        key = (RamGeneration.UNKNOWN.value, None, None, None, int(total_capacity_gb))
        if key in ram_cache:
            return ram_cache[key]
        label = f"{int(total_capacity_gb)}GB RAM"
        insert = (
            ram_spec_table.insert()
            .values(
                label=label,
                ddr_generation=RamGeneration.UNKNOWN.value,
                total_capacity_gb=int(total_capacity_gb),
            )
            .returning(ram_spec_table.c.id)
        )
        spec_id = bind.execute(insert).scalar_one()
        ram_cache[key] = spec_id
        return spec_id

    def normalize_medium(value: str | None) -> str:
        if not value:
            return StorageMedium.UNKNOWN.value
        normalized = value.strip().lower()
        if not normalized:
            return StorageMedium.UNKNOWN.value
        if "nvme" in normalized:
            return StorageMedium.NVME.value
        if normalized in {"ssd", "sata ssd", "sata"}:
            return StorageMedium.SATA_SSD.value
        if normalized in {"hdd", "hard drive", "hard disk"}:
            return StorageMedium.HDD.value
        if "hybrid" in normalized:
            return StorageMedium.HYBRID.value
        if "emmc" in normalized:
            return StorageMedium.EMMC.value
        if "ufs" in normalized:
            return StorageMedium.UFS.value
        return StorageMedium.UNKNOWN.value

    def get_or_create_storage_profile(capacity_gb: int | None, storage_type: str | None) -> int | None:
        if not capacity_gb or capacity_gb <= 0:
            return None
        medium_value = normalize_medium(storage_type)
        key = (medium_value, None, None, int(capacity_gb), None)
        if key in storage_cache:
            return storage_cache[key]
        label_parts = [medium_value.replace("_", " ").upper()]
        label_parts.append(f"{int(capacity_gb)}GB")
        label = " · ".join(label_parts)
        insert = (
            storage_table.insert()
            .values(
                label=label,
                medium=medium_value,
                capacity_gb=int(capacity_gb),
            )
            .returning(storage_table.c.id)
        )
        profile_id = bind.execute(insert).scalar_one()
        storage_cache[key] = profile_id
        return profile_id

    for row in listings:
        updates: dict[str, Any] = {}

        ram_spec_id = get_or_create_ram_spec(row.ram_gb)
        if ram_spec_id:
            updates["ram_spec_id"] = ram_spec_id

        primary_profile_id = get_or_create_storage_profile(
            row.primary_storage_gb,
            row.primary_storage_type,
        )
        if primary_profile_id:
            updates["primary_storage_profile_id"] = primary_profile_id

        secondary_profile_id = get_or_create_storage_profile(
            row.secondary_storage_gb,
            row.secondary_storage_type,
        )
        if secondary_profile_id:
            updates["secondary_storage_profile_id"] = secondary_profile_id

        if updates:
            bind.execute(
                listing_table.update()
                .where(listing_table.c.id == row.id)
                .values(**updates)
            )
