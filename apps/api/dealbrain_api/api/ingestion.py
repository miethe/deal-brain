"""API endpoints for URL ingestion workflow."""

from __future__ import annotations

import csv
import io
import json
import logging
from uuid import UUID, uuid4

from dealbrain_core.enums import SourceType
from dealbrain_core.schemas.ingestion import (
    BulkIngestionResponse,
    BulkIngestionStatusResponse,
    IngestionRequest,
    IngestionResponse,
    PerRowStatus,
)
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import HttpUrl, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..models.core import ImportSession
from ..tasks.ingestion import ingest_url_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/ingest", tags=["ingestion"])


# ============================================================================
# Helper Functions
# ============================================================================


def parse_csv_file(content: bytes) -> list[str]:
    """
    Parse CSV file content and extract URLs.

    Expected CSV format:
        url
        https://www.ebay.com/itm/123456789
        https://www.amazon.com/dp/B08N5WRWNW

    Args:
        content: Raw CSV file bytes

    Returns:
        List of URL strings

    Raises:
        ValueError: If CSV is invalid or missing 'url' column
    """
    try:
        # Decode bytes to string
        csv_text = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        # Validate 'url' column exists
        if not csv_reader.fieldnames or "url" not in csv_reader.fieldnames:
            raise ValueError("CSV must have 'url' column header")

        # Extract URLs
        urls = []
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (after header)
            url = row.get("url", "").strip()
            if url:
                urls.append(url)
            else:
                logger.warning(f"Empty URL at row {row_num}, skipping")

        return urls

    except UnicodeDecodeError as e:
        raise ValueError(f"Invalid CSV encoding, expected UTF-8: {e}") from e
    except csv.Error as e:
        raise ValueError(f"Invalid CSV format: {e}") from e


