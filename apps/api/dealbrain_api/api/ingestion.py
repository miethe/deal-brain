"""API endpoints for URL ingestion workflow."""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from dealbrain_core.enums import SourceType
from dealbrain_core.schemas.ingestion import IngestionRequest, IngestionResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..models.core import ImportSession
from ..tasks.ingestion import ingest_url_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/ingest", tags=["ingestion"])


@router.post("/single", status_code=status.HTTP_202_ACCEPTED, response_model=IngestionResponse)
async def create_single_url_import(
    request: IngestionRequest,
    session: AsyncSession = Depends(session_dependency),
) -> IngestionResponse:
    """
    Create a single URL import job and queue it for processing.

    This endpoint accepts a URL, validates it, creates an ImportSession record,
    and queues a Celery task for asynchronous ingestion. The task will:
    1. Fetch and parse the URL using the adapter router
    2. Extract product data (title, price, specs, etc.)
    3. Create or update a Listing record
    4. Store provenance and quality metadata

    Args:
        request: IngestionRequest containing URL and optional priority
        session: Database session (injected)

    Returns:
        IngestionResponse with job_id and status='queued'

    Raises:
        HTTPException: For validation errors (422) or server errors (500)

    Example:
        POST /api/v1/ingest/single
        {
            "url": "https://www.ebay.com/itm/123456789012",
            "priority": "normal"
        }

        Response (202):
        {
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "queued",
            "listing_id": null,
            "provenance": null,
            "quality": null,
            "errors": []
        }
    """
    try:
        # Generate unique job ID
        job_id = uuid4()

        # Extract domain from URL for filename
        url_str = str(request.url)
        filename = f"url_import_{job_id.hex[:8]}"

        # Create ImportSession record
        import_session = ImportSession(
            id=job_id,
            filename=filename,
            upload_path=url_str,  # Store URL in upload_path for reference
            source_type=SourceType.URL_SINGLE.value,
            url=url_str,
            status="queued",
            sheet_meta_json={},
            mappings_json={},
            conflicts_json={},
            preview_json={},
            declared_entities_json={},
            adapter_config={"priority": request.priority},
        )

        session.add(import_session)
        await session.flush()

        # Queue Celery task for async processing
        ingest_url_task.delay(job_id=str(job_id), url=url_str)

        logger.info(
            "Single URL import job created and queued",
            extra={"job_id": str(job_id), "url": url_str, "priority": request.priority},
        )

        # Return 202 Accepted with job details
        return IngestionResponse(
            job_id=str(job_id),
            status="queued",
            listing_id=None,
            provenance=None,
            quality=None,
            errors=[],
        )

    except Exception as e:
        logger.exception("Error creating single URL import job", extra={"url": str(request.url)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create import job: {str(e)}",
        ) from e


@router.get("/{job_id}", response_model=IngestionResponse)
async def get_ingestion_status(
    job_id: str,
    session: AsyncSession = Depends(session_dependency),
) -> IngestionResponse:
    """
    Retrieve the status of an ingestion job.

    This endpoint fetches the ImportSession record and returns the current status,
    along with any results (listing_id, provenance, quality) or errors.

    Args:
        job_id: ImportSession UUID as string
        session: Database session (injected)

    Returns:
        IngestionResponse with job status and results

    Raises:
        HTTPException: 404 if job not found, 422 if invalid UUID format

    Example:
        GET /api/v1/ingest/550e8400-e29b-41d4-a716-446655440000

        Response (200):
        {
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "complete",
            "listing_id": 123,
            "provenance": "ebay_api",
            "quality": "full",
            "errors": []
        }
    """
    try:
        # Convert string to UUID
        try:
            job_uuid = UUID(job_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid job_id format: {job_id}. Must be a valid UUID.",
            ) from e

        # Query ImportSession
        stmt = select(ImportSession).where(ImportSession.id == job_uuid)
        result = await session.execute(stmt)
        import_session = result.scalar_one_or_none()

        if not import_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        # Extract result data from conflicts_json (populated by Celery task)
        conflicts = import_session.conflicts_json or {}
        listing_id = conflicts.get("listing_id")
        provenance = conflicts.get("provenance")
        quality = conflicts.get("quality")

        # Extract errors if job failed
        errors = []
        if import_session.status == "failed" and "error" in conflicts:
            errors.append(
                {
                    "type": "ingestion_error",
                    "message": conflicts["error"],
                }
            )

        logger.debug(
            "Ingestion status retrieved",
            extra={
                "job_id": job_id,
                "status": import_session.status,
                "listing_id": listing_id,
            },
        )

        return IngestionResponse(
            job_id=job_id,
            status=import_session.status,
            listing_id=listing_id,
            provenance=provenance,
            quality=quality,
            errors=errors,
        )

    except HTTPException:
        # Re-raise HTTPException without wrapping
        raise
    except Exception as e:
        logger.exception("Error retrieving ingestion status", extra={"job_id": job_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job status: {str(e)}",
        ) from e


__all__ = ["router", "create_single_url_import", "get_ingestion_status"]
