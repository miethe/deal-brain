from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field

from ..tasks.admin import (
    import_entities_task,
    import_passmark_task,
    recalculate_cpu_mark_metrics_task,
    recalculate_metrics_task,
)
from ..tasks.valuation import recalculate_listings_task
from ..worker import celery_app

router = APIRouter(prefix="/v1/admin", tags=["admin"])

try:  # pragma: no cover - optional admin dependency
    from ..auth import require_admin  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - fallback when auth not wired

    async def require_admin() -> None:
        return None


class TaskSubmissionResponse(BaseModel):
    task_id: str
    action: str
    status: str = "queued"
    message: str | None = None
    metadata: dict[str, Any] | None = None


class ValuationRecalcRequest(BaseModel):
    listing_ids: list[int] | None = Field(
        default=None, description="Specific listing IDs to recalculate"
    )
    ruleset_id: int | None = Field(default=None, description="Override ruleset when recalculating")
    batch_size: int = Field(default=100, ge=1, le=1000)
    include_inactive: bool = False
    reason: str | None = None


class MetricsRecalcRequest(BaseModel):
    listing_ids: list[int] | None = Field(
        default=None, description="Specific listing IDs to update"
    )


class TaskStatusResponse(BaseModel):
    task_id: str
    action: str | None
    status: str
    state: str
    result: Any | None = None
    error: str | None = None


@router.post("/tasks/recalculate-valuations", response_model=TaskSubmissionResponse)
async def trigger_valuation_recalc(
    request: ValuationRecalcRequest,
    _user=Depends(require_admin),
) -> TaskSubmissionResponse:
    payload = request.model_dump()
    async_result = recalculate_listings_task.delay(**payload)
    return TaskSubmissionResponse(
        task_id=async_result.id,
        action=recalculate_listings_task.name,
        metadata={"requested_ids": request.listing_ids, "reason": request.reason},
    )


@router.post("/tasks/recalculate-metrics", response_model=TaskSubmissionResponse)
async def trigger_metric_recalc(
    request: MetricsRecalcRequest,
    _user=Depends(require_admin),
) -> TaskSubmissionResponse:
    payload = request.model_dump()
    async_result = recalculate_metrics_task.delay(payload.get("listing_ids"))
    return TaskSubmissionResponse(
        task_id=async_result.id,
        action=recalculate_metrics_task.name,
        metadata={"requested_ids": request.listing_ids},
    )


@router.post("/tasks/recalculate-cpu-marks", response_model=TaskSubmissionResponse)
async def trigger_cpu_mark_recalc(
    request: MetricsRecalcRequest,
    _user=Depends(require_admin),
) -> TaskSubmissionResponse:
    payload = request.model_dump()
    async_result = recalculate_cpu_mark_metrics_task.delay(payload.get("listing_ids"))
    return TaskSubmissionResponse(
        task_id=async_result.id,
        action=recalculate_cpu_mark_metrics_task.name,
        metadata={"requested_ids": request.listing_ids},
    )


@router.post("/tasks/import-passmark", response_model=TaskSubmissionResponse)
async def trigger_passmark_import(
    upload: UploadFile = File(...),
    _user=Depends(require_admin),
) -> TaskSubmissionResponse:
    suffix = Path(upload.filename or "passmark").suffix or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="passmark-") as handle:
        handle.write(await upload.read())
        temp_path = handle.name

    async_result = import_passmark_task.delay(temp_path)
    return TaskSubmissionResponse(
        task_id=async_result.id,
        action=import_passmark_task.name,
        metadata={"filename": upload.filename},
    )


@router.post("/tasks/import-entities", response_model=TaskSubmissionResponse)
async def trigger_entity_import(
    entity: str = Form(...),
    dry_run: bool = Form(False),
    upload: UploadFile = File(...),
    _user=Depends(require_admin),
) -> TaskSubmissionResponse:
    suffix = Path(upload.filename or entity).suffix or ".json"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=f"{entity}-") as handle:
        handle.write(await upload.read())
        temp_path = handle.name

    async_result = import_entities_task.delay(entity, temp_path, dry_run)
    return TaskSubmissionResponse(
        task_id=async_result.id,
        action=import_entities_task.name,
        metadata={"entity": entity, "dry_run": dry_run, "filename": upload.filename},
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, _user=Depends(require_admin)) -> TaskStatusResponse:
    async_result = celery_app.AsyncResult(task_id)
    action = async_result.name or async_result.task_name
    status_value = async_result.status
    state = async_result.state
    error: str | None = None
    result: Any | None = None

    if async_result.ready():
        try:
            result = async_result.get(timeout=0)
        except Exception as exc:  # pragma: no cover - surface background errors
            error = str(exc)
            status_value = "FAILURE"

    return TaskStatusResponse(
        task_id=task_id,
        action=action,
        status=status_value,
        state=state,
        result=result,
        error=error,
    )
