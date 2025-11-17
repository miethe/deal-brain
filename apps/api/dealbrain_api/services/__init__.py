"""Service layer for business logic.

This module provides high-level business logic services that orchestrate
repository operations and enforce business rules.

Services:
- SharingService: Deal sharing with tokens, validation, rate limiting
- CollectionsService: Collection CRUD and item management
- IntegrationService: Share-to-collection integration workflows
"""

from .collections_service import CollectionsService
from .integration_service import IntegrationService
from .sharing_service import SharingService

__all__ = [
    "SharingService",
    "CollectionsService",
    "IntegrationService",
]
