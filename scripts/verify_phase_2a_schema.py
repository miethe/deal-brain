#!/usr/bin/env python3
"""Verification script for Phase 2a database schema implementation.

This script verifies that all Phase 2a schema changes are correctly implemented:
1. CollectionShareToken model structure
2. Collection model relationships
3. Migration file integrity
4. Model export configuration

Run this script after applying the migration to verify the implementation.
"""

import sys
from pathlib import Path

# Add apps/api to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))


def verify_model_structure():
    """Verify CollectionShareToken model has all required attributes."""
    from dealbrain_api.models.sharing import CollectionShareToken

    print("🔍 Verifying CollectionShareToken model structure...")

    required_attrs = [
        'id', 'collection_id', 'token', 'view_count',
        'expires_at', 'created_at', 'updated_at'
    ]

    for attr in required_attrs:
        assert hasattr(CollectionShareToken, attr), f"Missing attribute: {attr}"

    print(f"  ✅ All {len(required_attrs)} required attributes present")


def verify_model_methods():
    """Verify CollectionShareToken has all required methods."""
    from dealbrain_api.models.sharing import CollectionShareToken

    print("🔍 Verifying CollectionShareToken methods...")

    required_methods = ['generate_token', 'is_expired', 'increment_view_count']

    for method in required_methods:
        assert hasattr(CollectionShareToken, method), f"Missing method: {method}"

    print(f"  ✅ All {len(required_methods)} required methods present")


def verify_relationships():
    """Verify bidirectional relationship between Collection and CollectionShareToken."""
    from dealbrain_api.models.sharing import Collection, CollectionShareToken

    print("🔍 Verifying model relationships...")

    assert hasattr(CollectionShareToken, 'collection'), "Missing collection relationship"
    assert hasattr(Collection, 'share_tokens'), "Missing share_tokens relationship"

    print("  ✅ Bidirectional relationship configured correctly")


def verify_token_generation():
    """Verify token generation produces valid tokens."""
    from dealbrain_api.models.sharing import CollectionShareToken

    print("🔍 Verifying token generation...")

    # Generate multiple tokens
    tokens = [CollectionShareToken.generate_token() for _ in range(10)]

    # Check length
    for token in tokens:
        assert len(token) == 64, f"Invalid token length: {len(token)}"

    # Check uniqueness
    assert len(set(tokens)) == len(tokens), "Tokens are not unique"

    # Check URL-safe characters
    for token in tokens:
        assert all(c.isalnum() or c in '-_' for c in token), f"Invalid characters in token: {token}"

    print(f"  ✅ Generated {len(tokens)} unique 64-character URL-safe tokens")


def verify_migration_file():
    """Verify migration file structure and content."""
    print("🔍 Verifying migration file...")

    migration_path = Path(__file__).parent.parent / "apps" / "api" / "alembic" / "versions" / "0030_add_collection_sharing_enhancements.py"

    assert migration_path.exists(), f"Migration file not found: {migration_path}"

    with open(migration_path, 'r') as f:
        content = f.read()

    # Check revision metadata
    assert "revision: str = '0030'" in content, "Invalid revision ID"
    assert "down_revision: Union[str, Sequence[str], None] = '5dc4b78ba7c1'" in content, "Invalid parent revision"

    # Check index creation
    required_indexes = [
        'idx_collection_user_visibility',
        'idx_collection_visibility_created',
        'idx_collection_visibility_updated',
        'ix_collection_share_token_id',
        'ix_collection_share_token_token',
        'idx_collection_share_token_collection',
        'idx_collection_share_token_expires',
    ]

    for index in required_indexes:
        assert index in content, f"Missing index: {index}"

    # Check table creation
    assert 'collection_share_token' in content, "Missing table creation"
    assert 'create_table' in content, "Missing create_table operation"

    # Check constraints
    assert 'fk_collection_share_token_collection_id' in content, "Missing foreign key constraint"
    assert 'CASCADE' in content, "Missing CASCADE delete"

    print(f"  ✅ Migration file structure valid ({len(required_indexes)} indexes defined)")


def verify_model_exports():
    """Verify CollectionShareToken is exported from models.core."""
    from dealbrain_api.models import core

    print("🔍 Verifying model exports...")

    assert hasattr(core, 'CollectionShareToken'), "CollectionShareToken not exported from models.core"
    assert 'CollectionShareToken' in core.__all__, "CollectionShareToken not in __all__"

    print("  ✅ CollectionShareToken properly exported")


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Phase 2a Database Schema Verification")
    print("=" * 70)
    print()

    checks = [
        ("Model Structure", verify_model_structure),
        ("Model Methods", verify_model_methods),
        ("Relationships", verify_relationships),
        ("Token Generation", verify_token_generation),
        ("Migration File", verify_migration_file),
        ("Model Exports", verify_model_exports),
    ]

    passed = 0
    failed = 0

    for check_name, check_func in checks:
        try:
            check_func()
            passed += 1
        except Exception as e:
            print(f"  ❌ {check_name} failed: {e}")
            failed += 1

    print()
    print("=" * 70)
    print(f"Verification Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print()
        print("🎉 All Phase 2a schema changes verified successfully!")
        print()
        print("Next steps:")
        print("  1. Apply migration: make migrate")
        print("  2. Verify in database: psql -d dealbrain -c '\\d collection_share_token'")
        print("  3. Test rollback: poetry run alembic downgrade -1")
        print()
        return 0
    else:
        print()
        print("⚠️  Some verification checks failed. Please review the errors above.")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
