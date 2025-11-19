"""Service for exporting and importing Deal Brain artifacts (listings and collections).

This module implements the business logic for:
- Exporting listings and collections as portable JSON (v1.0.0 schema)
- Importing JSON artifacts with validation and duplicate detection
- Preview system for confirming imports before committing
- Schema version validation and migration support

Export/Import Flow:
    1. Export: Fetch entity → Build export schema → Serialize to JSON
    2. Import: Parse JSON → Validate schema → Detect duplicates → Preview
    3. Confirm: Apply merge strategy → Create entities → Return result
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..models.catalog import Cpu, Gpu, RamSpec, StorageProfile
from ..models.core import Listing, ListingComponent
from ..models.ports import Port, PortsProfile
from ..models.sharing import Collection, CollectionItem
from ..schemas.export_import import (
    CPUExport,
    CollectionDataExport,
    CollectionExport,
    CollectionItemExport,
    ComponentExport,
    DealDataExport,
    ExportMetadata,
    GPUExport,
    ListingExport,
    ListingLinkExport,
    MetadataExport,
    PerformanceExport,
    PerformanceMetricsExport,
    PortableCollectionExport,
    PortableDealExport,
    PortExport,
    PortsExport,
    RAMExport,
    StorageExport,
    ValuationExport,
)
from dealbrain_core.enums import (
    Condition,
    ListingStatus,
    PortType,
    RamGeneration,
    StorageMedium,
)

logger = logging.getLogger(__name__)


# ==================== Preview Storage ====================


@dataclass
class ImportPreview:
    """Preview of an import operation before confirmation.

    Attributes:
        preview_id: Unique ID for this preview
        type: Type of import (deal or collection)
        data: Validated export data
        duplicates: List of potential duplicate entities
        created_at: When preview was created
        expires_at: When preview expires (30 minutes)
    """

    preview_id: str
    type: Literal["deal", "collection"]
    data: PortableDealExport | PortableCollectionExport
    duplicates: list[DuplicateMatch]
    created_at: datetime
    expires_at: datetime


@dataclass
class DuplicateMatch:
    """Potential duplicate entity match.

    Attributes:
        entity_id: ID of existing entity
        entity_type: Type of entity (listing or collection)
        match_score: Confidence score (0.0-1.0)
        match_reason: Human-readable explanation
        entity_data: Partial data for display
    """

    entity_id: int
    entity_type: Literal["listing", "collection"]
    match_score: float
    match_reason: str
    entity_data: dict[str, Any]


class PreviewCache:
    """In-memory cache for import previews with TTL."""

    def __init__(self, ttl_minutes: int = 30):
        """Initialize preview cache.

        Args:
            ttl_minutes: Time-to-live for previews in minutes
        """
        self._cache: dict[str, ImportPreview] = {}
        self._ttl_minutes = ttl_minutes

    def store(self, preview: ImportPreview) -> str:
        """Store preview and return preview ID.

        Args:
            preview: Import preview to store

        Returns:
            Preview ID
        """
        self._cache[preview.preview_id] = preview
        self._cleanup_expired()
        return preview.preview_id

    def get(self, preview_id: str) -> ImportPreview | None:
        """Retrieve preview by ID.

        Args:
            preview_id: Preview ID

        Returns:
            ImportPreview if found and not expired, None otherwise
        """
        preview = self._cache.get(preview_id)
        if preview and preview.expires_at > datetime.utcnow():
            return preview
        return None

    def remove(self, preview_id: str) -> None:
        """Remove preview from cache.

        Args:
            preview_id: Preview ID
        """
        self._cache.pop(preview_id, None)

    def _cleanup_expired(self) -> None:
        """Remove expired previews from cache."""
        now = datetime.utcnow()
        expired = [pid for pid, p in self._cache.items() if p.expires_at <= now]
        for pid in expired:
            self._cache.pop(pid)


# Global preview cache instance
_preview_cache = PreviewCache()


# ==================== Export/Import Service ====================


class ExportImportService:
    """Service for exporting and importing Deal Brain artifacts.

    Provides methods for:
    - Exporting listings and collections to portable JSON
    - Importing JSON with validation and duplicate detection
    - Preview system for user confirmation
    - Schema version validation

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    # ==================== Deal Export ====================

    async def export_listing_as_json(
        self, listing_id: int, user_id: int | None = None
    ) -> PortableDealExport:
        """Export single listing as portable JSON (v1.0.0 schema).

        Fetches listing with all relationships and serializes to export schema.

        Args:
            listing_id: Listing ID to export
            user_id: Optional user ID for ownership validation (future use)

        Returns:
            PortableDealExport: Validated export data ready for JSON serialization

        Raises:
            ValueError: If listing not found

        Example:
            >>> export = await service.export_listing_as_json(listing_id=123)
            >>> json_str = export.model_dump_json(indent=2)
        """
        # 1. Fetch listing with all relationships
        stmt = (
            select(Listing)
            .where(Listing.id == listing_id)
            .options(
                joinedload(Listing.cpu),
                joinedload(Listing.gpu),
                joinedload(Listing.ram_spec),
                joinedload(Listing.primary_storage_profile),
                joinedload(Listing.secondary_storage_profile),
                joinedload(Listing.ports_profile).selectinload(PortsProfile.ports),
                selectinload(Listing.components),
            )
        )
        result = await self.session.execute(stmt)
        listing = result.scalar_one_or_none()

        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # 2. Build export data
        listing_export = ListingExport(
            id=listing.id,
            title=listing.title,
            listing_url=listing.listing_url,
            other_urls=[
                ListingLinkExport(url=url.get("url", ""), label=url.get("label"))
                for url in listing.other_urls
            ],
            seller=listing.seller,
            price_usd=listing.price_usd or 0.0,
            price_date=listing.price_date,
            condition=Condition(listing.condition),
            status=ListingStatus(listing.status),
            device_model=listing.device_model,
            notes=listing.notes,
            custom_fields=listing.attributes_json or {},
            created_at=listing.created_at,
            updated_at=listing.updated_at,
        )

        # 3. Build valuation data
        valuation_export = None
        if listing.price_usd is not None:
            valuation_export = ValuationExport(
                base_price_usd=listing.price_usd,
                adjusted_price_usd=listing.adjusted_price_usd,
                valuation_breakdown=listing.valuation_breakdown,
                ruleset_name=listing.ruleset.name if listing.ruleset else None,
            )

        # 4. Build performance data
        cpu_export = None
        if listing.cpu:
            cpu_export = CPUExport(
                name=listing.cpu.name,
                manufacturer=listing.cpu.manufacturer,
                cores=listing.cpu.cores,
                threads=listing.cpu.threads,
                tdp_w=listing.cpu.tdp_w,
                igpu_model=listing.cpu.igpu_model,
                cpu_mark_multi=listing.cpu.cpu_mark_multi,
                cpu_mark_single=listing.cpu.cpu_mark_single,
                igpu_mark=listing.cpu.igpu_mark,
                release_year=listing.cpu.release_year,
            )

        gpu_export = None
        if listing.gpu:
            gpu_export = GPUExport(
                name=listing.gpu.name,
                manufacturer=listing.gpu.manufacturer,
                gpu_mark=listing.gpu.gpu_mark,
                metal_score=listing.gpu.metal_score,
            )

        ram_export = None
        if listing.ram_spec:
            ram_export = RAMExport(
                total_gb=listing.ram_spec.total_capacity_gb,
                ddr_generation=(
                    RamGeneration(listing.ram_spec.ddr_generation)
                    if listing.ram_spec.ddr_generation
                    else None
                ),
                speed_mhz=listing.ram_spec.speed_mhz,
                module_count=listing.ram_spec.module_count,
                capacity_per_module_gb=listing.ram_spec.capacity_per_module_gb,
                notes=listing.ram_notes,
            )

        storage_primary_export = None
        if listing.primary_storage_profile:
            storage_primary_export = StorageExport(
                capacity_gb=listing.primary_storage_profile.capacity_gb,
                medium=(
                    StorageMedium(listing.primary_storage_profile.medium)
                    if listing.primary_storage_profile.medium
                    else None
                ),
                interface=listing.primary_storage_profile.interface,
                form_factor=listing.primary_storage_profile.form_factor,
                performance_tier=listing.primary_storage_profile.performance_tier,
            )

        storage_secondary_export = None
        if listing.secondary_storage_profile:
            storage_secondary_export = StorageExport(
                capacity_gb=listing.secondary_storage_profile.capacity_gb,
                medium=(
                    StorageMedium(listing.secondary_storage_profile.medium)
                    if listing.secondary_storage_profile.medium
                    else None
                ),
                interface=listing.secondary_storage_profile.interface,
                form_factor=listing.secondary_storage_profile.form_factor,
                performance_tier=listing.secondary_storage_profile.performance_tier,
            )

        # 5. Build performance metrics
        metrics_export = None
        if any(
            [
                listing.dollar_per_cpu_mark_single,
                listing.dollar_per_cpu_mark_multi,
                listing.score_cpu_multi,
                listing.score_cpu_single,
                listing.score_gpu,
                listing.score_composite,
            ]
        ):
            metrics_export = PerformanceMetricsExport(
                dollar_per_cpu_mark_single=listing.dollar_per_cpu_mark_single,
                dollar_per_cpu_mark_single_adjusted=listing.dollar_per_cpu_mark_single_adjusted,
                dollar_per_cpu_mark_multi=listing.dollar_per_cpu_mark_multi,
                dollar_per_cpu_mark_multi_adjusted=listing.dollar_per_cpu_mark_multi_adjusted,
                score_cpu_multi=listing.score_cpu_multi,
                score_cpu_single=listing.score_cpu_single,
                score_gpu=listing.score_gpu,
                score_composite=listing.score_composite,
                perf_per_watt=listing.perf_per_watt,
            )

        # 6. Build ports data
        ports_export = None
        if listing.ports_profile:
            ports_export = PortsExport(
                profile_name=listing.ports_profile.name,
                ports=[
                    PortExport(
                        type=PortType(port.type),
                        count=port.count,
                        spec_notes=port.spec_notes,
                    )
                    for port in listing.ports_profile.ports
                ],
            )

        # 7. Build components data
        components_export = [
            ComponentExport(
                component_type=comp.component_type,
                name=comp.name,
                quantity=comp.quantity,
                metadata=comp.metadata_json,
                adjustment_value_usd=comp.adjustment_value_usd,
            )
            for comp in listing.components
        ]

        # 8. Build performance export
        performance_export = PerformanceExport(
            cpu=cpu_export,
            gpu=gpu_export,
            ram=ram_export,
            storage_primary=storage_primary_export,
            storage_secondary=storage_secondary_export,
            metrics=metrics_export,
            ports=ports_export,
            components=components_export,
        )

        # 9. Build metadata export
        metadata_export = MetadataExport(
            manufacturer=listing.manufacturer,
            series=listing.series,
            model_number=listing.model_number,
            form_factor=listing.form_factor,
        )

        # 10. Build complete deal data
        deal_data = DealDataExport(
            listing=listing_export,
            valuation=valuation_export,
            performance=performance_export,
            metadata=metadata_export,
        )

        # 11. Build export metadata
        export_metadata = ExportMetadata(
            version="1.0.0",
            exported_at=datetime.utcnow(),
            exported_by=uuid.UUID(int=user_id) if user_id else None,
            type="deal",
        )

        # 12. Return portable export
        portable_export = PortableDealExport(
            deal_brain_export=export_metadata, data=deal_data
        )

        logger.info(f"Exported listing {listing_id} as v1.0.0 JSON")
        return portable_export

    # ==================== Deal Import ====================

    async def import_listing_from_json(
        self, json_data: dict[str, Any], user_id: int | None = None
    ) -> str:
        """Import listing from JSON with validation and duplicate detection.

        Validates JSON against v1.0.0 schema, detects potential duplicates using
        fuzzy matching, and creates preview for user confirmation.

        Args:
            json_data: Parsed JSON data
            user_id: Optional user ID (for future ownership assignment)

        Returns:
            Preview ID for confirmation

        Raises:
            ValueError: If schema validation fails or version is incompatible

        Example:
            >>> import json
            >>> with open("deal.json") as f:
            ...     data = json.load(f)
            >>> preview_id = await service.import_listing_from_json(data)
            >>> # User reviews preview, then confirms:
            >>> listing = await service.confirm_import_listing(preview_id, "create_new")
        """
        # 1. Validate schema version
        self.validate_schema_version(json_data)

        # 2. Parse and validate against Pydantic schema
        try:
            portable_export = PortableDealExport.model_validate(json_data)
        except ValidationError as e:
            raise ValueError(f"Invalid export schema: {e}")

        # 3. Detect potential duplicates
        duplicates = await self._find_duplicate_listings(portable_export.data.listing)

        # 4. Create preview
        preview = ImportPreview(
            preview_id=str(uuid.uuid4()),
            type="deal",
            data=portable_export,
            duplicates=duplicates,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )

        # 5. Store preview
        preview_id = _preview_cache.store(preview)

        logger.info(
            f"Created import preview {preview_id} for listing '{portable_export.data.listing.title}' "
            f"with {len(duplicates)} potential duplicates"
        )

        return preview_id

    async def confirm_import_listing(
        self,
        preview_id: str,
        merge_strategy: Literal["create_new", "update_existing", "skip"] = "create_new",
        target_listing_id: int | None = None,
    ) -> Listing:
        """Confirm and execute listing import.

        Args:
            preview_id: Preview ID from import_listing_from_json
            merge_strategy: How to handle duplicates
                - create_new: Always create new listing
                - update_existing: Update existing listing (requires target_listing_id)
                - skip: Don't import (raises ValueError)
            target_listing_id: Required if merge_strategy is "update_existing"

        Returns:
            Created or updated Listing

        Raises:
            ValueError: If preview not found, expired, or invalid merge strategy

        Example:
            >>> listing = await service.confirm_import_listing(
            ...     preview_id="abc123",
            ...     merge_strategy="create_new"
            ... )
        """
        # 1. Retrieve preview
        preview = _preview_cache.get(preview_id)
        if not preview:
            raise ValueError("Preview not found or expired")

        if preview.type != "deal":
            raise ValueError("Preview is not for a listing import")

        # 2. Validate merge strategy
        if merge_strategy == "skip":
            _preview_cache.remove(preview_id)
            raise ValueError("Import skipped by user")

        if merge_strategy == "update_existing" and not target_listing_id:
            raise ValueError("target_listing_id required for update_existing strategy")

        # 3. Execute import
        portable_export: PortableDealExport = preview.data
        listing_data = portable_export.data.listing

        if merge_strategy == "update_existing":
            # Update existing listing
            stmt = select(Listing).where(Listing.id == target_listing_id)
            result = await self.session.execute(stmt)
            listing = result.scalar_one_or_none()

            if not listing:
                raise ValueError(f"Target listing {target_listing_id} not found")

            # Update fields
            listing.title = listing_data.title
            listing.listing_url = listing_data.listing_url
            listing.seller = listing_data.seller
            listing.price_usd = listing_data.price_usd
            listing.price_date = listing_data.price_date
            listing.condition = listing_data.condition.value
            listing.status = listing_data.status.value
            listing.device_model = listing_data.device_model
            listing.notes = listing_data.notes
            listing.attributes_json = listing_data.custom_fields
            listing.other_urls = [
                {"url": link.url, "label": link.label}
                for link in listing_data.other_urls
            ]

            logger.info(f"Updated listing {listing.id} from import")

        else:  # create_new
            # Create new listing
            listing = Listing(
                title=listing_data.title,
                listing_url=listing_data.listing_url,
                seller=listing_data.seller,
                price_usd=listing_data.price_usd,
                price_date=listing_data.price_date,
                condition=listing_data.condition.value,
                status=listing_data.status.value,
                device_model=listing_data.device_model,
                notes=listing_data.notes,
                attributes_json=listing_data.custom_fields,
                other_urls=[
                    {"url": link.url, "label": link.label}
                    for link in listing_data.other_urls
                ],
            )

            self.session.add(listing)
            await self.session.flush()

            logger.info(f"Created new listing {listing.id} from import")

        # 4. Import related data (CPU, GPU, RAM, Storage, Ports, Components)
        await self._import_listing_relationships(listing, portable_export.data)

        # 5. Commit transaction
        await self.session.commit()

        # 6. Refresh to get updated relationships
        await self.session.refresh(listing)

        # 7. Clean up preview
        _preview_cache.remove(preview_id)

        return listing

    async def _import_listing_relationships(
        self, listing: Listing, deal_data: DealDataExport
    ) -> None:
        """Import related entities (CPU, GPU, RAM, Storage, Ports, Components).

        Args:
            listing: Listing entity to update
            deal_data: Deal data from export
        """
        # Import CPU
        if deal_data.performance and deal_data.performance.cpu:
            cpu_data = deal_data.performance.cpu
            cpu = await self._get_or_create_cpu(cpu_data)
            listing.cpu_id = cpu.id

        # Import GPU
        if deal_data.performance and deal_data.performance.gpu:
            gpu_data = deal_data.performance.gpu
            gpu = await self._get_or_create_gpu(gpu_data)
            listing.gpu_id = gpu.id

        # Import RAM
        if deal_data.performance and deal_data.performance.ram:
            ram_data = deal_data.performance.ram
            ram_spec = await self._get_or_create_ram_spec(ram_data)
            listing.ram_spec_id = ram_spec.id
            listing.ram_notes = ram_data.notes

        # Import Storage
        if deal_data.performance and deal_data.performance.storage_primary:
            storage_data = deal_data.performance.storage_primary
            storage_profile = await self._get_or_create_storage_profile(storage_data)
            listing.primary_storage_profile_id = storage_profile.id

        if deal_data.performance and deal_data.performance.storage_secondary:
            storage_data = deal_data.performance.storage_secondary
            storage_profile = await self._get_or_create_storage_profile(storage_data)
            listing.secondary_storage_profile_id = storage_profile.id

        # Import Ports
        if deal_data.performance and deal_data.performance.ports:
            ports_data = deal_data.performance.ports
            ports_profile = await self._get_or_create_ports_profile(ports_data)
            listing.ports_profile_id = ports_profile.id

        # Import Components (delete existing and recreate)
        if deal_data.performance and deal_data.performance.components:
            # Delete existing components
            await self.session.execute(
                select(ListingComponent)
                .where(ListingComponent.listing_id == listing.id)
            )
            # Create new components
            for comp_data in deal_data.performance.components:
                component = ListingComponent(
                    listing_id=listing.id,
                    component_type=comp_data.component_type.value,
                    name=comp_data.name,
                    quantity=comp_data.quantity,
                    metadata_json=comp_data.metadata,
                    adjustment_value_usd=comp_data.adjustment_value_usd,
                )
                self.session.add(component)

        # Import Metadata
        if deal_data.metadata:
            listing.manufacturer = deal_data.metadata.manufacturer
            listing.series = deal_data.metadata.series
            listing.model_number = deal_data.metadata.model_number
            listing.form_factor = deal_data.metadata.form_factor

        # Import Valuation
        if deal_data.valuation:
            listing.adjusted_price_usd = deal_data.valuation.adjusted_price_usd
            listing.valuation_breakdown = deal_data.valuation.valuation_breakdown

        # Import Performance Metrics
        if deal_data.performance and deal_data.performance.metrics:
            metrics = deal_data.performance.metrics
            listing.dollar_per_cpu_mark_single = metrics.dollar_per_cpu_mark_single
            listing.dollar_per_cpu_mark_single_adjusted = (
                metrics.dollar_per_cpu_mark_single_adjusted
            )
            listing.dollar_per_cpu_mark_multi = metrics.dollar_per_cpu_mark_multi
            listing.dollar_per_cpu_mark_multi_adjusted = (
                metrics.dollar_per_cpu_mark_multi_adjusted
            )
            listing.score_cpu_multi = metrics.score_cpu_multi
            listing.score_cpu_single = metrics.score_cpu_single
            listing.score_gpu = metrics.score_gpu
            listing.score_composite = metrics.score_composite
            listing.perf_per_watt = metrics.perf_per_watt

        await self.session.flush()

    async def _get_or_create_cpu(self, cpu_data: CPUExport) -> Cpu:
        """Get existing CPU or create new one.

        Args:
            cpu_data: CPU export data

        Returns:
            CPU entity
        """
        # Try to find existing CPU by name
        stmt = select(Cpu).where(Cpu.name == cpu_data.name)
        result = await self.session.execute(stmt)
        cpu = result.scalar_one_or_none()

        if not cpu:
            # Create new CPU
            cpu = Cpu(
                name=cpu_data.name,
                manufacturer=cpu_data.manufacturer,
                cores=cpu_data.cores,
                threads=cpu_data.threads,
                tdp_w=cpu_data.tdp_w,
                igpu_model=cpu_data.igpu_model,
                cpu_mark_multi=cpu_data.cpu_mark_multi,
                cpu_mark_single=cpu_data.cpu_mark_single,
                igpu_mark=cpu_data.igpu_mark,
                release_year=cpu_data.release_year,
            )
            self.session.add(cpu)
            await self.session.flush()
            logger.info(f"Created CPU '{cpu_data.name}'")

        return cpu

    async def _get_or_create_gpu(self, gpu_data: GPUExport) -> Gpu:
        """Get existing GPU or create new one.

        Args:
            gpu_data: GPU export data

        Returns:
            GPU entity
        """
        # Try to find existing GPU by name
        stmt = select(Gpu).where(Gpu.name == gpu_data.name)
        result = await self.session.execute(stmt)
        gpu = result.scalar_one_or_none()

        if not gpu:
            # Create new GPU
            gpu = Gpu(
                name=gpu_data.name,
                manufacturer=gpu_data.manufacturer,
                gpu_mark=gpu_data.gpu_mark,
                metal_score=gpu_data.metal_score,
            )
            self.session.add(gpu)
            await self.session.flush()
            logger.info(f"Created GPU '{gpu_data.name}'")

        return gpu

    async def _get_or_create_ram_spec(self, ram_data: RAMExport) -> RamSpec:
        """Get existing RAM spec or create new one.

        Args:
            ram_data: RAM export data

        Returns:
            RamSpec entity
        """
        # Try to find existing RAM spec by dimensions
        stmt = select(RamSpec).where(
            RamSpec.total_capacity_gb == ram_data.total_gb,
            RamSpec.ddr_generation == (ram_data.ddr_generation.value if ram_data.ddr_generation else None),
            RamSpec.speed_mhz == ram_data.speed_mhz,
            RamSpec.module_count == ram_data.module_count,
            RamSpec.capacity_per_module_gb == ram_data.capacity_per_module_gb,
        )
        result = await self.session.execute(stmt)
        ram_spec = result.scalar_one_or_none()

        if not ram_spec:
            # Create new RAM spec
            ram_spec = RamSpec(
                total_capacity_gb=ram_data.total_gb,
                ddr_generation=ram_data.ddr_generation.value if ram_data.ddr_generation else None,
                speed_mhz=ram_data.speed_mhz,
                module_count=ram_data.module_count,
                capacity_per_module_gb=ram_data.capacity_per_module_gb,
            )
            self.session.add(ram_spec)
            await self.session.flush()
            logger.info(f"Created RAM spec {ram_data.total_gb}GB")

        return ram_spec

    async def _get_or_create_storage_profile(
        self, storage_data: StorageExport
    ) -> StorageProfile:
        """Get existing storage profile or create new one.

        Args:
            storage_data: Storage export data

        Returns:
            StorageProfile entity
        """
        # Try to find existing storage profile by dimensions
        stmt = select(StorageProfile).where(
            StorageProfile.capacity_gb == storage_data.capacity_gb,
            StorageProfile.medium == (storage_data.medium.value if storage_data.medium else None),
            StorageProfile.interface == storage_data.interface,
            StorageProfile.form_factor == storage_data.form_factor,
        )
        result = await self.session.execute(stmt)
        storage_profile = result.scalar_one_or_none()

        if not storage_profile:
            # Create new storage profile
            storage_profile = StorageProfile(
                capacity_gb=storage_data.capacity_gb,
                medium=storage_data.medium.value if storage_data.medium else None,
                interface=storage_data.interface,
                form_factor=storage_data.form_factor,
                performance_tier=storage_data.performance_tier,
            )
            self.session.add(storage_profile)
            await self.session.flush()
            logger.info(f"Created storage profile {storage_data.capacity_gb}GB")

        return storage_profile

    async def _get_or_create_ports_profile(
        self, ports_data: PortsExport
    ) -> PortsProfile:
        """Get existing ports profile or create new one.

        Args:
            ports_data: Ports export data

        Returns:
            PortsProfile entity
        """
        # For ports, we'll create a new profile with a unique name if profile_name exists
        profile_name = ports_data.profile_name or f"Imported_{uuid.uuid4().hex[:8]}"

        # Try to find existing ports profile by name
        stmt = select(PortsProfile).where(PortsProfile.name == profile_name)
        result = await self.session.execute(stmt)
        ports_profile = result.scalar_one_or_none()

        if not ports_profile:
            # Create new ports profile
            ports_profile = PortsProfile(name=profile_name)
            self.session.add(ports_profile)
            await self.session.flush()

            # Create ports
            for port_data in ports_data.ports:
                port = Port(
                    ports_profile_id=ports_profile.id,
                    type=port_data.type.value,
                    count=port_data.count,
                    spec_notes=port_data.spec_notes,
                )
                self.session.add(port)

            await self.session.flush()
            logger.info(f"Created ports profile '{profile_name}'")

        return ports_profile

    # ==================== Collection Export ====================

    async def export_collection_as_json(
        self, collection_id: int, user_id: int
    ) -> PortableCollectionExport:
        """Export collection as portable JSON (v1.0.0 schema).

        Fetches collection with all items and exports each item using deal export logic.

        Args:
            collection_id: Collection ID to export
            user_id: User ID (for ownership validation)

        Returns:
            PortableCollectionExport: Validated export data ready for JSON serialization

        Raises:
            ValueError: If collection not found or access denied

        Example:
            >>> export = await service.export_collection_as_json(collection_id=5, user_id=1)
            >>> json_str = export.model_dump_json(indent=2)
        """
        # 1. Fetch collection with items
        stmt = (
            select(Collection)
            .where(Collection.id == collection_id, Collection.user_id == user_id)
            .options(
                selectinload(Collection.items).joinedload(CollectionItem.listing)
            )
        )
        result = await self.session.execute(stmt)
        collection = result.scalar_one_or_none()

        if not collection:
            raise ValueError(
                f"Collection {collection_id} not found or access denied"
            )

        # 2. Export collection metadata
        collection_export = CollectionExport(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            visibility=collection.visibility,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )

        # 3. Export each collection item
        items_export = []
        for item in collection.items:
            # Export the listing
            listing_export = await self.export_listing_as_json(
                item.listing_id, user_id
            )

            # Create collection item export
            item_export = CollectionItemExport(
                listing=listing_export.data,
                status=item.status,
                notes=item.notes,
                position=item.position,
                added_at=item.added_at,
            )
            items_export.append(item_export)

        # 4. Build collection data
        collection_data = CollectionDataExport(
            collection=collection_export, items=items_export
        )

        # 5. Build export metadata
        export_metadata = ExportMetadata(
            version="1.0.0",
            exported_at=datetime.utcnow(),
            exported_by=uuid.UUID(int=user_id) if user_id else None,
            type="collection",
        )

        # 6. Return portable export
        portable_export = PortableCollectionExport(
            deal_brain_export=export_metadata, data=collection_data
        )

        logger.info(
            f"Exported collection {collection_id} with {len(items_export)} items as v1.0.0 JSON"
        )
        return portable_export

    # ==================== Collection Import ====================

    async def import_collection_from_json(
        self, json_data: dict[str, Any], user_id: int
    ) -> str:
        """Import collection from JSON with validation and duplicate detection.

        Validates JSON against v1.0.0 schema, detects potential duplicate collections,
        and creates preview for user confirmation.

        Args:
            json_data: Parsed JSON data
            user_id: User ID (for ownership assignment)

        Returns:
            Preview ID for confirmation

        Raises:
            ValueError: If schema validation fails or version is incompatible

        Example:
            >>> import json
            >>> with open("collection.json") as f:
            ...     data = json.load(f)
            >>> preview_id = await service.import_collection_from_json(data, user_id=1)
            >>> # User reviews preview, then confirms:
            >>> collection = await service.confirm_import_collection(preview_id, "create_new")
        """
        # 1. Validate schema version
        self.validate_schema_version(json_data)

        # 2. Parse and validate against Pydantic schema
        try:
            portable_export = PortableCollectionExport.model_validate(json_data)
        except ValidationError as e:
            raise ValueError(f"Invalid export schema: {e}")

        # 3. Detect potential duplicate collections
        duplicates = await self._find_duplicate_collections(
            portable_export.data.collection, user_id
        )

        # 4. Create preview
        preview = ImportPreview(
            preview_id=str(uuid.uuid4()),
            type="collection",
            data=portable_export,
            duplicates=duplicates,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )

        # 5. Store preview
        preview_id = _preview_cache.store(preview)

        logger.info(
            f"Created import preview {preview_id} for collection '{portable_export.data.collection.name}' "
            f"with {len(duplicates)} potential duplicates and {len(portable_export.data.items)} items"
        )

        return preview_id

    async def confirm_import_collection(
        self,
        preview_id: str,
        merge_strategy: Literal["create_new", "merge_items", "skip"] = "create_new",
        target_collection_id: int | None = None,
        user_id: int | None = None,
    ) -> Collection:
        """Confirm and execute collection import.

        Args:
            preview_id: Preview ID from import_collection_from_json
            merge_strategy: How to handle duplicates
                - create_new: Always create new collection
                - merge_items: Add items to existing collection (requires target_collection_id)
                - skip: Don't import (raises ValueError)
            target_collection_id: Required if merge_strategy is "merge_items"
            user_id: User ID for ownership (required for create_new)

        Returns:
            Created or updated Collection

        Raises:
            ValueError: If preview not found, expired, or invalid merge strategy

        Example:
            >>> collection = await service.confirm_import_collection(
            ...     preview_id="abc123",
            ...     merge_strategy="create_new",
            ...     user_id=1
            ... )
        """
        # 1. Retrieve preview
        preview = _preview_cache.get(preview_id)
        if not preview:
            raise ValueError("Preview not found or expired")

        if preview.type != "collection":
            raise ValueError("Preview is not for a collection import")

        # 2. Validate merge strategy
        if merge_strategy == "skip":
            _preview_cache.remove(preview_id)
            raise ValueError("Import skipped by user")

        if merge_strategy == "merge_items" and not target_collection_id:
            raise ValueError(
                "target_collection_id required for merge_items strategy"
            )

        if merge_strategy == "create_new" and not user_id:
            raise ValueError("user_id required for create_new strategy")

        # 3. Execute import
        portable_export: PortableCollectionExport = preview.data
        collection_data = portable_export.data.collection

        if merge_strategy == "merge_items":
            # Merge items into existing collection
            stmt = select(Collection).where(Collection.id == target_collection_id)
            result = await self.session.execute(stmt)
            collection = result.scalar_one_or_none()

            if not collection:
                raise ValueError(
                    f"Target collection {target_collection_id} not found"
                )

            logger.info(
                f"Merging {len(portable_export.data.items)} items into collection {collection.id}"
            )

        else:  # create_new
            # Create new collection
            collection = Collection(
                user_id=user_id,
                name=collection_data.name,
                description=collection_data.description,
                visibility=collection_data.visibility.value,
            )

            self.session.add(collection)
            await self.session.flush()

            logger.info(
                f"Created new collection {collection.id} '{collection_data.name}'"
            )

        # 4. Import collection items
        for item_data in portable_export.data.items:
            # Import the listing first
            listing_preview_id = await self.import_listing_from_json(
                {
                    "deal_brain_export": {
                        "version": "1.0.0",
                        "exported_at": datetime.utcnow().isoformat(),
                        "type": "deal",
                    },
                    "data": item_data.listing.model_dump(),
                }
            )

            # Confirm import with create_new strategy
            listing = await self.confirm_import_listing(
                listing_preview_id, merge_strategy="create_new"
            )

            # Create collection item
            collection_item = CollectionItem(
                collection_id=collection.id,
                listing_id=listing.id,
                status=item_data.status.value,
                notes=item_data.notes,
                position=item_data.position,
                added_at=item_data.added_at,
            )
            self.session.add(collection_item)

        # 5. Commit transaction
        await self.session.commit()

        # 6. Refresh to get updated relationships
        await self.session.refresh(collection)

        # 7. Clean up preview
        _preview_cache.remove(preview_id)

        return collection

    # ==================== Schema Versioning ====================

    def validate_schema_version(self, json_data: dict[str, Any]) -> str:
        """Validate export schema version.

        Args:
            json_data: Parsed JSON data

        Returns:
            Schema version string

        Raises:
            ValueError: If version is missing, invalid, or incompatible

        Example:
            >>> version = service.validate_schema_version(json_data)
            >>> assert version == "1.0.0"
        """
        if "deal_brain_export" not in json_data:
            raise ValueError("Missing 'deal_brain_export' metadata")

        metadata = json_data["deal_brain_export"]

        if "version" not in metadata:
            raise ValueError("Missing 'version' in export metadata")

        version = metadata["version"]

        # v1.0.0 is LOCKED - only accept exact match
        if version != "1.0.0":
            raise ValueError(
                f"Incompatible schema version: {version}. "
                f"Only v1.0.0 is currently supported. "
                f"Migration from older versions may be required."
            )

        return version

    def migrate_schema(
        self,
        json_data: dict[str, Any],
        from_version: str,
        to_version: str = "1.0.0",
    ) -> dict[str, Any]:
        """Migrate schema from one version to another (future-proof).

        This is a placeholder for future schema migrations.
        Currently only v1.0.0 is supported.

        Args:
            json_data: Parsed JSON data
            from_version: Source schema version
            to_version: Target schema version (default: 1.0.0)

        Returns:
            Migrated JSON data

        Raises:
            NotImplementedError: Migration not implemented for this version pair

        Example:
            >>> # Future use when v0.9 → v1.0 migration is needed
            >>> migrated = service.migrate_schema(json_data, "0.9.0", "1.0.0")
        """
        if from_version == to_version:
            return json_data

        # Placeholder for future migrations
        if from_version == "0.9.0" and to_version == "1.0.0":
            # TODO: Implement 0.9 → 1.0 migration when needed
            raise NotImplementedError(
                "Migration from v0.9.0 to v1.0.0 not yet implemented"
            )

        raise NotImplementedError(
            f"Migration from {from_version} to {to_version} not supported"
        )

    # ==================== Duplicate Detection ====================

    async def _find_duplicate_listings(
        self, listing_data: ListingExport
    ) -> list[DuplicateMatch]:
        """Find potential duplicate listings using fuzzy matching.

        Matches on:
        1. Exact title + seller match (score: 1.0)
        2. Title similarity + price similarity (score: 0.8-0.95)
        3. URL match (score: 1.0)

        Args:
            listing_data: Listing export data

        Returns:
            List of potential duplicate matches sorted by score
        """
        duplicates: list[DuplicateMatch] = []

        # 1. Exact title + seller match
        if listing_data.seller:
            stmt = select(Listing).where(
                Listing.title == listing_data.title,
                Listing.seller == listing_data.seller,
            )
            result = await self.session.execute(stmt)
            exact_matches = result.scalars().all()

            for match in exact_matches:
                duplicates.append(
                    DuplicateMatch(
                        entity_id=match.id,
                        entity_type="listing",
                        match_score=1.0,
                        match_reason="Exact title and seller match",
                        entity_data={
                            "id": match.id,
                            "title": match.title,
                            "seller": match.seller,
                            "price_usd": match.price_usd,
                        },
                    )
                )

        # 2. URL match
        if listing_data.listing_url:
            stmt = select(Listing).where(Listing.listing_url == listing_data.listing_url)
            result = await self.session.execute(stmt)
            url_matches = result.scalars().all()

            for match in url_matches:
                # Skip if already added as exact match
                if any(d.entity_id == match.id for d in duplicates):
                    continue

                duplicates.append(
                    DuplicateMatch(
                        entity_id=match.id,
                        entity_type="listing",
                        match_score=1.0,
                        match_reason="Exact URL match",
                        entity_data={
                            "id": match.id,
                            "title": match.title,
                            "listing_url": match.listing_url,
                            "price_usd": match.price_usd,
                        },
                    )
                )

        # 3. Fuzzy title + price similarity
        # Normalize title for comparison
        normalized_title = self._normalize_text(listing_data.title)

        # Get all listings for fuzzy comparison (limit to recent 100 for performance)
        stmt = select(Listing).order_by(Listing.created_at.desc()).limit(100)
        result = await self.session.execute(stmt)
        all_listings = result.scalars().all()

        for listing in all_listings:
            # Skip if already matched
            if any(d.entity_id == listing.id for d in duplicates):
                continue

            # Calculate title similarity
            normalized_existing = self._normalize_text(listing.title)
            title_similarity = self._text_similarity(
                normalized_title, normalized_existing
            )

            # Calculate price similarity (if both have prices)
            price_similarity = 0.0
            if listing_data.price_usd and listing.price_usd:
                price_diff = abs(listing_data.price_usd - listing.price_usd)
                max_price = max(listing_data.price_usd, listing.price_usd)
                price_similarity = 1.0 - (price_diff / max_price)

            # Combined score (weighted: 70% title, 30% price)
            combined_score = (title_similarity * 0.7) + (price_similarity * 0.3)

            # Only consider if score > 0.7
            if combined_score > 0.7:
                duplicates.append(
                    DuplicateMatch(
                        entity_id=listing.id,
                        entity_type="listing",
                        match_score=combined_score,
                        match_reason=f"Similar title ({title_similarity:.0%}) and price ({price_similarity:.0%})",
                        entity_data={
                            "id": listing.id,
                            "title": listing.title,
                            "price_usd": listing.price_usd,
                            "seller": listing.seller,
                        },
                    )
                )

        # Sort by score descending
        duplicates.sort(key=lambda x: x.match_score, reverse=True)

        return duplicates

    async def _find_duplicate_collections(
        self, collection_data: CollectionExport, user_id: int
    ) -> list[DuplicateMatch]:
        """Find potential duplicate collections by name.

        Args:
            collection_data: Collection export data
            user_id: User ID for scoping search

        Returns:
            List of potential duplicate matches sorted by score
        """
        duplicates: list[DuplicateMatch] = []

        # 1. Exact name match (same user)
        stmt = select(Collection).where(
            Collection.name == collection_data.name, Collection.user_id == user_id
        )
        result = await self.session.execute(stmt)
        exact_matches = result.scalars().all()

        for match in exact_matches:
            duplicates.append(
                DuplicateMatch(
                    entity_id=match.id,
                    entity_type="collection",
                    match_score=1.0,
                    match_reason="Exact name match",
                    entity_data={
                        "id": match.id,
                        "name": match.name,
                        "description": match.description,
                        "item_count": len(match.items),
                    },
                )
            )

        # 2. Fuzzy name match (same user)
        normalized_name = self._normalize_text(collection_data.name)

        stmt = select(Collection).where(Collection.user_id == user_id)
        result = await self.session.execute(stmt)
        all_collections = result.scalars().all()

        for collection in all_collections:
            # Skip if already matched
            if any(d.entity_id == collection.id for d in duplicates):
                continue

            # Calculate name similarity
            normalized_existing = self._normalize_text(collection.name)
            name_similarity = self._text_similarity(normalized_name, normalized_existing)

            # Only consider if score > 0.7
            if name_similarity > 0.7:
                duplicates.append(
                    DuplicateMatch(
                        entity_id=collection.id,
                        entity_type="collection",
                        match_score=name_similarity,
                        match_reason=f"Similar name ({name_similarity:.0%})",
                        entity_data={
                            "id": collection.id,
                            "name": collection.name,
                            "description": collection.description,
                            "item_count": len(collection.items),
                        },
                    )
                )

        # Sort by score descending
        duplicates.sort(key=lambda x: x.match_score, reverse=True)

        return duplicates

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison.

        Args:
            text: Input text

        Returns:
            Normalized text (lowercase, no extra spaces)
        """
        return " ".join(text.lower().split())

    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """Calculate text similarity using simple token-based Jaccard similarity.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0-1.0)
        """
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        return len(intersection) / len(union)


__all__ = [
    "ExportImportService",
    "ImportPreview",
    "DuplicateMatch",
    "PreviewCache",
]
