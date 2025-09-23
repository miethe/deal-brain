from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..importers import SpreadsheetImporter
from ..models.core import ImportSession
from ..seeds import apply_seed
from ..services.imports import ImportSessionService
from .schemas.imports import (
    CommitImportRequest,
    CommitImportResponse,
    ImportSessionListModel,
    ImportSessionSnapshotModel,
    UpdateMappingsRequest,
)

router = APIRouter(prefix="/v1/imports", tags=["imports"])
service = ImportSessionService()


async def _get_session_or_404(db: AsyncSession, session_id: UUID) -> ImportSession:
    import_session = await db.get(ImportSession, session_id)
    if import_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import session not found")
    return import_session


def _snapshot(import_session: ImportSession) -> ImportSessionSnapshotModel:
    # Accepts a dict or Pydantic model, not ORM object
    return ImportSessionSnapshotModel.model_validate(import_session)


@router.post("/sessions", response_model=ImportSessionSnapshotModel, status_code=status.HTTP_201_CREATED)
async def create_import_session(
    upload: UploadFile = File(...),
    declared_entities: str | None = Form(default=None),
    db: AsyncSession = Depends(session_dependency),
) -> ImportSessionSnapshotModel:
    declared_entities_payload: dict[str, str] = {}
    if declared_entities:
        try:
            payload = json.loads(declared_entities)
            if not isinstance(payload, dict):
                raise ValueError("declared_entities must be an object")
            declared_entities_payload = {str(key): str(value) for key, value in payload.items()}
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    try:
        import_session = await service.create_session(
            db,
            upload=upload,
            declared_entities=declared_entities_payload,
        )
        await service.refresh_preview(db, import_session)
        await db.refresh(import_session)
        # Build dict while still in async context
        payload = {
            "id": import_session.id,
            "filename": import_session.filename,
            "content_type": import_session.content_type,
            "status": import_session.status,
            "checksum": import_session.checksum,
            "sheet_meta": import_session.sheet_meta_json or [],
            "mappings": import_session.mappings_json or {},
            "preview": import_session.preview_json or {},
            "conflicts": import_session.conflicts_json or {},
            "declared_entities": import_session.declared_entities_json or {},
            "created_at": import_session.created_at,
            "updated_at": import_session.updated_at,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _snapshot(payload)


@router.get("/sessions", response_model=ImportSessionListModel)
async def list_import_sessions(db: AsyncSession = Depends(session_dependency)) -> ImportSessionListModel:
    result = await db.execute(select(ImportSession).order_by(ImportSession.created_at.desc()))
    sessions = result.scalars().all()
    session_dicts = [
        {
            "id": session.id,
            "filename": session.filename,
            "content_type": session.content_type,
            "status": session.status,
            "checksum": session.checksum,
            "sheet_meta": session.sheet_meta_json or [],
            "mappings": session.mappings_json or {},
            "preview": session.preview_json or {},
            "conflicts": session.conflicts_json or {},
            "declared_entities": session.declared_entities_json or {},
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }
        for session in sessions
    ]
    return ImportSessionListModel(sessions=[_snapshot(s) for s in session_dicts])


@router.get("/sessions/{session_id}", response_model=ImportSessionSnapshotModel)
async def get_import_session(
    session_id: UUID,
    db: AsyncSession = Depends(session_dependency),
) -> ImportSessionSnapshotModel:
    import_session = await _get_session_or_404(db, session_id)
    await service.refresh_preview(db, import_session)
    await db.refresh(import_session)
    payload = {
        "id": import_session.id,
        "filename": import_session.filename,
        "content_type": import_session.content_type,
        "status": import_session.status,
        "checksum": import_session.checksum,
        "sheet_meta": import_session.sheet_meta_json or [],
        "mappings": import_session.mappings_json or {},
        "preview": import_session.preview_json or {},
        "conflicts": import_session.conflicts_json or {},
        "declared_entities": import_session.declared_entities_json or {},
        "created_at": import_session.created_at,
        "updated_at": import_session.updated_at,
    }
    return _snapshot(payload)


@router.post("/sessions/{session_id}/mappings", response_model=ImportSessionSnapshotModel)
async def update_import_mappings(
    session_id: UUID,
    request: UpdateMappingsRequest,
    db: AsyncSession = Depends(session_dependency),
) -> ImportSessionSnapshotModel:
    import_session = await _get_session_or_404(db, session_id)
    await service.update_mappings(db, import_session, mappings=request.model_dump()["mappings"])
    await service.compute_conflicts(db, import_session)
    await db.refresh(import_session)
    payload = {
        "id": import_session.id,
        "filename": import_session.filename,
        "content_type": import_session.content_type,
        "status": import_session.status,
        "checksum": import_session.checksum,
        "sheet_meta": import_session.sheet_meta_json or [],
        "mappings": import_session.mappings_json or {},
        "preview": import_session.preview_json or {},
        "conflicts": import_session.conflicts_json or {},
        "declared_entities": import_session.declared_entities_json or {},
        "created_at": import_session.created_at,
        "updated_at": import_session.updated_at,
    }
    return _snapshot(payload)


@router.post("/sessions/{session_id}/conflicts", response_model=ImportSessionSnapshotModel)
async def refresh_conflicts(
    session_id: UUID,
    db: AsyncSession = Depends(session_dependency),
) -> ImportSessionSnapshotModel:
    import_session = await _get_session_or_404(db, session_id)
    await service.compute_conflicts(db, import_session)
    await db.refresh(import_session)
    payload = {
        "id": import_session.id,
        "filename": import_session.filename,
        "content_type": import_session.content_type,
        "status": import_session.status,
        "checksum": import_session.checksum,
        "sheet_meta": import_session.sheet_meta_json or [],
        "mappings": import_session.mappings_json or {},
        "preview": import_session.preview_json or {},
        "conflicts": import_session.conflicts_json or {},
        "declared_entities": import_session.declared_entities_json or {},
        "created_at": import_session.created_at,
        "updated_at": import_session.updated_at,
    }
    return _snapshot(payload)


@router.post("/sessions/{session_id}/commit", response_model=CommitImportResponse)
async def commit_import_session(
    session_id: UUID,
    request: CommitImportRequest,
    db: AsyncSession = Depends(session_dependency),
) -> CommitImportResponse:
    import_session = await _get_session_or_404(db, session_id)
    conflict_resolutions = {
        resolution.identifier: resolution.action
        for resolution in request.conflict_resolutions
        if resolution.entity == "cpu"
    }
    component_overrides = {
        override.row_index: {
            "cpu_match": override.cpu_match,
            "gpu_match": override.gpu_match,
        }
        for override in request.component_overrides
    }
    try:
        counts = await service.commit(
            db,
            import_session,
            conflict_resolutions=conflict_resolutions,
            component_overrides=component_overrides,
        )
        await service.refresh_preview(db, import_session)
        await db.refresh(import_session)
        payload = {
            "id": import_session.id,
            "filename": import_session.filename,
            "content_type": import_session.content_type,
            "status": import_session.status,
            "checksum": import_session.checksum,
            "sheet_meta": import_session.sheet_meta_json or [],
            "mappings": import_session.mappings_json or {},
            "preview": import_session.preview_json or {},
            "conflicts": import_session.conflicts_json or {},
            "created_at": import_session.created_at,
            "updated_at": import_session.updated_at,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CommitImportResponse(status="completed", counts=counts, session=_snapshot(payload))


class ImportRequest(BaseModel):
    path: str


class ImportResponse(BaseModel):
    status: str
    path: str
    counts: dict[str, int]


@router.post("/workbook", response_model=ImportResponse, status_code=status.HTTP_200_OK)
async def import_workbook(
    payload: ImportRequest,
) -> ImportResponse:
    path = Path(payload.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Workbook not found at {path}")
    importer = SpreadsheetImporter(path)
    seed, summary = importer.load()
    await apply_seed(seed)
    counts = summary.__dict__
    return ImportResponse(status="completed", path=str(path), counts=counts)
