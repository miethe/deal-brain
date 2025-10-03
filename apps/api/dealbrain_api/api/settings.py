"""Settings API endpoints."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..services.settings import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingResponse(BaseModel):
    """Setting response schema."""
    key: str
    value: dict[str, Any]
    description: str | None = None


class SettingUpdateRequest(BaseModel):
    """Setting update request schema."""
    value: dict[str, Any]
    description: str | None = None


@router.get("/{key}", response_model=dict[str, Any])
async def get_setting(
    key: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a setting by key."""
    service = SettingsService()
    value = await service.get_setting(session, key)

    if value is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    return value


@router.put("/{key}", response_model=dict[str, Any])
async def update_setting(
    key: str,
    request: SettingUpdateRequest,
    session: AsyncSession = Depends(get_session)
):
    """Update or create a setting."""
    service = SettingsService()
    value = await service.update_setting(
        session,
        key,
        request.value,
        request.description
    )
    return value


@router.get("/valuation_thresholds/default", response_model=dict[str, float])
async def get_valuation_thresholds(
    session: AsyncSession = Depends(get_session)
):
    """Get valuation thresholds (backwards compatibility endpoint)."""
    service = SettingsService()
    return await service.get_valuation_thresholds(session)
