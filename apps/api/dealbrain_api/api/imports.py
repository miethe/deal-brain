from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..seeds import apply_seed
from ..importers import SpreadsheetImporter

router = APIRouter(prefix="/v1/imports", tags=["imports"])


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