def parse_json_file(content: bytes) -> list[str]:
    """
    Parse JSON file content and extract URLs.

    Expected JSON format:
        [
          {"url": "https://www.ebay.com/itm/123456789"},
          {"url": "https://www.amazon.com/dp/B08N5WRWNW"}
        ]

    Args:
        content: Raw JSON file bytes

    Returns:
        List of URL strings

    Raises:
        ValueError: If JSON is invalid or missing 'url' fields
    """
    try:
        # Decode bytes to string and parse JSON
        json_text = content.decode("utf-8")
        data = json.loads(json_text)

        # Validate array of objects
        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects")

        # Extract URLs
        urls = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"Item at index {idx} must be an object with 'url' field")

            url = item.get("url", "").strip()
            if url:
                urls.append(url)
            else:
                logger.warning(f"Empty URL at index {idx}, skipping")

        return urls

    except UnicodeDecodeError as e:
        raise ValueError(f"Invalid JSON encoding, expected UTF-8: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}") from e


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED, response_model=BulkIngestionResponse)
async def create_bulk_url_import(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(session_dependency),
) -> BulkIngestionResponse:
    """
    Create a bulk URL import job from CSV or JSON file upload.

    This endpoint accepts a file upload (CSV or JSON format) containing up to 1000 URLs,
    creates a parent ImportSession and child sessions for each URL, and queues Celery tasks
    for asynchronous processing.

    File Formats:

    CSV format (header: url):
    ```csv
    url
    https://www.ebay.com/itm/123456789
    https://www.amazon.com/dp/B08N5WRWNW
    ```

    JSON format:
    ```json
    [
      {"url": "https://www.ebay.com/itm/123456789"},
      {"url": "https://www.amazon.com/dp/B08N5WRWNW"}
    ]
    ```

    Args:
        file: Uploaded CSV or JSON file (multipart/form-data)
        session: Database session (injected)

    Returns:
        BulkIngestionResponse with bulk_job_id and total_urls

    Raises:
        HTTPException:
            400: Invalid file format, empty file, or parse errors
            413: More than 1000 URLs in file
            422: Invalid URL format in file
            500: Unexpected server errors

    Example:
        POST /api/v1/ingest/bulk
        Content-Type: multipart/form-data
        file: urls.csv

        Response (202):
        {
            "bulk_job_id": "550e8400-e29b-41d4-a716-446655440000",
            "total_urls": 42
        }
    """
    try:
        # Read file content
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded",
            )

        # Detect format from filename
        filename = file.filename or ""
        file_format = None

        if filename.endswith(".csv"):
            file_format = "csv"
        elif filename.endswith(".json"):
            file_format = "json"
        else:
            # Try to detect from content
            try:
                content.decode("utf-8").strip()
                if content.strip().startswith(b"["):
                    file_format = "json"
                elif b"url" in content[:100]:  # Check first 100 bytes for 'url' header
                    file_format = "csv"
            except Exception:
                # Unable to detect format from content
                logger.debug("Failed to auto-detect file format from content")

        if not file_format:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Unable to detect file format. "
                    "File must be CSV or JSON with .csv or .json extension"
                ),
            )

        # Parse URLs using appropriate helper
        try:
            urls = parse_csv_file(content) if file_format == "csv" else parse_json_file(content)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {file_format.upper()} file: {str(e)}",
            ) from e

        # Validate not empty
        if not urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid URLs found in file",
            )

        # Validate URL count (max 1000)
        if len(urls) > 1000:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Too many URLs: {len(urls)}. Maximum is 1000 URLs per request.",
            )

        # Deduplicate URLs (case-sensitive)
        unique_urls = list(dict.fromkeys(urls))  # Preserves order
        if len(unique_urls) < len(urls):
            logger.info(
                f"Deduplicated URLs: {len(urls)} -> {len(unique_urls)}",
                extra={"original": len(urls), "deduplicated": len(unique_urls)},
            )

        # Validate URLs using Pydantic HttpUrl
        validated_urls = []
        invalid_urls = []
        for url_str in unique_urls:
            try:
                validated_url = HttpUrl(url_str)
                validated_urls.append(str(validated_url))
            except ValidationError:
                invalid_urls.append(url_str)

        if invalid_urls:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid URLs found: {invalid_urls[:5]}",  # Show first 5
            )

        # Generate parent job ID
        parent_job_id = uuid4()

        # Create parent ImportSession
        parent_session = ImportSession(
            id=parent_job_id,
            filename=filename or f"bulk_import_{parent_job_id.hex[:8]}",
            upload_path=f"bulk_upload_{parent_job_id.hex[:8]}",
            source_type=SourceType.URL_BULK.value,
            url=None,  # Parent has no single URL
            status="queued",
            sheet_meta_json={},
            mappings_json={},
            conflicts_json={
                "total_urls": len(validated_urls),
                "file_format": file_format,
            },
            preview_json={},
            declared_entities_json={},
            adapter_config={},
        )

        session.add(parent_session)
        await session.flush()

        # Create child ImportSession for each URL and queue tasks
        child_job_ids = []
        for url in validated_urls:
            child_job_id = uuid4()
            child_session = ImportSession(
                id=child_job_id,
                filename=f"url_import_{child_job_id.hex[:8]}",
                upload_path=url,
                source_type=SourceType.URL_SINGLE.value,
                url=url,
                status="queued",
                sheet_meta_json={},
                mappings_json={},
                conflicts_json={
                    "parent_job_id": str(parent_job_id),
                },
                preview_json={},
                declared_entities_json={},
                adapter_config={},
            )

            session.add(child_session)
            child_job_ids.append(str(child_job_id))

            # Queue Celery task for this URL
            ingest_url_task.delay(job_id=str(child_job_id), url=url)

        await session.flush()

        logger.info(
            "Bulk URL import job created and queued",
            extra={
                "bulk_job_id": str(parent_job_id),
                "total_urls": len(validated_urls),
                "file_format": file_format,
                "child_jobs": len(child_job_ids),
            },
        )

        # Return 202 Accepted with bulk job details
        return BulkIngestionResponse(
            bulk_job_id=str(parent_job_id),
            total_urls=len(validated_urls),
        )

    except HTTPException:
        # Re-raise HTTPException without wrapping
        raise
    except Exception as e:
        logger.exception("Error creating bulk URL import job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bulk import job: {str(e)}",
        ) from e


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


