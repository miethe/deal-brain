"""Service for validating formulas and providing preview calculations"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.rules.formula import FormulaEngine, FormulaParser
from dealbrain_core.rules.formula_validator import FormulaValidator, ValidationError

from ..models.core import CustomFieldDefinition, Listing, Cpu, Gpu

logger = logging.getLogger(__name__)


class FormulaValidationService:
    """Service for validating formulas and providing preview calculations"""

    def __init__(self):
        self.parser = FormulaParser()
        self.validator = FormulaValidator()
        self.engine = FormulaEngine()

    async def get_available_fields(self, session: AsyncSession, entity_type: str) -> set[str]:
        """
        Get available field names for an entity type.

        Args:
            session: Database session
            entity_type: Entity type (Listing, CPU, GPU, etc.)

        Returns:
            Set of available field names
        """
        fields = set()

        # Normalize entity type
        entity_type_normalized = entity_type.lower()

        # Get custom fields for this entity
        query = select(CustomFieldDefinition).where(
            CustomFieldDefinition.entity == entity_type_normalized,
            CustomFieldDefinition.is_active.is_(True),
            CustomFieldDefinition.deleted_at.is_(None),
        )
        result = await session.execute(query)
        custom_fields = result.scalars().all()

        # Add custom field keys
        for field in custom_fields:
            fields.add(field.key)

        # Add standard model fields based on entity type
        if entity_type_normalized == "listing":
            fields.update(self._get_listing_fields())
        elif entity_type_normalized == "cpu":
            fields.update(self._get_cpu_fields())
        elif entity_type_normalized == "gpu":
            fields.update(self._get_gpu_fields())

        return fields

    def _get_listing_fields(self) -> set[str]:
        """Get standard Listing model fields"""
        return {
            # Pricing fields
            "price_usd",
            "adjusted_price_usd",
            # Metadata
            "title",
            "listing_url",
            "seller",
            "condition",
            "device_model",
            "manufacturer",
            "series",
            "model_number",
            "form_factor",
            "status",
            # Storage and RAM
            "ram_gb",
            "primary_storage_gb",
            "primary_storage_type",
            "secondary_storage_gb",
            "secondary_storage_type",
            # Performance metrics
            "score_cpu_multi",
            "score_cpu_single",
            "score_gpu",
            "score_composite",
            "dollar_per_cpu_mark",
            "dollar_per_single_mark",
            "dollar_per_cpu_mark_single",
            "dollar_per_cpu_mark_single_adjusted",
            "dollar_per_cpu_mark_multi",
            "dollar_per_cpu_mark_multi_adjusted",
            "perf_per_watt",
            # Timestamps
            "created_at",
            "updated_at",
            # Nested fields (CPU)
            "cpu.name",
            "cpu.manufacturer",
            "cpu.cores",
            "cpu.threads",
            "cpu.tdp_w",
            "cpu.cpu_mark_multi",
            "cpu.cpu_mark_single",
            "cpu.igpu_mark",
            "cpu.igpu_model",
            "cpu.socket",
            "cpu.release_year",
            # Nested fields (GPU)
            "gpu.name",
            "gpu.manufacturer",
            "gpu.gpu_mark",
            "gpu.metal_score",
        }

    def _get_cpu_fields(self) -> set[str]:
        """Get standard CPU model fields"""
        return {
            "name",
            "manufacturer",
            "cores",
            "threads",
            "tdp_w",
            "socket",
            "igpu_model",
            "cpu_mark_multi",
            "cpu_mark_single",
            "igpu_mark",
            "release_year",
            "passmark_slug",
            "passmark_category",
            "passmark_id",
            "notes",
            "created_at",
            "updated_at",
        }

    def _get_gpu_fields(self) -> set[str]:
        """Get standard GPU model fields"""
        return {
            "name",
            "manufacturer",
            "gpu_mark",
            "metal_score",
            "notes",
            "created_at",
            "updated_at",
        }

    async def get_sample_context(
        self,
        session: AsyncSession,
        entity_type: str,
        provided_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Get sample context data for formula preview.

        Args:
            session: Database session
            entity_type: Entity type (Listing, CPU, GPU, etc.)
            provided_context: Optional user-provided context values

        Returns:
            Dictionary with sample field values
        """
        # Start with provided context if available
        context = provided_context.copy() if provided_context else {}

        # Normalize entity type
        entity_type_normalized = entity_type.lower()

        # Get a sample entity from database
        if entity_type_normalized == "listing":
            sample = await self._get_sample_listing(session)
            if sample:
                context.update(self._listing_to_context(sample))
        elif entity_type_normalized == "cpu":
            sample = await self._get_sample_cpu(session)
            if sample:
                context.update(self._cpu_to_context(sample))
        elif entity_type_normalized == "gpu":
            sample = await self._get_sample_gpu(session)
            if sample:
                context.update(self._gpu_to_context(sample))

        # If no sample found or context is empty, use default values
        if not context:
            context = self._get_default_context(entity_type_normalized)

        return context

    async def _get_sample_listing(self, session: AsyncSession) -> Listing | None:
        """Get a sample listing from database"""
        query = select(Listing).where(Listing.status == "active").limit(1)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _get_sample_cpu(self, session: AsyncSession) -> Cpu | None:
        """Get a sample CPU from database"""
        query = select(Cpu).limit(1)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def _get_sample_gpu(self, session: AsyncSession) -> Gpu | None:
        """Get a sample GPU from database"""
        query = select(Gpu).limit(1)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    def _listing_to_context(self, listing: Listing) -> dict[str, Any]:
        """Convert listing to context dictionary"""
        context = {
            "price_usd": float(listing.price_usd) if listing.price_usd else 0.0,
            "adjusted_price_usd": (
                float(listing.adjusted_price_usd) if listing.adjusted_price_usd else 0.0
            ),
            "title": listing.title or "",
            "condition": listing.condition or "used",
            "device_model": listing.device_model or "",
            "manufacturer": listing.manufacturer or "",
            "series": listing.series or "",
            "model_number": listing.model_number or "",
            "form_factor": listing.form_factor or "",
            "status": listing.status or "",
            "ram_gb": float(listing.ram_gb) if listing.ram_gb else 0.0,
            "primary_storage_gb": (
                float(listing.primary_storage_gb) if listing.primary_storage_gb else 0.0
            ),
            "primary_storage_type": listing.primary_storage_type or "",
            "secondary_storage_gb": (
                float(listing.secondary_storage_gb) if listing.secondary_storage_gb else 0.0
            ),
            "secondary_storage_type": listing.secondary_storage_type or "",
            "score_cpu_multi": float(listing.score_cpu_multi) if listing.score_cpu_multi else 0.0,
            "score_cpu_single": (
                float(listing.score_cpu_single) if listing.score_cpu_single else 0.0
            ),
            "score_gpu": float(listing.score_gpu) if listing.score_gpu else 0.0,
            "score_composite": float(listing.score_composite) if listing.score_composite else 0.0,
        }

        # Add CPU data if available
        if listing.cpu:
            context["cpu"] = {
                "name": listing.cpu.name or "",
                "manufacturer": listing.cpu.manufacturer or "",
                "cores": listing.cpu.cores or 0,
                "threads": listing.cpu.threads or 0,
                "tdp_w": listing.cpu.tdp_w or 0,
                "cpu_mark_multi": (
                    float(listing.cpu.cpu_mark_multi) if listing.cpu.cpu_mark_multi else 0.0
                ),
                "cpu_mark_single": (
                    float(listing.cpu.cpu_mark_single) if listing.cpu.cpu_mark_single else 0.0
                ),
                "igpu_mark": float(listing.cpu.igpu_mark) if listing.cpu.igpu_mark else 0.0,
                "socket": listing.cpu.socket or "",
                "release_year": listing.cpu.release_year or 0,
            }

        # Add GPU data if available
        if listing.gpu:
            context["gpu"] = {
                "name": listing.gpu.name or "",
                "manufacturer": listing.gpu.manufacturer or "",
                "gpu_mark": float(listing.gpu.gpu_mark) if listing.gpu.gpu_mark else 0.0,
                "metal_score": float(listing.gpu.metal_score) if listing.gpu.metal_score else 0.0,
            }

        return context

    def _cpu_to_context(self, cpu: Cpu) -> dict[str, Any]:
        """Convert CPU to context dictionary"""
        return {
            "name": cpu.name or "",
            "manufacturer": cpu.manufacturer or "",
            "cores": cpu.cores or 0,
            "threads": cpu.threads or 0,
            "tdp_w": cpu.tdp_w or 0,
            "cpu_mark_multi": float(cpu.cpu_mark_multi) if cpu.cpu_mark_multi else 0.0,
            "cpu_mark_single": float(cpu.cpu_mark_single) if cpu.cpu_mark_single else 0.0,
            "igpu_mark": float(cpu.igpu_mark) if cpu.igpu_mark else 0.0,
            "socket": cpu.socket or "",
            "release_year": cpu.release_year or 0,
        }

    def _gpu_to_context(self, gpu: Gpu) -> dict[str, Any]:
        """Convert GPU to context dictionary"""
        return {
            "name": gpu.name or "",
            "manufacturer": gpu.manufacturer or "",
            "gpu_mark": float(gpu.gpu_mark) if gpu.gpu_mark else 0.0,
            "metal_score": float(gpu.metal_score) if gpu.metal_score else 0.0,
        }

    def _get_default_context(self, entity_type: str) -> dict[str, Any]:
        """Get default context values for entity type"""
        if entity_type == "listing":
            return {
                "price_usd": 500.0,
                "adjusted_price_usd": 450.0,
                "ram_gb": 16.0,
                "primary_storage_gb": 512.0,
                "score_cpu_multi": 150.0,
                "score_cpu_single": 125.0,
                "condition": "used",
                "form_factor": "mini",
            }
        elif entity_type == "cpu":
            return {
                "cores": 8,
                "threads": 16,
                "cpu_mark_multi": 15000.0,
                "cpu_mark_single": 2500.0,
                "tdp_w": 65,
                "release_year": 2021,
            }
        elif entity_type == "gpu":
            return {
                "gpu_mark": 15000.0,
                "metal_score": 12000.0,
            }

        return {}

    async def validate_formula(
        self,
        session: AsyncSession,
        formula: str,
        entity_type: str = "Listing",
        sample_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate a formula and provide preview calculation.

        Args:
            session: Database session
            formula: Formula string to validate
            entity_type: Entity type for field context
            sample_context: Optional sample context for preview

        Returns:
            Dictionary with validation results
        """
        errors = []
        preview = None
        used_fields = []

        # Step 1: Validate formula syntax
        validation_errors = self.validator.validate(formula)
        for error in validation_errors:
            errors.append(
                {
                    "message": error.message,
                    "severity": error.severity,
                    "position": error.position,
                    "suggestion": error.suggestion,
                }
            )

        # If there are syntax errors, don't proceed
        if any(e["severity"] == "error" for e in errors):
            available_fields = await self.get_available_fields(session, entity_type)
            return {
                "valid": False,
                "errors": errors,
                "preview": None,
                "used_fields": [],
                "available_fields": sorted(available_fields),
            }

        # Step 2: Extract field references
        used_fields = sorted(self.validator.get_field_references(formula))

        # Step 3: Get available fields and validate field availability
        available_fields = await self.get_available_fields(session, entity_type)
        field_availability_errors = self.validator.validate_field_availability(
            formula, available_fields
        )

        for error in field_availability_errors:
            errors.append(
                {
                    "message": error.message,
                    "severity": error.severity,
                    "position": error.position,
                    "suggestion": error.suggestion,
                }
            )

        # If there are field availability errors, don't proceed to preview
        if any(e["severity"] == "error" for e in errors):
            return {
                "valid": False,
                "errors": errors,
                "preview": None,
                "used_fields": used_fields,
                "available_fields": sorted(available_fields),
            }

        # Step 4: Calculate preview with sample data
        try:
            context = await self.get_sample_context(session, entity_type, sample_context)
            preview = self.engine.evaluate(formula, context)
        except Exception as e:
            logger.warning(f"Preview calculation failed: {e}", exc_info=True)
            errors.append(
                {
                    "message": f"Preview calculation failed: {str(e)}",
                    "severity": "warning",
                    "position": None,
                    "suggestion": "Check that all required fields have values in the sample context",
                }
            )

        # Validation passes if no errors (warnings are okay)
        valid = not any(e["severity"] == "error" for e in errors)

        return {
            "valid": valid,
            "errors": errors,
            "preview": preview,
            "used_fields": used_fields,
            "available_fields": sorted(available_fields),
        }
