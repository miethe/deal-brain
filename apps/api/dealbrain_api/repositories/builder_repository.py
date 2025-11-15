"""Repository for SavedBuild CRUD operations.

This module provides the data access layer for saved PC build configurations.
Implements query optimization with eager loading and access control for private builds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.builds import SavedBuild


class BuilderRepository:
    """Repository for SavedBuild CRUD operations.

    Handles all database operations for saved builds with:
    - Soft delete filtering (excludes deleted builds by default)
    - Query optimization (eager loading CPU/GPU relationships)
    - Access control (validates ownership for private builds)
    - Performance target: <100ms for typical queries

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def create(self, data: dict) -> SavedBuild:
        """Create a new saved build.

        Args:
            data: Dictionary containing build data with the following keys:
                - user_id (int | None): Owner user ID
                - name (str): Build name (required)
                - description (str | None): Build description
                - tags (list[str] | None): Tags for categorization
                - visibility (str): 'private', 'public', or 'unlisted'
                - share_token (str): UUID hex string (32 chars)
                - cpu_id (int | None): CPU component ID
                - gpu_id (int | None): GPU component ID
                - ram_spec_id (int | None): RAM specification ID
                - storage_spec_id (int | None): Storage specification ID
                - psu_spec_id (int | None): PSU specification ID
                - case_spec_id (int | None): Case specification ID
                - pricing_snapshot (dict | None): Pricing data snapshot
                - metrics_snapshot (dict | None): Performance metrics snapshot
                - valuation_breakdown (dict | None): Valuation breakdown data

        Returns:
            SavedBuild: Created build instance with ID and timestamps

        Raises:
            ValueError: If required fields are missing (name, visibility, share_token)
        """
        # Validate required fields
        required_fields = ["name", "visibility", "share_token"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Create SavedBuild instance
        build = SavedBuild(**data)

        # Add to session and flush to get ID
        self.session.add(build)
        await self.session.flush()

        # Refresh to get created_at and updated_at from database
        await self.session.refresh(build)

        return build

    async def get_by_id(
        self,
        build_id: int,
        user_id: Optional[int] = None
    ) -> Optional[SavedBuild]:
        """Get single build by ID with optional access control.

        Access control rules:
        - Public builds: accessible to anyone
        - Unlisted builds: accessible to anyone
        - Private builds: only accessible to owner (requires user_id match)

        Args:
            build_id: Build ID to retrieve
            user_id: Optional user ID for access control validation

        Returns:
            SavedBuild instance if found and accessible, None otherwise
        """
        # Build query with eager loading
        stmt = (
            select(SavedBuild)
            .options(
                joinedload(SavedBuild.cpu),
                joinedload(SavedBuild.gpu)
            )
            .where(
                and_(
                    SavedBuild.id == build_id,
                    SavedBuild.deleted_at.is_(None)  # Only active builds
                )
            )
        )

        result = await self.session.execute(stmt)
        build = result.unique().scalar_one_or_none()

        if not build:
            return None

        # Apply access control for private builds
        if build.visibility == "private" and (user_id is None or build.user_id != user_id):
            return None  # Access denied

        return build

    async def get_by_share_token(self, share_token: str) -> Optional[SavedBuild]:
        """Get build by share token for shared URLs.

        Only returns public or unlisted builds. Private builds are not accessible
        via share token without authentication.

        Args:
            share_token: Unique share token (32-char UUID hex)

        Returns:
            SavedBuild instance if found and shareable, None otherwise
        """
        stmt = (
            select(SavedBuild)
            .options(
                joinedload(SavedBuild.cpu),
                joinedload(SavedBuild.gpu)
            )
            .where(
                and_(
                    SavedBuild.share_token == share_token,
                    SavedBuild.deleted_at.is_(None),  # Only active builds
                    SavedBuild.visibility.in_(["public", "unlisted"])  # Only shareable builds
                )
            )
        )

        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> list[SavedBuild]:
        """List user's builds with pagination.

        Returns builds ordered by creation date (newest first).
        Uses eager loading to prevent N+1 query problems.

        Args:
            user_id: Owner user ID
            limit: Maximum number of builds to return (default: 10)
            offset: Number of builds to skip for pagination (default: 0)

        Returns:
            List of SavedBuild instances owned by user
        """
        stmt = (
            select(SavedBuild)
            .options(
                joinedload(SavedBuild.cpu),
                joinedload(SavedBuild.gpu)
            )
            .where(
                and_(
                    SavedBuild.user_id == user_id,
                    SavedBuild.deleted_at.is_(None)  # Only active builds
                )
            )
            .order_by(SavedBuild.created_at.desc())  # Newest first
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def update(self, build_id: int, data: dict, user_id: int) -> SavedBuild:
        """Update existing build.

        Validates ownership before allowing updates. Only the build owner can update.
        Protected fields (id, user_id, share_token, created_at, deleted_at) are ignored.

        Allowed update fields:
        - name, description, tags
        - visibility
        - Component IDs (cpu_id, gpu_id, ram_spec_id, storage_spec_id, psu_spec_id, case_spec_id)
        - Snapshots (pricing_snapshot, metrics_snapshot, valuation_breakdown)

        Args:
            build_id: Build ID to update
            data: Dictionary with fields to update
            user_id: User ID for ownership validation

        Returns:
            Updated SavedBuild instance

        Raises:
            ValueError: If build not found or access denied
        """
        # Get build with ownership check
        build = await self.get_by_id(build_id, user_id)

        if not build:
            raise ValueError(f"Build {build_id} not found or access denied")

        # Verify ownership explicitly for private builds
        if build.user_id != user_id:
            raise ValueError(f"Access denied to build {build_id}")

        # Define allowed update fields
        allowed_fields = {
            "name", "description", "tags", "visibility",
            "cpu_id", "gpu_id", "ram_spec_id", "storage_spec_id",
            "psu_spec_id", "case_spec_id",
            "pricing_snapshot", "metrics_snapshot", "valuation_breakdown"
        }

        # Update only allowed fields
        for key, value in data.items():
            if key in allowed_fields:
                setattr(build, key, value)

        # Update timestamp
        build.updated_at = datetime.now(timezone.utc)

        # Flush changes to database
        await self.session.flush()

        return build

    async def soft_delete(self, build_id: int, user_id: int) -> bool:
        """Soft delete a build (set deleted_at timestamp).

        Does not physically remove the build from database. Sets deleted_at timestamp
        to maintain audit trail and allow potential recovery.

        Args:
            build_id: Build ID to delete
            user_id: User ID for ownership validation

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If build not found or access denied
        """
        # Get build with ownership check
        build = await self.get_by_id(build_id, user_id)

        if not build:
            raise ValueError(f"Build {build_id} not found or access denied")

        # Verify ownership explicitly
        if build.user_id != user_id:
            raise ValueError(f"Access denied to build {build_id}")

        # Call model's soft_delete method
        build.soft_delete()

        # Flush changes to database
        await self.session.flush()

        return True
