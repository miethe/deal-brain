"""Tests for Phase 2a collection sharing migration (0030).

This test suite verifies:
1. CollectionShareToken model structure and methods
2. Collection model relationship with share tokens
3. Model validation and constraints
"""

import pytest
from datetime import datetime, timedelta

from dealbrain_api.models.sharing import Collection, CollectionShareToken, User


class TestCollectionShareTokenModel:
    """Test CollectionShareToken model structure and methods."""

    def test_collection_share_token_structure(self):
        """Verify CollectionShareToken has all required fields."""
        # Check model attributes exist
        assert hasattr(CollectionShareToken, 'id')
        assert hasattr(CollectionShareToken, 'collection_id')
        assert hasattr(CollectionShareToken, 'token')
        assert hasattr(CollectionShareToken, 'view_count')
        assert hasattr(CollectionShareToken, 'expires_at')
        assert hasattr(CollectionShareToken, 'created_at')
        assert hasattr(CollectionShareToken, 'updated_at')

    def test_collection_share_token_relationships(self):
        """Verify CollectionShareToken has proper relationships."""
        assert hasattr(CollectionShareToken, 'collection')

    def test_generate_token_method(self):
        """Verify token generation produces valid URL-safe tokens."""
        token1 = CollectionShareToken.generate_token()
        token2 = CollectionShareToken.generate_token()

        # Tokens should be 64 characters
        assert len(token1) == 64
        assert len(token2) == 64

        # Tokens should be unique
        assert token1 != token2

        # Tokens should be URL-safe (alphanumeric, -, _)
        assert token1.replace('-', '').replace('_', '').isalnum()
        assert token2.replace('-', '').replace('_', '').isalnum()

    def test_is_expired_method_no_expiry(self):
        """Verify is_expired returns False when expires_at is None."""
        token = CollectionShareToken()
        token.expires_at = None

        assert token.is_expired() is False

    def test_is_expired_method_future_expiry(self):
        """Verify is_expired returns False when expires_at is in the future."""
        token = CollectionShareToken()
        token.expires_at = datetime.utcnow() + timedelta(days=30)

        assert token.is_expired() is False

    def test_is_expired_method_past_expiry(self):
        """Verify is_expired returns True when expires_at is in the past."""
        token = CollectionShareToken()
        token.expires_at = datetime.utcnow() - timedelta(days=1)

        assert token.is_expired() is True

    def test_repr_method(self):
        """Verify __repr__ provides useful debug information."""
        token = CollectionShareToken()
        token.id = 1
        token.collection_id = 5
        token.token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab5678cdef9012"
        token.view_count = 42
        token.expires_at = None

        repr_str = repr(token)

        assert "CollectionShareToken" in repr_str
        assert "id=1" in repr_str
        assert "collection_id=5" in repr_str
        assert "abcd1234" in repr_str  # First 8 chars of token
        assert "views=42" in repr_str
        assert "active" in repr_str


class TestCollectionModelEnhancements:
    """Test Collection model enhancements for Phase 2a."""

    def test_collection_has_share_tokens_relationship(self):
        """Verify Collection model has share_tokens relationship."""
        assert hasattr(Collection, 'share_tokens')

    def test_collection_visibility_field(self):
        """Verify Collection model has visibility field."""
        assert hasattr(Collection, 'visibility')


class TestMigrationIndexes:
    """Test that migration indexes are properly defined.

    These tests verify the migration file contains the correct index definitions.
    Actual index creation is tested via integration tests with a real database.
    """

    def test_migration_file_exists(self):
        """Verify migration file 0030 exists."""
        import os
        migration_path = "apps/api/alembic/versions/0030_add_collection_sharing_enhancements.py"
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"

    def test_migration_content(self):
        """Verify migration file contains expected operations."""
        import os
        migration_path = "apps/api/alembic/versions/0030_add_collection_sharing_enhancements.py"

        with open(migration_path, 'r') as f:
            content = f.read()

        # Verify revision metadata
        assert "revision: str = '0030'" in content
        assert "down_revision: Union[str, Sequence[str], None] = '5dc4b78ba7c1'" in content

        # Verify collection indexes
        assert "idx_collection_user_visibility" in content
        assert "idx_collection_visibility_created" in content
        assert "idx_collection_visibility_updated" in content

        # Verify collection_share_token table creation
        assert "create_table" in content
        assert "collection_share_token" in content

        # Verify collection_share_token indexes
        assert "ix_collection_share_token_id" in content
        assert "ix_collection_share_token_token" in content
        assert "idx_collection_share_token_collection" in content
        assert "idx_collection_share_token_expires" in content

        # Verify foreign key constraint
        assert "fk_collection_share_token_collection_id" in content

        # Verify downgrade function
        assert "def downgrade()" in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
