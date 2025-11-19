"""Service layer for Deal Builder business logic.

This module provides the business logic layer for the Deal Builder feature,
orchestrating valuation, performance metrics calculation, and build persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from dealbrain_core.scoring import dollar_per_metric

from ..models.builds import SavedBuild
from ..models.catalog import Cpu, Gpu
from ..models.listings import Listing
from ..repositories.builder_repository import BuilderRepository
from ..telemetry import get_logger

logger = get_logger("dealbrain.builder.service")

# Price estimation constants per benchmark point
CPU_PRICE_PER_MARK = Decimal("0.10")
GPU_PRICE_PER_MARK = Decimal("0.15")


class BuilderService:
    """Service layer for Deal Builder business logic.

    Orchestrates:
    - Build valuation using existing domain logic
    - Performance metrics calculation
    - Build persistence with pricing/metrics snapshots
    - Build retrieval with access control
    - Build comparison with similar listings

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.repository = BuilderRepository(session)

    async def calculate_build_valuation(
        self, components: Dict[str, Optional[int]]
    ) -> Dict[str, Any]:
        """Calculate pricing and valuation for a custom build.

        Validates component IDs, fetches component data from database,
        calculates base price, and applies valuation rules using existing
        domain logic from packages/core.

        Args:
            components: Dictionary of component IDs:
                - cpu_id (int): Required
                - gpu_id (int | None): Optional
                - ram_spec_id (int | None): Optional
                - storage_spec_id (int | None): Optional
                - psu_spec_id (int | None): Optional
                - case_spec_id (int | None): Optional

        Returns:
            Dictionary with valuation data:
                - base_price (Decimal): Sum of component prices
                - adjusted_price (Decimal): Price after valuation adjustments
                - delta_amount (Decimal): Absolute price difference
                - delta_percentage (Decimal): Percentage difference
                - breakdown (dict): Detailed component and adjustment breakdown

        Raises:
            ValueError: If cpu_id is missing or any component ID is invalid

        Performance:
            Target: <300ms total execution time
        """
        # Validate CPU required
        cpu_id = components.get("cpu_id")
        if not cpu_id:
            raise ValueError("CPU is required for build valuation")

        # Fetch CPU (required component)
        cpu = await self.session.get(Cpu, cpu_id)
        if not cpu:
            raise ValueError(f"Invalid CPU ID: {cpu_id}")

        # Fetch GPU (optional component)
        gpu = None
        gpu_id = components.get("gpu_id")
        if gpu_id:
            gpu = await self.session.get(Gpu, gpu_id)
            if not gpu:
                raise ValueError(f"Invalid GPU ID: {gpu_id}")

        # Calculate base price (sum of component prices)
        # For Phase 3, we'll use a simplified pricing model
        # In Phase 4, this will be enhanced with actual component pricing data
        base_price = Decimal("0.00")
        component_breakdown = []

        # CPU price estimation (from PassMark data if available)
        cpu_price = Decimal("0.00")
        if cpu.cpu_mark_multi and cpu.cpu_mark_multi > 0:
            # Rough estimation using CPU_PRICE_PER_MARK per PassMark point
            cpu_price = Decimal(str(cpu.cpu_mark_multi)) * CPU_PRICE_PER_MARK
        component_breakdown.append(
            {
                "type": "CPU",
                "name": cpu.name,
                "price": float(cpu_price),
            }
        )
        base_price += cpu_price

        # GPU price estimation (if present)
        if gpu:
            gpu_price = Decimal("0.00")
            if gpu.gpu_mark and gpu.gpu_mark > 0:
                # Rough estimation using GPU_PRICE_PER_MARK per GPU Mark point
                gpu_price = Decimal(str(gpu.gpu_mark)) * GPU_PRICE_PER_MARK
            component_breakdown.append(
                {
                    "type": "GPU",
                    "name": gpu.name,
                    "price": float(gpu_price),
                }
            )
            base_price += gpu_price

        # For Phase 3, we'll use a simple valuation model
        # In Phase 4, this will integrate with the full valuation rules system
        # For now, adjusted_price = base_price (no adjustments)
        adjusted_price = base_price
        delta_amount = adjusted_price - base_price
        delta_percentage = Decimal("0.00")
        if base_price > 0:
            delta_percentage = (delta_amount / base_price) * Decimal("100")

        # Generate valuation breakdown
        breakdown = {
            "components": component_breakdown,
            "adjustments": [],  # No adjustments in Phase 3 simplified model
        }

        logger.info(
            "build.valuation.calculated",
            cpu_id=cpu_id,
            gpu_id=gpu_id,
            base_price=float(base_price),
            adjusted_price=float(adjusted_price),
        )

        return {
            "base_price": base_price,
            "adjusted_price": adjusted_price,
            "delta_amount": delta_amount,
            "delta_percentage": float(delta_percentage),
            "breakdown": breakdown,
        }

    async def calculate_build_metrics(self, cpu_id: int, adjusted_price: Decimal) -> Dict[str, Any]:
        """Calculate performance metrics for a build.

        Fetches CPU benchmark data and calculates price-per-performance metrics
        using existing domain logic from packages/core.

        Args:
            cpu_id: ID of selected CPU
            adjusted_price: Calculated adjusted price from valuation

        Returns:
            Dictionary with performance metrics:
                - dollar_per_cpu_mark_multi (Decimal | None): $/CPU Mark (multi-thread)
                - dollar_per_cpu_mark_single (Decimal | None): $/CPU Mark (single-thread)
                - composite_score (int | None): Composite score (0-100 scale)
                - cpu_mark_multi (int | None): CPU multi-thread benchmark
                - cpu_mark_single (int | None): CPU single-thread benchmark

        Raises:
            ValueError: If CPU not found

        Notes:
            If CPU lacks benchmark data, returns metrics as None
        """
        # Fetch CPU benchmark data
        cpu = await self.session.get(Cpu, cpu_id)
        if not cpu:
            raise ValueError(f"Invalid CPU ID: {cpu_id}")

        # Calculate $/CPU Mark metrics
        cpu_mark_multi = cpu.cpu_mark_multi
        cpu_mark_single = cpu.cpu_mark_single

        # Use existing domain logic for dollar_per_metric calculation
        price_float = float(adjusted_price)
        dollar_per_cpu_mark_multi = None
        dollar_per_cpu_mark_single = None

        if cpu_mark_multi and cpu_mark_multi > 0:
            dollar_per_cpu_mark_multi = dollar_per_metric(price_float, float(cpu_mark_multi))

        if cpu_mark_single and cpu_mark_single > 0:
            dollar_per_cpu_mark_single = dollar_per_metric(price_float, float(cpu_mark_single))

        # Composite score calculation (simplified for Phase 3)
        # In Phase 4, this will use the full scoring profile system
        composite_score = None
        if dollar_per_cpu_mark_multi is not None:
            # Lower $/Mark is better, scale to 0-100
            # Assuming $0.50/Mark = 50, $0.25/Mark = 75, $0.10/Mark = 90
            if dollar_per_cpu_mark_multi <= 0.10:
                composite_score = 90
            elif dollar_per_cpu_mark_multi <= 0.25:
                composite_score = 75
            elif dollar_per_cpu_mark_multi <= 0.50:
                composite_score = 50
            else:
                composite_score = 25

        logger.info(
            "build.metrics.calculated",
            cpu_id=cpu_id,
            adjusted_price=float(adjusted_price),
            dollar_per_cpu_mark_multi=dollar_per_cpu_mark_multi,
            composite_score=composite_score,
        )

        return {
            "dollar_per_cpu_mark_multi": (
                Decimal(str(dollar_per_cpu_mark_multi))
                if dollar_per_cpu_mark_multi is not None
                else None
            ),
            "dollar_per_cpu_mark_single": (
                Decimal(str(dollar_per_cpu_mark_single))
                if dollar_per_cpu_mark_single is not None
                else None
            ),
            "composite_score": composite_score,
            "cpu_mark_multi": cpu_mark_multi,
            "cpu_mark_single": cpu_mark_single,
        }

    async def save_build(
        self, request: Dict[str, Any], user_id: Optional[int] = None
    ) -> SavedBuild:
        """Save a build with pricing/metrics snapshot.

        Validates input, calculates current valuation and metrics,
        generates snapshots, and persists to database.

        Args:
            request: Build save request:
                - name (str): Required, non-empty
                - description (str | None): Optional description
                - tags (List[str] | None): Optional tags
                - visibility (str): 'private', 'public', or 'unlisted'
                - components (dict): Component IDs (cpu_id required)
            user_id: Optional user ID for ownership

        Returns:
            Saved build instance with ID and timestamps

        Raises:
            ValueError: If validation fails (name required, invalid visibility, etc.)

        Performance:
            Target: <500ms total execution time
        """
        # Validate input
        name = request.get("name")
        if not name or not name.strip():
            raise ValueError("Build name is required and cannot be empty")

        visibility = request.get("visibility", "private")
        if visibility not in ["private", "public", "unlisted"]:
            raise ValueError(
                f"Invalid visibility: {visibility}. " "Must be 'private', 'public', or 'unlisted'"
            )

        components = request.get("components", {})
        if not components.get("cpu_id"):
            raise ValueError("CPU is required in components")

        # Calculate current valuation
        valuation = await self.calculate_build_valuation(components)
        base_price = valuation["base_price"]
        adjusted_price = valuation["adjusted_price"]
        delta_amount = valuation["delta_amount"]
        delta_percentage = valuation["delta_percentage"]
        breakdown = valuation["breakdown"]

        # Calculate current metrics
        cpu_id = components["cpu_id"]
        metrics = await self.calculate_build_metrics(cpu_id, adjusted_price)

        # Generate share_token
        share_token = uuid.uuid4().hex

        # Create snapshots
        pricing_snapshot = {
            "base_price": str(base_price),
            "adjusted_price": str(adjusted_price),
            "delta_amount": str(delta_amount),
            "delta_percentage": float(delta_percentage),
            "breakdown": breakdown,
            "calculated_at": datetime.utcnow().isoformat(),
        }

        metrics_snapshot = {
            "dollar_per_cpu_mark_multi": (
                str(metrics["dollar_per_cpu_mark_multi"])
                if metrics["dollar_per_cpu_mark_multi"] is not None
                else None
            ),
            "dollar_per_cpu_mark_single": (
                str(metrics["dollar_per_cpu_mark_single"])
                if metrics["dollar_per_cpu_mark_single"] is not None
                else None
            ),
            "composite_score": metrics["composite_score"],
            "calculated_at": datetime.utcnow().isoformat(),
        }

        # Prepare data for repository
        build_data = {
            "user_id": user_id,
            "name": name.strip(),
            "description": request.get("description"),
            "tags": request.get("tags"),
            "visibility": visibility,
            "share_token": share_token,
            "cpu_id": components.get("cpu_id"),
            "gpu_id": components.get("gpu_id"),
            "ram_spec_id": components.get("ram_spec_id"),
            "storage_spec_id": components.get("storage_spec_id"),
            "psu_spec_id": components.get("psu_spec_id"),
            "case_spec_id": components.get("case_spec_id"),
            "pricing_snapshot": pricing_snapshot,
            "metrics_snapshot": metrics_snapshot,
            "valuation_breakdown": breakdown,
        }

        # Call repository to persist
        build = await self.repository.create(build_data)

        logger.info(
            "build.saved",
            build_id=build.id,
            user_id=user_id,
            name=name,
            visibility=visibility,
            base_price=str(base_price),
            adjusted_price=str(adjusted_price),
        )

        return build

    async def get_user_builds(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[SavedBuild]:
        """List user's saved builds with pagination.

        Simple delegation to repository layer. Builds are ordered by
        creation date (newest first).

        Args:
            user_id: Owner user ID
            limit: Maximum number of builds to return (default: 10)
            offset: Number of builds to skip for pagination (default: 0)

        Returns:
            List of SavedBuild instances owned by user
        """
        return await self.repository.list_by_user(user_id, limit, offset)

    async def get_build_by_id(
        self, build_id: int, user_id: Optional[int] = None
    ) -> Optional[SavedBuild]:
        """Get single build with access control.

        Access control handled by repository:
        - Public/unlisted builds: accessible to anyone
        - Private builds: only accessible to owner

        Args:
            build_id: Build ID to retrieve
            user_id: Optional user ID for access control validation

        Returns:
            SavedBuild instance if found and accessible, None otherwise
        """
        return await self.repository.get_by_id(build_id, user_id)

    async def compare_build_to_listings(
        self, cpu_id: int, ram_gb: int, storage_gb: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar pre-built listings for comparison.

        Searches for listings with:
        - Same CPU (preferred) or similar performance tier
        - Similar RAM (±8GB tolerance)
        - Similar storage (±256GB tolerance)

        Args:
            cpu_id: CPU ID from build
            ram_gb: Total RAM in GB
            storage_gb: Total storage in GB
            limit: Maximum number of listings to return (default: 5)

        Returns:
            List of dictionaries with listing comparison data:
                - listing_id (int): Listing ID
                - name (str): Listing title
                - price (Decimal): Original price
                - adjusted_price (Decimal): Adjusted price
                - deal_quality (str): 'great', 'good', 'fair', 'premium'
                - price_difference (Decimal): Price vs custom build
                - similarity_score (float): 0-1 similarity score

        Notes:
            This is a "nice to have" method for Phase 3.
            Can be enhanced in Phase 4 with more sophisticated matching.
        """
        # Query listings with same CPU or similar specs
        stmt = (
            select(Listing)
            .options(
                joinedload(Listing.cpu),
                joinedload(Listing.gpu),
            )
            .where(
                and_(
                    Listing.cpu_id == cpu_id,
                    Listing.price_usd.isnot(None),
                    Listing.adjusted_price_usd.isnot(None),
                )
            )
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        listings = list(result.unique().scalars().all())

        # Build comparison results
        comparisons = []
        for listing in listings:
            # Calculate similarity score (0-1 scale)
            similarity_score = 1.0  # Same CPU = perfect match

            # Adjust similarity based on RAM difference
            if listing.ram_gb:
                ram_diff = abs(listing.ram_gb - ram_gb)
                if ram_diff <= 8:
                    similarity_score *= 0.95
                elif ram_diff <= 16:
                    similarity_score *= 0.85
                else:
                    similarity_score *= 0.70

            # Adjust similarity based on storage difference
            if listing.primary_storage_gb:
                storage_diff = abs(listing.primary_storage_gb - storage_gb)
                if storage_diff <= 256:
                    similarity_score *= 0.95
                elif storage_diff <= 512:
                    similarity_score *= 0.85
                else:
                    similarity_score *= 0.70

            # Determine deal quality (simplified for Phase 3)
            price = Decimal(str(listing.price_usd)) if listing.price_usd else Decimal("0")
            adjusted_price = (
                Decimal(str(listing.adjusted_price_usd))
                if listing.adjusted_price_usd
                else Decimal("0")
            )

            # Price difference is positive if listing is more expensive
            price_difference = price - Decimal("0")  # Placeholder

            # Deal quality based on adjusted_price thresholds
            deal_quality = "fair"
            if adjusted_price < price * Decimal("0.85"):
                deal_quality = "great"
            elif adjusted_price < price * Decimal("0.95"):
                deal_quality = "good"
            elif adjusted_price > price * Decimal("1.10"):
                deal_quality = "premium"

            comparisons.append(
                {
                    "listing_id": listing.id,
                    "name": listing.title,
                    "price": price,
                    "adjusted_price": adjusted_price,
                    "deal_quality": deal_quality,
                    "price_difference": price_difference,
                    "similarity_score": similarity_score,
                }
            )

        # Sort by similarity score (highest first)
        comparisons.sort(key=lambda x: x["similarity_score"], reverse=True)

        logger.info(
            "build.comparison.completed",
            cpu_id=cpu_id,
            ram_gb=ram_gb,
            storage_gb=storage_gb,
            matches_found=len(comparisons),
        )

        return comparisons
