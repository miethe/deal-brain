"""Tests for SavedBuild model (Phase 1: Database Layer)."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest


def test_saved_build_model_can_be_imported():
    """Verify SavedBuild model can be imported."""
    from dealbrain_api.models import SavedBuild

    assert SavedBuild is not None
    assert SavedBuild.__tablename__ == "saved_builds"


def test_saved_build_model_has_required_fields():
    """Verify SavedBuild model has all required fields."""
    from dealbrain_api.models import SavedBuild

    # Verify fields exist by checking annotations
    annotations = SavedBuild.__annotations__

    # Required fields
    assert "id" in annotations
    assert "name" in annotations
    assert "visibility" in annotations
    assert "share_token" in annotations

    # Optional metadata
    assert "user_id" in annotations
    assert "description" in annotations
    assert "tags" in annotations

    # Component references
    assert "cpu_id" in annotations
    assert "gpu_id" in annotations
    assert "ram_spec_id" in annotations
    assert "storage_spec_id" in annotations
    assert "psu_spec_id" in annotations
    assert "case_spec_id" in annotations

    # Snapshot fields
    assert "pricing_snapshot" in annotations
    assert "metrics_snapshot" in annotations
    assert "valuation_breakdown" in annotations

    # Soft delete
    assert "deleted_at" in annotations

    # Note: created_at and updated_at come from TimestampMixin and may not appear in annotations
    # but they are still accessible as class attributes


def test_saved_build_model_has_soft_delete_method():
    """Verify SavedBuild model has soft_delete method."""
    from dealbrain_api.models import SavedBuild

    assert hasattr(SavedBuild, "soft_delete")
    assert callable(SavedBuild.soft_delete)


def test_saved_build_model_has_helper_properties():
    """Verify SavedBuild model has helper properties."""
    from dealbrain_api.models import SavedBuild

    # Check that properties exist
    assert hasattr(SavedBuild, "is_deleted")
    assert hasattr(SavedBuild, "is_public")
    assert hasattr(SavedBuild, "is_unlisted")
    assert hasattr(SavedBuild, "share_url")


def test_saved_build_can_be_instantiated():
    """Verify SavedBuild model can be instantiated with basic fields."""
    from dealbrain_api.models import SavedBuild

    # Create instance with minimal required fields
    build = SavedBuild(
        name="Test Build",
        visibility="private",
        share_token=uuid.uuid4().hex
    )

    assert build.name == "Test Build"
    assert build.visibility == "private"
    assert build.share_token is not None
    assert len(build.share_token) == 32  # UUID hex is 32 characters


def test_saved_build_soft_delete():
    """Verify soft_delete method sets deleted_at timestamp."""
    from dealbrain_api.models import SavedBuild

    build = SavedBuild(
        name="Test Build",
        visibility="private",
        share_token=uuid.uuid4().hex
    )

    # Initially not deleted
    assert build.deleted_at is None
    assert not build.is_deleted

    # Soft delete
    build.soft_delete()

    # Now deleted
    assert build.deleted_at is not None
    assert isinstance(build.deleted_at, datetime)
    assert build.is_deleted


def test_saved_build_visibility_properties():
    """Verify visibility helper properties work correctly."""
    from dealbrain_api.models import SavedBuild

    # Test public build
    public_build = SavedBuild(
        name="Public Build",
        visibility="public",
        share_token=uuid.uuid4().hex
    )
    assert public_build.is_public
    assert not public_build.is_unlisted

    # Test unlisted build
    unlisted_build = SavedBuild(
        name="Unlisted Build",
        visibility="unlisted",
        share_token=uuid.uuid4().hex
    )
    assert not unlisted_build.is_public
    assert unlisted_build.is_unlisted

    # Test private build
    private_build = SavedBuild(
        name="Private Build",
        visibility="private",
        share_token=uuid.uuid4().hex
    )
    assert not private_build.is_public
    assert not private_build.is_unlisted


def test_saved_build_share_url():
    """Verify share_url property generates correct URL path."""
    from dealbrain_api.models import SavedBuild

    share_token = uuid.uuid4().hex
    build = SavedBuild(
        name="Test Build",
        visibility="public",
        share_token=share_token
    )

    assert build.share_url == f"/builds/{share_token}"


def test_saved_build_with_optional_fields():
    """Verify SavedBuild can be created with all optional fields."""
    from dealbrain_api.models import SavedBuild

    build = SavedBuild(
        name="Complete Build",
        description="A fully configured gaming PC",
        tags=["gaming", "high-end", "rgb"],
        visibility="public",
        share_token=uuid.uuid4().hex,
        user_id=1,
        cpu_id=1,
        gpu_id=1,
        ram_spec_id=1,
        storage_spec_id=1,
        psu_spec_id=1,
        case_spec_id=1,
        pricing_snapshot={
            "base_price": 1500.0,
            "adjusted_price": 1450.0,
            "delta_amount": -50.0,
            "delta_percentage": -3.33
        },
        metrics_snapshot={
            "dollar_per_cpu_mark_multi": 5.5,
            "dollar_per_cpu_mark_single": 8.2,
            "composite_score": 85.3
        },
        valuation_breakdown={
            "rules_applied": ["RAM_UPGRADE", "GPU_PREMIUM"],
            "total_adjustment": -50.0
        }
    )

    assert build.name == "Complete Build"
    assert build.description == "A fully configured gaming PC"
    assert build.tags == ["gaming", "high-end", "rgb"]
    assert build.user_id == 1
    assert build.cpu_id == 1
    assert build.gpu_id == 1
    assert build.pricing_snapshot is not None
    assert build.pricing_snapshot["base_price"] == 1500.0
    assert build.metrics_snapshot is not None
    assert build.valuation_breakdown is not None


def test_saved_build_model_table_args():
    """Verify SavedBuild model has correct table arguments (indexes, constraints)."""
    from dealbrain_api.models import SavedBuild

    table_args = SavedBuild.__table_args__

    # Should have indexes and constraints
    assert table_args is not None
    assert isinstance(table_args, tuple)

    # Convert to list for easier checking
    table_arg_list = list(table_args)

    # Check that we have Index objects and CheckConstraint
    index_names = []
    check_constraint_names = []

    for arg in table_arg_list:
        if hasattr(arg, "name"):
            if "idx_" in arg.name or "ix_" in arg.name:
                index_names.append(arg.name)
            elif "ck_" in arg.name:
                check_constraint_names.append(arg.name)

    # Verify we have the expected indexes
    assert "idx_user_builds" in index_names
    assert "idx_visibility" in index_names

    # Verify we have the check constraint
    assert "ck_saved_builds_name_not_empty" in check_constraint_names
