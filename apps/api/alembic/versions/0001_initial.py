"""Initial schema for Deal Brain"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from dealbrain_core.enums import ComponentMetric, ComponentType, Condition, ListingStatus, PortType

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    component_type = sa.Enum(ComponentType, name="component_type")
    component_metric = sa.Enum(ComponentMetric, name="component_metric")
    condition = sa.Enum('new', 'refurb', 'used', name="condition")
    listing_status = sa.Enum('active', 'archived', 'pending', name="listing_status")
    port_type = sa.Enum(PortType, name="port_type")

    op.create_table(
        "cpu",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("manufacturer", sa.String(length=64), nullable=False),
        sa.Column("socket", sa.String(length=64)),
        sa.Column("cores", sa.Integer()),
        sa.Column("threads", sa.Integer()),
        sa.Column("tdp_w", sa.Integer()),
        sa.Column("igpu_model", sa.String(length=255)),
        sa.Column("cpu_mark_multi", sa.Integer()),
        sa.Column("cpu_mark_single", sa.Integer()),
        sa.Column("release_year", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "gpu",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("manufacturer", sa.String(length=64), nullable=False),
        sa.Column("gpu_mark", sa.Integer()),
        sa.Column("metal_score", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ports_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("weights_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "valuation_rule",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("component_type", component_type, nullable=False),
        sa.Column("metric", component_metric, nullable=False),
        sa.Column("unit_value_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("condition_new", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("condition_refurb", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("condition_used", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("age_curve_json", sa.JSON()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "import_job",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer()),
        sa.Column("processed_rows", sa.Integer()),
        sa.Column("error", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "task_run",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("payload", sa.JSON()),
        sa.Column("result", sa.JSON()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "port",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ports_profile_id", sa.Integer(), sa.ForeignKey("ports_profile.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", port_type, nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("spec_notes", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ports_profile_id", "type", "spec_notes", name="uq_port_profile_type"),
    )

    op.create_table(
        "listing",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text()),
        sa.Column("seller", sa.String(length=128)),
        sa.Column("price_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_date", sa.DateTime()),
        sa.Column("condition", condition, nullable=False, server_default=sa.text(f"'{Condition.USED.value}'")),
        sa.Column("status", listing_status, nullable=False, server_default=sa.text(f"'{ListingStatus.ACTIVE.value}'")),
        sa.Column("cpu_id", sa.Integer(), sa.ForeignKey("cpu.id")),
        sa.Column("gpu_id", sa.Integer(), sa.ForeignKey("gpu.id")),
        sa.Column("ports_profile_id", sa.Integer(), sa.ForeignKey("ports_profile.id")),
        sa.Column("device_model", sa.String(length=255)),
        sa.Column("ram_gb", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ram_notes", sa.Text()),
        sa.Column("primary_storage_gb", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_storage_type", sa.String(length=64)),
        sa.Column("secondary_storage_gb", sa.Integer()),
        sa.Column("secondary_storage_type", sa.String(length=64)),
        sa.Column("os_license", sa.String(length=64)),
        sa.Column("other_components", sa.JSON(), server_default=sa.text("'[]'::json")),
        sa.Column("notes", sa.Text()),
        sa.Column("raw_listing_json", sa.JSON()),
        sa.Column("adjusted_price_usd", sa.Numeric(10, 2)),
        sa.Column("valuation_breakdown", sa.JSON()),
        sa.Column("score_cpu_multi", sa.Float()),
        sa.Column("score_cpu_single", sa.Float()),
        sa.Column("score_gpu", sa.Float()),
        sa.Column("score_composite", sa.Float()),
        sa.Column("dollar_per_cpu_mark", sa.Float()),
        sa.Column("dollar_per_single_mark", sa.Float()),
        sa.Column("perf_per_watt", sa.Float()),
        sa.Column("active_profile_id", sa.Integer(), sa.ForeignKey("profile.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "listing_component",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listing.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("valuation_rule.id")),
        sa.Column("component_type", sa.Enum(ComponentType), nullable=False),
        sa.Column("name", sa.String(length=255)),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("adjustment_value_usd", sa.Numeric(10, 2)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "listing_score_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listing.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("profile.id")),
        sa.Column("score_composite", sa.Float()),
        sa.Column("adjusted_price_usd", sa.Numeric(10, 2)),
        sa.Column("dollar_per_cpu_mark", sa.Float()),
        sa.Column("dollar_per_single_mark", sa.Float()),
        sa.Column("perf_per_watt", sa.Float()),
        sa.Column("explain_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("listing_score_snapshot")
    op.drop_table("listing_component")
    op.drop_table("listing")
    op.drop_table("port")
    op.drop_table("task_run")
    op.drop_table("import_job")
    op.drop_table("valuation_rule")
    op.drop_table("profile")
    op.drop_table("ports_profile")
    op.drop_table("gpu")
    op.drop_table("cpu")
