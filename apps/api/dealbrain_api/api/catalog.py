from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.schemas import (
    CpuCreate,
    CpuRead,
    GpuCreate,
    GpuRead,
    PortsProfileCreate,
    PortsProfileRead,
    ProfileCreate,
    ProfileRead,
)

from ..db import session_dependency
from ..models import Cpu, Gpu, PortsProfile, Port, Profile

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])


@router.get("/cpus", response_model=list[CpuRead])
async def list_cpus(session: AsyncSession = Depends(session_dependency)) -> Sequence[CpuRead]:
    result = await session.execute(select(Cpu).order_by(Cpu.name))
    return [CpuRead.model_validate(row) for row in result.scalars().all()]


@router.post("/cpus", response_model=CpuRead, status_code=status.HTTP_201_CREATED)
async def create_cpu(payload: CpuCreate, session: AsyncSession = Depends(session_dependency)) -> CpuRead:
    existing = await session.scalar(select(Cpu).where(Cpu.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="CPU already exists")
    cpu = Cpu(**payload.model_dump(exclude_none=True))
    session.add(cpu)
    await session.flush()
    return CpuRead.model_validate(cpu)


@router.get("/gpus", response_model=list[GpuRead])
async def list_gpus(session: AsyncSession = Depends(session_dependency)) -> Sequence[GpuRead]:
    result = await session.execute(select(Gpu).order_by(Gpu.name))
    return [GpuRead.model_validate(row) for row in result.scalars().all()]


@router.post("/gpus", response_model=GpuRead, status_code=status.HTTP_201_CREATED)
async def create_gpu(payload: GpuCreate, session: AsyncSession = Depends(session_dependency)) -> GpuRead:
    existing = await session.scalar(select(Gpu).where(Gpu.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="GPU already exists")
    gpu = Gpu(**payload.model_dump(exclude_none=True))
    session.add(gpu)
    await session.flush()
    return GpuRead.model_validate(gpu)


@router.get("/profiles", response_model=list[ProfileRead])
async def list_profiles(session: AsyncSession = Depends(session_dependency)) -> Sequence[ProfileRead]:
    result = await session.execute(select(Profile).order_by(Profile.name))
    return [ProfileRead.model_validate(row) for row in result.scalars().all()]


@router.post("/profiles", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(payload: ProfileCreate, session: AsyncSession = Depends(session_dependency)) -> ProfileRead:
    existing = await session.scalar(select(Profile).where(Profile.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    if payload.is_default:
        await session.execute(update(Profile).values(is_default=False))
    profile = Profile(**payload.model_dump(exclude_none=True))
    session.add(profile)
    await session.flush()
    return ProfileRead.model_validate(profile)


@router.get("/ports-profiles", response_model=list[PortsProfileRead])
async def list_ports_profiles(session: AsyncSession = Depends(session_dependency)) -> Sequence[PortsProfileRead]:
    result = await session.execute(select(PortsProfile).order_by(PortsProfile.name))
    profiles = result.scalars().unique().all()
    return [PortsProfileRead.model_validate(profile) for profile in profiles]


@router.post("/ports-profiles", response_model=PortsProfileRead, status_code=status.HTTP_201_CREATED)
async def create_ports_profile(
    payload: PortsProfileCreate,
    session: AsyncSession = Depends(session_dependency),
) -> PortsProfileRead:
    existing = await session.scalar(select(PortsProfile).where(PortsProfile.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="Ports profile already exists")
    profile = PortsProfile(**payload.model_dump(exclude={"ports"}, exclude_none=True))
    session.add(profile)
    await session.flush()
    for port in payload.ports or []:
        session.add(Port(**port.model_dump(exclude_none=True), ports_profile_id=profile.id))
    await session.flush()
    await session.refresh(profile)
    return PortsProfileRead.model_validate(profile)
