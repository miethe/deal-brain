#!/usr/bin/env python3
"""Verification script for Phase 1.2 SQLAlchemy models.

This script tests that all sharing models can be imported and have the expected
attributes, relationships, and helper methods.

Run this after installing dependencies:
    poetry run python scripts/verify_sharing_models.py
"""

import sys


def verify_imports():
    """Verify all models can be imported."""
    print("Testing model imports...")

    try:
        from dealbrain_api.models import (
            User,
            ListingShare,
            UserShare,
            Collection,
            CollectionItem,
            Listing,
        )
        print("✅ All models imported successfully")
        return User, ListingShare, UserShare, Collection, CollectionItem, Listing
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)


def verify_user_model(User):
    """Verify User model structure."""
    print("\nVerifying User model...")

    # Check fields
    expected_fields = ['id', 'username', 'email', 'display_name', 'created_at', 'updated_at']
    for field in expected_fields:
        assert hasattr(User, field), f"Missing field: {field}"

    # Check relationships
    expected_relationships = ['collections', 'created_shares', 'sent_shares', 'received_shares']
    for rel in expected_relationships:
        assert hasattr(User, rel), f"Missing relationship: {rel}"

    print("✅ User model verified")


def verify_listing_share_model(ListingShare):
    """Verify ListingShare model structure."""
    print("\nVerifying ListingShare model...")

    # Check fields
    expected_fields = [
        'id', 'listing_id', 'created_by', 'share_token',
        'view_count', 'created_at', 'expires_at'
    ]
    for field in expected_fields:
        assert hasattr(ListingShare, field), f"Missing field: {field}"

    # Check relationships
    expected_relationships = ['listing', 'creator']
    for rel in expected_relationships:
        assert hasattr(ListingShare, rel), f"Missing relationship: {rel}"

    # Check class methods
    assert hasattr(ListingShare, 'generate_token'), "Missing generate_token() class method"

    # Check instance methods
    expected_methods = ['is_expired', 'increment_view_count']
    for method in expected_methods:
        assert hasattr(ListingShare, method), f"Missing method: {method}"

    # Test token generation
    token = ListingShare.generate_token()
    assert isinstance(token, str), "Token should be a string"
    assert len(token) == 64, f"Token should be 64 characters, got {len(token)}"

    print("✅ ListingShare model verified")


def verify_user_share_model(UserShare):
    """Verify UserShare model structure."""
    print("\nVerifying UserShare model...")

    # Check fields
    expected_fields = [
        'id', 'sender_id', 'recipient_id', 'listing_id', 'share_token',
        'message', 'shared_at', 'expires_at', 'viewed_at', 'imported_at', 'created_at'
    ]
    for field in expected_fields:
        assert hasattr(UserShare, field), f"Missing field: {field}"

    # Check relationships
    expected_relationships = ['sender', 'recipient', 'listing']
    for rel in expected_relationships:
        assert hasattr(UserShare, rel), f"Missing relationship: {rel}"

    # Check class methods
    assert hasattr(UserShare, 'generate_token'), "Missing generate_token() class method"

    # Check instance methods
    expected_methods = ['is_expired', 'is_viewed', 'is_imported', 'mark_viewed', 'mark_imported']
    for method in expected_methods:
        assert hasattr(UserShare, method), f"Missing method: {method}"

    # Test token generation
    token = UserShare.generate_token()
    assert isinstance(token, str), "Token should be a string"
    assert len(token) == 64, f"Token should be 64 characters, got {len(token)}"

    print("✅ UserShare model verified")


def verify_collection_model(Collection):
    """Verify Collection model structure."""
    print("\nVerifying Collection model...")

    # Check fields
    expected_fields = [
        'id', 'user_id', 'name', 'description', 'visibility',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        assert hasattr(Collection, field), f"Missing field: {field}"

    # Check relationships
    expected_relationships = ['user', 'items']
    for rel in expected_relationships:
        assert hasattr(Collection, rel), f"Missing relationship: {rel}"

    # Check instance methods/properties
    expected_methods = ['item_count', 'has_item']
    for method in expected_methods:
        assert hasattr(Collection, method), f"Missing method/property: {method}"

    print("✅ Collection model verified")


def verify_collection_item_model(CollectionItem):
    """Verify CollectionItem model structure."""
    print("\nVerifying CollectionItem model...")

    # Check fields
    expected_fields = [
        'id', 'collection_id', 'listing_id', 'status', 'notes',
        'position', 'added_at', 'created_at', 'updated_at'
    ]
    for field in expected_fields:
        assert hasattr(CollectionItem, field), f"Missing field: {field}"

    # Check relationships
    expected_relationships = ['collection', 'listing']
    for rel in expected_relationships:
        assert hasattr(CollectionItem, rel), f"Missing relationship: {rel}"

    print("✅ CollectionItem model verified")


def verify_listing_relationships(Listing):
    """Verify Listing model has new relationships."""
    print("\nVerifying Listing model relationships...")

    # Check new relationships
    expected_relationships = ['shares', 'user_shares', 'collection_items']
    for rel in expected_relationships:
        assert hasattr(Listing, rel), f"Missing relationship on Listing: {rel}"

    print("✅ Listing relationships verified")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Phase 1.2 SQLAlchemy Models Verification")
    print("=" * 60)

    # Import all models
    User, ListingShare, UserShare, Collection, CollectionItem, Listing = verify_imports()

    # Verify each model
    verify_user_model(User)
    verify_listing_share_model(ListingShare)
    verify_user_share_model(UserShare)
    verify_collection_model(Collection)
    verify_collection_item_model(CollectionItem)
    verify_listing_relationships(Listing)

    print("\n" + "=" * 60)
    print("✅ All verification tests passed!")
    print("=" * 60)
    print("\nPhase 1.2 SQLAlchemy Models: COMPLETE")
    print("Ready to proceed to Phase 1.3: Repository Layer")


if __name__ == "__main__":
    main()
