from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, or_, select, update
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
    RamSpecCreate,
    RamSpecRead,
    StorageProfileCreate,
    StorageProfileRead,
)
from dealbrain_core.enums import RamGeneration, StorageMedium

from ..db import session_dependency
from ..models import Cpu, Gpu, PortsProfile, Port, Profile, RamSpec, StorageProfile
from ..services.component_catalog import (
    get_or_create_ram_spec,
    get_or_create_storage_profile,
    normalize_storage_medium,
)

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


@router.get("/ram-specs", response_model=list[RamSpecRead])
async def list_ram_specs(
    search: str | None = Query(default=None, description="Filter by label, generation, or capacity"),
    generation: RamGeneration | None = Query(default=None, description="Filter by RAM generation"),
    min_capacity_gb: int | None = Query(default=None, ge=0),
    max_capacity_gb: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[RamSpecRead]:
    stmt = select(RamSpec)
    if generation:
        stmt = stmt.where(RamSpec.ddr_generation == generation)
    if min_capacity_gb is not None:
        stmt = stmt.where(RamSpec.total_capacity_gb >= min_capacity_gb)
    if max_capacity_gb is not None:
        stmt = stmt.where(RamSpec.total_capacity_gb <= max_capacity_gb)
    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(RamSpec.label).like(term),
                func.lower(cast(RamSpec.ddr_generation, String)).like(term),
                func.cast(RamSpec.total_capacity_gb, String).like(term),
            )
        )
    stmt = stmt.order_by(
        RamSpec.total_capacity_gb.desc().nulls_last(),
        RamSpec.speed_mhz.desc().nulls_last(),
        RamSpec.updated_at.desc(),
    )
    result = await session.execute(stmt.limit(limit))
    specs = result.scalars().unique().all()
    return [RamSpecRead.model_validate(spec) for spec in specs]


@router.post("/ram-specs", response_model=RamSpecRead, status_code=status.HTTP_201_CREATED)
async def create_ram_spec(payload: RamSpecCreate, session: AsyncSession = Depends(session_dependency)) -> RamSpecRead:
    try:
        spec = await get_or_create_ram_spec(session, payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RamSpecRead.model_validate(spec)


@router.get("/storage-profiles", response_model=list[StorageProfileRead])
async def list_storage_profiles(
    search: str | None = Query(default=None, description="Filter by label, interface, or capacity"),
    medium: StorageMedium | None = Query(default=None, description="Filter by storage medium"),
    min_capacity_gb: int | None = Query(default=None, ge=0),
    max_capacity_gb: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[StorageProfileRead]:
    stmt = select(StorageProfile)
    if medium:
        stmt = stmt.where(StorageProfile.medium == medium)
    if min_capacity_gb is not None:
        stmt = stmt.where(StorageProfile.capacity_gb >= min_capacity_gb)
    if max_capacity_gb is not None:
        stmt = stmt.where(StorageProfile.capacity_gb <= max_capacity_gb)
    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(StorageProfile.label).like(term),
                func.lower(cast(StorageProfile.medium, String)).like(term),
                func.lower(StorageProfile.interface).like(term),
                func.lower(StorageProfile.form_factor).like(term),
                func.cast(StorageProfile.capacity_gb, String).like(term),
            )
        )
    stmt = stmt.order_by(
        StorageProfile.capacity_gb.desc().nulls_last(),
        StorageProfile.medium.asc(),
        StorageProfile.updated_at.desc(),
    )
    result = await session.execute(stmt.limit(limit))
    profiles = result.scalars().unique().all()
    return [StorageProfileRead.model_validate(profile) for profile in profiles]


@router.post("/storage-profiles", response_model=StorageProfileRead, status_code=status.HTTP_201_CREATED)
async def create_storage_profile(
    payload: StorageProfileCreate,
    session: AsyncSession = Depends(session_dependency),
) -> StorageProfileRead:
    data = payload.model_dump(exclude_none=True)
    if "medium" in data and data["medium"] is not None:
        data["medium"] = normalize_storage_medium(data["medium"])
    try:
        profile = await get_or_create_storage_profile(session, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StorageProfileRead.model_validate(profile)