@router.get("/bulk/{bulk_job_id}", response_model=BulkIngestionStatusResponse)
async def get_bulk_ingestion_status(
    bulk_job_id: str,
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=100, ge=1, le=1000, description="Pagination limit"),
    session: AsyncSession = Depends(session_dependency),
) -> BulkIngestionStatusResponse:
    """
    Retrieve the aggregated status of a bulk URL ingestion job.

    This endpoint fetches the parent ImportSession and all child ImportSession records
    for a bulk job, aggregates status counts, and returns per-URL status information
    with pagination support.

    Status Aggregation Logic:
    - total_urls: Total number of URLs in the bulk job
    - completed: Number of URLs finished (complete + partial + failed)
    - success: Number of URLs successfully completed (complete only)
    - partial: Number of partially completed URLs
    - failed: Number of failed URLs
    - running: Number of URLs currently being processed
    - queued: Number of URLs waiting to be processed

    Overall Status Logic:
    - "queued": All children are queued
    - "running": At least one child is running or queued (but not all queued)
    - "complete": All children are complete/partial/failed (100% done)
    - "partial": Some children complete and some failed
    - "failed": All children failed

    Args:
        bulk_job_id: Parent ImportSession UUID as string
        offset: Pagination offset (default: 0)
        limit: Pagination limit (default: 100, max: 1000)
        session: Database session (injected)

    Returns:
        BulkIngestionStatusResponse with aggregated status and per-URL details

    Raises:
        HTTPException:
            404: Bulk job not found
            422: Invalid UUID format
            500: Unexpected server errors

    Example:
        GET /api/v1/ingest/bulk/550e8400-e29b-41d4-a716-446655440000?offset=0&limit=50

        Response (200):
        {
            "bulk_job_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "running",
            "total_urls": 42,
            "completed": 30,
            "success": 25,
            "partial": 3,
            "failed": 2,
            "running": 5,
            "queued": 7,
            "per_row_status": [
                {
                    "url": "https://ebay.com/itm/123",
                    "status": "complete",
                    "listing_id": 456,
                    "error": null
                },
                ...
            ],
            "offset": 0,
            "limit": 50,
            "has_more": false
        }
    """
    try:
        # Convert string to UUID
        try:
            bulk_job_uuid = UUID(bulk_job_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid bulk_job_id format: {bulk_job_id}. Must be a valid UUID.",
            ) from e

        # Query parent ImportSession to verify bulk job exists
        stmt_parent = select(ImportSession).where(ImportSession.id == bulk_job_uuid)
        result_parent = await session.execute(stmt_parent)
        parent_session = result_parent.scalar_one_or_none()

        if not parent_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bulk job {bulk_job_id} not found",
            )

        # Query all child ImportSession records (filter by parent_job_id in conflicts_json)
        # Fetch all potential children and filter in Python (SQLite-compatible)
        stmt_all_sessions = select(ImportSession).where(
            ImportSession.source_type == SourceType.URL_SINGLE.value
        )
        result_all = await session.execute(stmt_all_sessions)
        all_sessions = result_all.scalars().all()

        # Filter children by parent_job_id in conflicts_json (in-memory)
        children_all = [
            s
            for s in all_sessions
            if s.conflicts_json and s.conflicts_json.get("parent_job_id") == str(bulk_job_uuid)
        ]

        # Apply pagination to per_row_status only
        children = children_all[offset : offset + limit]

        # Aggregate status counts across all children (not paginated)
        status_counts: dict[str, int] = {}
        for child in children_all:
            status_counts[child.status] = status_counts.get(child.status, 0) + 1

        # Calculate aggregated metrics
        total_urls = sum(status_counts.values())
        success_count = status_counts.get("complete", 0)
        partial_count = status_counts.get("partial", 0)
        failed_count = status_counts.get("failed", 0)
        running_count = status_counts.get("running", 0)
        queued_count = status_counts.get("queued", 0)
        completed_count = success_count + partial_count + failed_count

        # Determine overall status
        overall_status = "queued"
        if total_urls == 0:
            # No children yet (edge case)
            overall_status = "queued"
        elif queued_count == total_urls:
            # All children are queued
            overall_status = "queued"
        elif running_count > 0 or (queued_count > 0 and queued_count < total_urls):
            # At least one child is running, or some (but not all) are queued
            overall_status = "running"
        elif completed_count == total_urls:
            # All children are done (complete/partial/failed)
            if failed_count == total_urls:
                # All failed
                overall_status = "failed"
            elif success_count > 0 and failed_count > 0:
                # Mixed success and failure
                overall_status = "partial"
            else:
                # All succeeded (complete or partial)
                overall_status = "complete"

        # Build per-row status list
        per_row_status = []
        for child in children:
            conflicts = child.conflicts_json or {}
            per_row_status.append(
                PerRowStatus(
                    url=child.url or "",
                    status=child.status,
                    listing_id=conflicts.get("listing_id"),
                    error=conflicts.get("error"),
                )
            )

        # Calculate has_more flag
        has_more = total_urls > offset + limit

        logger.debug(
            "Bulk ingestion status retrieved",
            extra={
                "bulk_job_id": bulk_job_id,
                "total_urls": total_urls,
                "completed": completed_count,
                "overall_status": overall_status,
            },
        )

        return BulkIngestionStatusResponse(
            bulk_job_id=bulk_job_id,
            status=overall_status,
            total_urls=total_urls,
            completed=completed_count,
            success=success_count,
            partial=partial_count,
            failed=failed_count,
            running=running_count,
            queued=queued_count,
            per_row_status=per_row_status,
            offset=offset,
            limit=limit,
            has_more=has_more,
        )

    except HTTPException:
        # Re-raise HTTPException without wrapping
        raise
    except Exception as e:
        logger.exception(
            "Error retrieving bulk ingestion status", extra={"bulk_job_id": bulk_job_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve bulk job status: {str(e)}",
        ) from e


__all__ = [
    "router",
    "parse_csv_file",
    "parse_json_file",
    "create_bulk_url_import",
    "create_single_url_import",
    "get_ingestion_status",
    "get_bulk_ingestion_status",
]
