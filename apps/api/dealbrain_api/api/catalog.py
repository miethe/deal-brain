from __future__ import annotations

from typing import Sequence

from dealbrain_core.enums import RamGeneration, StorageMedium
from dealbrain_core.schemas import (
    CpuCreate,
    CpuRead,
    CpuUpdate,
    GpuCreate,
    GpuRead,
    GpuUpdate,
    ListingRead,
    PortsProfileCreate,
    PortsProfileRead,
    PortsProfileUpdate,
    ProfileCreate,
    ProfileRead,
    ProfileUpdate,
    RamSpecCreate,
    RamSpecRead,
    RamSpecUpdate,
    StorageProfileCreate,
    StorageProfileRead,
    StorageProfileUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from opentelemetry import trace
from sqlalchemy import String, cast, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..models import Cpu, Gpu, Listing, Port, PortsProfile, Profile, RamSpec, StorageProfile
from ..services.catalog import (
    get_cpu_usage_count,
    get_gpu_usage_count,
    get_ports_profile_usage_count,
    get_ram_spec_usage_count,
    get_scoring_profile_usage_count,
    get_storage_profile_usage_count,
)
from ..services.component_catalog import (
    get_or_create_ram_spec,
    get_or_create_storage_profile,
    normalize_storage_medium,
)

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])
tracer = trace.get_tracer(__name__)


@router.get("/cpus", response_model=list[CpuRead])
async def list_cpus(session: AsyncSession = Depends(session_dependency)) -> Sequence[CpuRead]:
    result = await session.execute(select(Cpu).order_by(Cpu.name))
    return [CpuRead.model_validate(row) for row in result.scalars().all()]


@router.get("/cpus/{cpu_id}", response_model=CpuRead)
async def get_cpu(cpu_id: int, session: AsyncSession = Depends(session_dependency)) -> CpuRead:
    """Get a single CPU by ID."""
    cpu = await session.get(Cpu, cpu_id)
    if not cpu:
        raise HTTPException(status_code=404, detail=f"CPU with id {cpu_id} not found")
    return CpuRead.model_validate(cpu)


@router.post("/cpus", response_model=CpuRead, status_code=status.HTTP_201_CREATED)
async def create_cpu(
    payload: CpuCreate, session: AsyncSession = Depends(session_dependency)
) -> CpuRead:
    existing = await session.scalar(select(Cpu).where(Cpu.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="CPU already exists")

    # Map attributes → attributes_json for model creation
    data = payload.model_dump(exclude_none=True)
    if "attributes" in data:
        data["attributes_json"] = data.pop("attributes")

    cpu = Cpu(**data)
    session.add(cpu)
    await session.flush()
    return CpuRead.model_validate(cpu)


@router.put("/cpus/{cpu_id}", response_model=CpuRead)
async def update_cpu(
    cpu_id: int, payload: CpuUpdate, session: AsyncSession = Depends(session_dependency)
) -> CpuRead:
    """Full update of a CPU entity."""
    with tracer.start_as_current_span("catalog.update_cpu"):
        cpu = await session.get(Cpu, cpu_id)
        if not cpu:
            raise HTTPException(status_code=404, detail=f"CPU with id {cpu_id} not found")

        update_data = payload.model_dump(exclude_unset=True)

        # Check for unique constraint violation if name is being changed
        if "name" in update_data and update_data["name"] != cpu.name:
            existing = await session.scalar(select(Cpu).where(Cpu.name == update_data["name"]))
            if existing:
                raise HTTPException(
                    status_code=422, detail=f"CPU with name '{update_data['name']}' already exists"
                )

        # Update all provided fields
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                # Merge attributes for PUT (replace completely)
                setattr(cpu, "attributes_json", value)
            else:
                setattr(cpu, field if not field.endswith("_json") else field, value)

        await session.flush()
        await session.refresh(cpu)
        return CpuRead.model_validate(cpu)


@router.patch("/cpus/{cpu_id}", response_model=CpuRead)
async def partial_update_cpu(
    cpu_id: int, payload: CpuUpdate, session: AsyncSession = Depends(session_dependency)
) -> CpuRead:
    """Partial update of a CPU entity. Merges attributes_json."""
    with tracer.start_as_current_span("catalog.partial_update_cpu"):
        cpu = await session.get(Cpu, cpu_id)
        if not cpu:
            raise HTTPException(status_code=404, detail=f"CPU with id {cpu_id} not found")

        update_data = payload.model_dump(exclude_unset=True)

        # Check for unique constraint violation if name is being changed
        if "name" in update_data and update_data["name"] != cpu.name:
            existing = await session.scalar(select(Cpu).where(Cpu.name == update_data["name"]))
            if existing:
                raise HTTPException(
                    status_code=422, detail=f"CPU with name '{update_data['name']}' already exists"
                )

        # Update all provided fields with special handling for attributes
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                # Merge attributes for PATCH
                current_attrs = cpu.attributes_json or {}
                merged_attrs = {**current_attrs, **value}
                setattr(cpu, "attributes_json", merged_attrs)
            else:
                setattr(cpu, field if not field.endswith("_json") else field, value)

        await session.flush()
        await session.refresh(cpu)
        return CpuRead.model_validate(cpu)


@router.delete("/cpus/{cpu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cpu(
    cpu_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> Response:
    """Delete a CPU from the catalog.

    Prevents deletion if the CPU is currently used in any listings.
    Returns 409 Conflict if in use, 404 if not found, 204 No Content on success.
    """
    with tracer.start_as_current_span("catalog.delete_cpu"):
        # Get entity
        cpu = await session.get(Cpu, cpu_id)
        if not cpu:
            raise HTTPException(status_code=404, detail=f"CPU with id {cpu_id} not found")

        # Check if in use
        usage_count = await get_cpu_usage_count(session, cpu_id)
        if usage_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete CPU: used in {usage_count} listing(s)"
            )

        # Delete
        await session.delete(cpu)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/gpus", response_model=list[GpuRead])
async def list_gpus(session: AsyncSession = Depends(session_dependency)) -> Sequence[GpuRead]:
    result = await session.execute(select(Gpu).order_by(Gpu.name))
    return [GpuRead.model_validate(row) for row in result.scalars().all()]


@router.get("/gpus/{gpu_id}", response_model=GpuRead)
async def get_gpu(gpu_id: int, session: AsyncSession = Depends(session_dependency)) -> GpuRead:
    """Get a single GPU by ID."""
    gpu = await session.get(Gpu, gpu_id)
    if not gpu:
        raise HTTPException(status_code=404, detail=f"GPU with id {gpu_id} not found")
    return GpuRead.model_validate(gpu)


@router.post("/gpus", response_model=GpuRead, status_code=status.HTTP_201_CREATED)
async def create_gpu(
    payload: GpuCreate, session: AsyncSession = Depends(session_dependency)
) -> GpuRead:
    existing = await session.scalar(select(Gpu).where(Gpu.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="GPU already exists")

    # Map attributes → attributes_json for model creation
    data = payload.model_dump(exclude_none=True)
    if "attributes" in data:
        data["attributes_json"] = data.pop("attributes")

    gpu = Gpu(**data)
    session.add(gpu)
    await session.flush()
    return GpuRead.model_validate(gpu)


@router.put("/gpus/{gpu_id}", response_model=GpuRead)
async def update_gpu(
    gpu_id: int, payload: GpuUpdate, session: AsyncSession = Depends(session_dependency)
) -> GpuRead:
    """Full update of a GPU entity."""
    with tracer.start_as_current_span("catalog.update_gpu"):
        gpu = await session.get(Gpu, gpu_id)
        if not gpu:
            raise HTTPException(status_code=404, detail=f"GPU with id {gpu_id} not found")

        update_data = payload.model_dump(exclude_unset=True)

        # Check for unique constraint violation if name is being changed
        if "name" in update_data and update_data["name"] != gpu.name:
            existing = await session.scalar(select(Gpu).where(Gpu.name == update_data["name"]))
            if existing:
                raise HTTPException(
                    status_code=422, detail=f"GPU with name '{update_data['name']}' already exists"
                )

        # Update all provided fields
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                setattr(gpu, "attributes_json", value)
            else:
                setattr(gpu, field if not field.endswith("_json") else field, value)

        await session.flush()
        await session.refresh(gpu)
        return GpuRead.model_validate(gpu)


@router.patch("/gpus/{gpu_id}", response_model=GpuRead)
async def partial_update_gpu(
    gpu_id: int, payload: GpuUpdate, session: AsyncSession = Depends(session_dependency)
) -> GpuRead:
    """Partial update of a GPU entity. Merges attributes_json."""
    with tracer.start_as_current_span("catalog.partial_update_gpu"):
        gpu = await session.get(Gpu, gpu_id)
        if not gpu:
            raise HTTPException(status_code=404, detail=f"GPU with id {gpu_id} not found")

        update_data = payload.model_dump(exclude_unset=True)

        # Check for unique constraint violation if name is being changed
        if "name" in update_data and update_data["name"] != gpu.name:
            existing = await session.scalar(select(Gpu).where(Gpu.name == update_data["name"]))
            if existing:
                raise HTTPException(
                    status_code=422, detail=f"GPU with name '{update_data['name']}' already exists"
                )

        # Update all provided fields with special handling for attributes
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                current_attrs = gpu.attributes_json or {}
                merged_attrs = {**current_attrs, **value}
                setattr(gpu, "attributes_json", merged_attrs)
            else:
                setattr(gpu, field if not field.endswith("_json") else field, value)

        await session.flush()
        await session.refresh(gpu)
        return GpuRead.model_validate(gpu)


@router.delete("/gpus/{gpu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gpu(
    gpu_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> Response:
    """Delete a GPU from the catalog.

    Prevents deletion if the GPU is currently used in any listings.
    Returns 409 Conflict if in use, 404 if not found, 204 No Content on success.
    """
    with tracer.start_as_current_span("catalog.delete_gpu"):
        # Get entity
        gpu = await session.get(Gpu, gpu_id)
        if not gpu:
            raise HTTPException(status_code=404, detail=f"GPU with id {gpu_id} not found")

        # Check if in use
        usage_count = await get_gpu_usage_count(session, gpu_id)
        if usage_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete GPU: used in {usage_count} listing(s)"
            )

        # Delete
        await session.delete(gpu)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/profiles", response_model=list[ProfileRead])
async def list_profiles(
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ProfileRead]:
    result = await session.execute(select(Profile).order_by(Profile.name))
    return [ProfileRead.model_validate(row) for row in result.scalars().all()]


@router.post("/profiles", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: ProfileCreate, session: AsyncSession = Depends(session_dependency)
) -> ProfileRead:
    existing = await session.scalar(select(Profile).where(Profile.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    if payload.is_default:
        await session.execute(update(Profile).values(is_default=False))

    # No mapping needed for Profile - it uses weights_json directly in schema
    profile = Profile(**payload.model_dump(exclude_none=True))
    session.add(profile)
    await session.flush()
    return ProfileRead.model_validate(profile)


@router.put("/profiles/{profile_id}", response_model=ProfileRead)
async def update_profile(
    profile_id: int, payload: ProfileUpdate, session: AsyncSession = Depends(session_dependency)
) -> ProfileRead:
    """Full update of a Profile entity."""
    with tracer.start_as_current_span("catalog.update_profile"):
        profile = await session.get(Profile, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile with id {profile_id} not found")

        update_data = payload.model_dump(exclude_unset=True)

        # Check for unique constraint violation if name is being changed
        if "name" in update_data and update_data["name"] != profile.name:
            existing = await session.scalar(
                select(Profile).where(Profile.name == update_data["name"])
            )
            if existing:
                raise HTTPException(
                    status_code=422,
                    detail=f"Profile with name '{update_data['name']}' already exists",
                )

        # Prevent removing is_default from the only default profile
        if "is_default" in update_data and not update_data["is_default"] and profile.is_default:
            other_defaults = await session.scalar(
                select(func.count(Profile.id)).where(
                    Profile.is_default.is_(True), Profile.id != profile_id
                )
            )
            if other_defaults == 0:
                raise HTTPException(
                    status_code=422, detail="Cannot unset is_default from the only default profile"
                )

        # If setting is_default, unset others
        if update_data.get("is_default"):
            await session.execute(update(Profile).values(is_default=False))

        # Update all provided fields
        for field, value in update_data.items():
            if field == "weights_json" and value is not None:
                setattr(profile, field, value)
            else:
                setattr(profile, field, value)

        await session.flush()
        await session.refresh(profile)
        return ProfileRead.model_validate(profile)


@router.patch("/profiles/{profile_id}", response_model=ProfileRead)
async def partial_update_profile(
    profile_id: int, payload: ProfileUpdate, session: AsyncSession = Depends(session_dependency)
) -> ProfileRead:
    """Partial update of a Profile entity. Merges weights_json."""
    with tracer.start_as_current_span("catalog.partial_update_profile"):
        profile = await session.get(Profile, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile with id {profile_id} not found")

        update_data = payload.model_dump(exclude_unset=True)

        # Check for unique constraint violation if name is being changed
        if "name" in update_data and update_data["name"] != profile.name:
            existing = await session.scalar(
                select(Profile).where(Profile.name == update_data["name"])
            )
            if existing:
                raise HTTPException(
                    status_code=422,
                    detail=f"Profile with name '{update_data['name']}' already exists",
                )

        # Prevent removing is_default from the only default profile
        if "is_default" in update_data and not update_data["is_default"] and profile.is_default:
            other_defaults = await session.scalar(
                select(func.count(Profile.id)).where(
                    Profile.is_default.is_(True), Profile.id != profile_id
                )
            )
            if other_defaults == 0:
                raise HTTPException(
                    status_code=422, detail="Cannot unset is_default from the only default profile"
                )

        # If setting is_default, unset others
        if update_data.get("is_default"):
            await session.execute(update(Profile).values(is_default=False))

        # Update all provided fields with special handling for weights_json
        for field, value in update_data.items():
            if field == "weights_json" and value is not None:
                # Merge weights for PATCH
                current_weights = profile.weights_json or {}
                merged_weights = {**current_weights, **value}
                setattr(profile, field, merged_weights)
            else:
                setattr(profile, field, value)

        await session.flush()
        await session.refresh(profile)
        return ProfileRead.model_validate(profile)


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> Response:
    """Delete a scoring profile from the catalog.

    Prevents deletion if:
    - The profile is currently used in any listings
    - The profile is marked as default and is the only default profile

    Returns 409 Conflict if in use or only default, 404 if not found, 204 No Content on success.
    """
    with tracer.start_as_current_span("catalog.delete_profile"):
        # Get entity
        profile = await session.get(Profile, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile with id {profile_id} not found")

        # Check if this is the only default profile
        if profile.is_default:
            other_defaults = await session.scalar(
                select(func.count(Profile.id)).where(
                    Profile.is_default.is_(True), Profile.id != profile_id
                )
            )
            if other_defaults == 0:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete the only default profile"
                )

        # Check if in use
        usage_count = await get_scoring_profile_usage_count(session, profile_id)
        if usage_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete Scoring Profile: used in {usage_count} listing(s)"
            )

        # Delete
        await session.delete(profile)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/ports-profiles", response_model=list[PortsProfileRead])
async def list_ports_profiles(
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[PortsProfileRead]:
    result = await session.execute(select(PortsProfile).order_by(PortsProfile.name))
    profiles = result.scalars().unique().all()
    return [PortsProfileRead.model_validate(profile) for profile in profiles]


@router.post(
    "/ports-profiles", response_model=PortsProfileRead, status_code=status.HTTP_201_CREATED
)
async def create_ports_profile(
    payload: PortsProfileCreate,
    session: AsyncSession = Depends(session_dependency),
) -> PortsProfileRead:
    existing = await session.scalar(select(PortsProfile).where(PortsProfile.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail="Ports profile already exists")

    # Map attributes → attributes_json for model creation
    data = payload.model_dump(exclude={"ports"}, exclude_none=True)
    if "attributes" in data:
        data["attributes_json"] = data.pop("attributes")

    profile = PortsProfile(**data)
    session.add(profile)
    await session.flush()
    for port in payload.ports or []:
        session.add(Port(**port.model_dump(exclude_none=True), ports_profile_id=profile.id))
    await session.flush()
    await session.refresh(profile)
    return PortsProfileRead.model_validate(profile)


@router.put("/ports-profiles/{profile_id}", response_model=PortsProfileRead)
async def update_ports_profile(
    profile_id: int,
    payload: PortsProfileUpdate,
    session: AsyncSession = Depends(session_dependency),
) -> PortsProfileRead:
    """Full update of a PortsProfile entity."""
    with tracer.start_as_current_span("catalog.update_ports_profile"):
        profile = await session.get(PortsProfile, profile_id)
        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Ports profile with id {profile_id} not found"
            )

        update_data = payload.model_dump(exclude={"ports"}, exclude_unset=True)

        # Check for unique constraint violation if name is being changed
        if "name" in update_data and update_data["name"] != profile.name:
            existing = await session.scalar(
                select(PortsProfile).where(PortsProfile.name == update_data["name"])
            )
            if existing:
                raise HTTPException(
                    status_code=422,
                    detail=f"Ports profile with name '{update_data['name']}' already exists",
                )

        # Update profile fields
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                setattr(profile, "attributes_json", value)
            else:
                setattr(profile, field, value)

        # Handle ports update (replace all)
        if payload.ports is not None:
            # Delete existing ports
            await session.execute(
                select(Port).where(Port.ports_profile_id == profile_id)
            ).scalars().all()
            for port in profile.ports:
                await session.delete(port)

            # Add new ports
            for port_data in payload.ports:
                session.add(
                    Port(**port_data.model_dump(exclude_none=True), ports_profile_id=profile.id)
                )

        await session.flush()
        await session.refresh(profile)
        return PortsProfileRead.model_validate(profile)


@router.patch("/ports-profiles/{profile_id}", response_model=PortsProfileRead)
async def partial_update_ports_profile(
    profile_id: int,
    payload: PortsProfileUpdate,
    session: AsyncSession = Depends(session_dependency),
) -> PortsProfileRead:
    """Partial update of a PortsProfile entity. Merges attributes_json."""
    with tracer.start_as_current_span("catalog.partial_update_ports_profile"):
        profile = await session.get(PortsProfile, profile_id)
        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Ports profile with id {profile_id} not found"
            )

        update_data = payload.model_dump(exclude={"ports"}, exclude_unset=True)

        # Check for unique constraint violation if name is being changed
        if "name" in update_data and update_data["name"] != profile.name:
            existing = await session.scalar(
                select(PortsProfile).where(PortsProfile.name == update_data["name"])
            )
            if existing:
                raise HTTPException(
                    status_code=422,
                    detail=f"Ports profile with name '{update_data['name']}' already exists",
                )

        # Update profile fields with special handling for attributes
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                current_attrs = profile.attributes_json or {}
                merged_attrs = {**current_attrs, **value}
                setattr(profile, "attributes_json", merged_attrs)
            else:
                setattr(profile, field, value)

        # Handle ports update (replace all if provided)
        if payload.ports is not None:
            # Delete existing ports
            for port in profile.ports:
                await session.delete(port)

            # Add new ports
            for port_data in payload.ports:
                session.add(
                    Port(**port_data.model_dump(exclude_none=True), ports_profile_id=profile.id)
                )

        await session.flush()
        await session.refresh(profile)
        return PortsProfileRead.model_validate(profile)


@router.delete("/ports-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ports_profile(
    profile_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> Response:
    """Delete a ports profile from the catalog.

    Prevents deletion if the ports profile is currently used in any listings.
    Related Port entities will be cascade deleted automatically by the database.

    Returns 409 Conflict if in use, 404 if not found, 204 No Content on success.
    """
    with tracer.start_as_current_span("catalog.delete_ports_profile"):
        # Get entity
        profile = await session.get(PortsProfile, profile_id)
        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Ports profile with id {profile_id} not found"
            )

        # Check if in use
        usage_count = await get_ports_profile_usage_count(session, profile_id)
        if usage_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete Ports Profile: used in {usage_count} listing(s)"
            )

        # Delete (related Port entities will be cascade deleted by the database)
        await session.delete(profile)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/ram-specs", response_model=list[RamSpecRead])
async def list_ram_specs(
    search: str | None = Query(
        default=None, description="Filter by label, generation, or capacity"
    ),
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


@router.get("/ram-specs/{ram_spec_id}", response_model=RamSpecRead)
async def get_ram_spec(
    ram_spec_id: int, session: AsyncSession = Depends(session_dependency)
) -> RamSpecRead:
    """Get a single RAM specification by ID."""
    ram_spec = await session.get(RamSpec, ram_spec_id)
    if not ram_spec:
        raise HTTPException(status_code=404, detail=f"RAM spec with id {ram_spec_id} not found")
    return RamSpecRead.model_validate(ram_spec)


@router.post("/ram-specs", response_model=RamSpecRead, status_code=status.HTTP_201_CREATED)
async def create_ram_spec(
    payload: RamSpecCreate, session: AsyncSession = Depends(session_dependency)
) -> RamSpecRead:
    try:
        spec = await get_or_create_ram_spec(session, payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RamSpecRead.model_validate(spec)


@router.put("/ram-specs/{ram_spec_id}", response_model=RamSpecRead)
async def update_ram_spec(
    ram_spec_id: int, payload: RamSpecUpdate, session: AsyncSession = Depends(session_dependency)
) -> RamSpecRead:
    """Full update of a RamSpec entity."""
    with tracer.start_as_current_span("catalog.update_ram_spec"):
        ram_spec = await session.get(RamSpec, ram_spec_id)
        if not ram_spec:
            raise HTTPException(
                status_code=404, detail=f"RAM spec with id {ram_spec_id} not found"
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Check for unique constraint violation
        # Unique constraint: (ddr_generation, speed_mhz, module_count,
        # capacity_per_module_gb, total_capacity_gb)
        constraint_fields = {
            "ddr_generation": update_data.get("ddr_generation", ram_spec.ddr_generation),
            "speed_mhz": update_data.get("speed_mhz", ram_spec.speed_mhz),
            "module_count": update_data.get("module_count", ram_spec.module_count),
            "capacity_per_module_gb": update_data.get(
                "capacity_per_module_gb", ram_spec.capacity_per_module_gb
            ),
            "total_capacity_gb": update_data.get(
                "total_capacity_gb", ram_spec.total_capacity_gb
            ),
        }

        # Check if any constraint field changed
        constraint_changed = any(
            constraint_fields[field] != getattr(ram_spec, field) for field in constraint_fields
        )

        if constraint_changed:
            existing = await session.scalar(
                select(RamSpec).where(
                    RamSpec.ddr_generation == constraint_fields["ddr_generation"],
                    RamSpec.speed_mhz == constraint_fields["speed_mhz"],
                    RamSpec.module_count == constraint_fields["module_count"],
                    RamSpec.capacity_per_module_gb == constraint_fields["capacity_per_module_gb"],
                    RamSpec.total_capacity_gb == constraint_fields["total_capacity_gb"],
                    RamSpec.id != ram_spec_id,
                )
            )
            if existing:
                raise HTTPException(
                    status_code=422,
                    detail="RAM spec with these specifications already exists",
                )

        # Update all provided fields
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                setattr(ram_spec, "attributes_json", value)
            else:
                setattr(ram_spec, field, value)

        await session.flush()
        await session.refresh(ram_spec)
        return RamSpecRead.model_validate(ram_spec)


@router.patch("/ram-specs/{ram_spec_id}", response_model=RamSpecRead)
async def partial_update_ram_spec(
    ram_spec_id: int, payload: RamSpecUpdate, session: AsyncSession = Depends(session_dependency)
) -> RamSpecRead:
    """Partial update of a RamSpec entity. Merges attributes_json."""
    with tracer.start_as_current_span("catalog.partial_update_ram_spec"):
        ram_spec = await session.get(RamSpec, ram_spec_id)
        if not ram_spec:
            raise HTTPException(
                status_code=404, detail=f"RAM spec with id {ram_spec_id} not found"
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Check for unique constraint violation
        constraint_fields = {
            "ddr_generation": update_data.get("ddr_generation", ram_spec.ddr_generation),
            "speed_mhz": update_data.get("speed_mhz", ram_spec.speed_mhz),
            "module_count": update_data.get("module_count", ram_spec.module_count),
            "capacity_per_module_gb": update_data.get(
                "capacity_per_module_gb", ram_spec.capacity_per_module_gb
            ),
            "total_capacity_gb": update_data.get("total_capacity_gb", ram_spec.total_capacity_gb),
        }

        constraint_changed = any(
            constraint_fields[field] != getattr(ram_spec, field) for field in constraint_fields
        )

        if constraint_changed:
            existing = await session.scalar(
                select(RamSpec).where(
                    RamSpec.ddr_generation == constraint_fields["ddr_generation"],
                    RamSpec.speed_mhz == constraint_fields["speed_mhz"],
                    RamSpec.module_count == constraint_fields["module_count"],
                    RamSpec.capacity_per_module_gb == constraint_fields["capacity_per_module_gb"],
                    RamSpec.total_capacity_gb == constraint_fields["total_capacity_gb"],
                    RamSpec.id != ram_spec_id,
                )
            )
            if existing:
                raise HTTPException(
                    status_code=422,
                    detail="RAM spec with these specifications already exists",
                )

        # Update all provided fields with special handling for attributes
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                current_attrs = ram_spec.attributes_json or {}
                merged_attrs = {**current_attrs, **value}
                setattr(ram_spec, "attributes_json", merged_attrs)
            else:
                setattr(ram_spec, field, value)

        await session.flush()
        await session.refresh(ram_spec)
        return RamSpecRead.model_validate(ram_spec)


@router.delete("/ram-specs/{ram_spec_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ram_spec(
    ram_spec_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> Response:
    """Delete a RAM specification from the catalog.

    Prevents deletion if the RAM spec is currently used in any listings.

    Returns 409 Conflict if in use, 404 if not found, 204 No Content on success.
    """
    with tracer.start_as_current_span("catalog.delete_ram_spec"):
        # Get entity
        ram_spec = await session.get(RamSpec, ram_spec_id)
        if not ram_spec:
            raise HTTPException(
                status_code=404, detail=f"RAM spec with id {ram_spec_id} not found"
            )

        # Check if in use
        usage_count = await get_ram_spec_usage_count(session, ram_spec_id)
        if usage_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete RAM Spec: used in {usage_count} listing(s)"
            )

        # Delete
        await session.delete(ram_spec)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.get("/storage-profiles/{storage_profile_id}", response_model=StorageProfileRead)
async def get_storage_profile(
    storage_profile_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> StorageProfileRead:
    """Get a single storage profile by ID."""
    storage_profile = await session.get(StorageProfile, storage_profile_id)
    if not storage_profile:
        raise HTTPException(
            status_code=404, detail=f"Storage profile with id {storage_profile_id} not found"
        )
    return StorageProfileRead.model_validate(storage_profile)


@router.post(
    "/storage-profiles", response_model=StorageProfileRead, status_code=status.HTTP_201_CREATED
)
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


@router.put("/storage-profiles/{storage_profile_id}", response_model=StorageProfileRead)
async def update_storage_profile(
    storage_profile_id: int,
    payload: StorageProfileUpdate,
    session: AsyncSession = Depends(session_dependency),
) -> StorageProfileRead:
    """Full update of a StorageProfile entity."""
    with tracer.start_as_current_span("catalog.update_storage_profile"):
        storage_profile = await session.get(StorageProfile, storage_profile_id)
        if not storage_profile:
            raise HTTPException(
                status_code=404,
                detail=f"Storage profile with id {storage_profile_id} not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Normalize medium if provided
        if "medium" in update_data and update_data["medium"] is not None:
            update_data["medium"] = normalize_storage_medium(update_data["medium"])

        # Check for unique constraint violation
        # Unique constraint: (medium, interface, form_factor, capacity_gb, performance_tier)
        constraint_fields = {
            "medium": update_data.get("medium", storage_profile.medium),
            "interface": update_data.get("interface", storage_profile.interface),
            "form_factor": update_data.get("form_factor", storage_profile.form_factor),
            "capacity_gb": update_data.get("capacity_gb", storage_profile.capacity_gb),
            "performance_tier": update_data.get(
                "performance_tier", storage_profile.performance_tier
            ),
        }

        constraint_changed = any(
            constraint_fields[field] != getattr(storage_profile, field)
            for field in constraint_fields
        )

        if constraint_changed:
            existing = await session.scalar(
                select(StorageProfile).where(
                    StorageProfile.medium == constraint_fields["medium"],
                    StorageProfile.interface == constraint_fields["interface"],
                    StorageProfile.form_factor == constraint_fields["form_factor"],
                    StorageProfile.capacity_gb == constraint_fields["capacity_gb"],
                    StorageProfile.performance_tier == constraint_fields["performance_tier"],
                    StorageProfile.id != storage_profile_id,
                )
            )
            if existing:
                raise HTTPException(
                    status_code=422,
                    detail="Storage profile with these specifications already exists",
                )

        # Update all provided fields
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                setattr(storage_profile, "attributes_json", value)
            else:
                setattr(storage_profile, field, value)

        await session.flush()
        await session.refresh(storage_profile)
        return StorageProfileRead.model_validate(storage_profile)


@router.patch("/storage-profiles/{storage_profile_id}", response_model=StorageProfileRead)
async def partial_update_storage_profile(
    storage_profile_id: int,
    payload: StorageProfileUpdate,
    session: AsyncSession = Depends(session_dependency),
) -> StorageProfileRead:
    """Partial update of a StorageProfile entity. Merges attributes_json."""
    with tracer.start_as_current_span("catalog.partial_update_storage_profile"):
        storage_profile = await session.get(StorageProfile, storage_profile_id)
        if not storage_profile:
            raise HTTPException(
                status_code=404,
                detail=f"Storage profile with id {storage_profile_id} not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Normalize medium if provided
        if "medium" in update_data and update_data["medium"] is not None:
            update_data["medium"] = normalize_storage_medium(update_data["medium"])

        # Check for unique constraint violation
        constraint_fields = {
            "medium": update_data.get("medium", storage_profile.medium),
            "interface": update_data.get("interface", storage_profile.interface),
            "form_factor": update_data.get("form_factor", storage_profile.form_factor),
            "capacity_gb": update_data.get("capacity_gb", storage_profile.capacity_gb),
            "performance_tier": update_data.get(
                "performance_tier", storage_profile.performance_tier
            ),
        }

        constraint_changed = any(
            constraint_fields[field] != getattr(storage_profile, field)
            for field in constraint_fields
        )

        if constraint_changed:
            existing = await session.scalar(
                select(StorageProfile).where(
                    StorageProfile.medium == constraint_fields["medium"],
                    StorageProfile.interface == constraint_fields["interface"],
                    StorageProfile.form_factor == constraint_fields["form_factor"],
                    StorageProfile.capacity_gb == constraint_fields["capacity_gb"],
                    StorageProfile.performance_tier == constraint_fields["performance_tier"],
                    StorageProfile.id != storage_profile_id,
                )
            )
            if existing:
                raise HTTPException(
                    status_code=422,
                    detail="Storage profile with these specifications already exists",
                )

        # Update all provided fields with special handling for attributes
        for field, value in update_data.items():
            if field == "attributes" and value is not None:
                current_attrs = storage_profile.attributes_json or {}
                merged_attrs = {**current_attrs, **value}
                setattr(storage_profile, "attributes_json", merged_attrs)
            else:
                setattr(storage_profile, field, value)

        await session.flush()
        await session.refresh(storage_profile)
        return StorageProfileRead.model_validate(storage_profile)


@router.delete("/storage-profiles/{storage_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage_profile(
    storage_profile_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> Response:
    """Delete a storage profile from the catalog.

    Prevents deletion if the storage profile is currently used in any listings
    (as either primary or secondary storage).

    Returns 409 Conflict if in use, 404 if not found, 204 No Content on success.
    """
    with tracer.start_as_current_span("catalog.delete_storage_profile"):
        # Get entity
        storage_profile = await session.get(StorageProfile, storage_profile_id)
        if not storage_profile:
            raise HTTPException(
                status_code=404,
                detail=f"Storage profile with id {storage_profile_id} not found"
            )

        # Check if in use (checks both primary and secondary storage)
        usage_count = await get_storage_profile_usage_count(session, storage_profile_id)
        if usage_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete Storage Profile: used in {usage_count} listing(s)"
            )

        # Delete
        await session.delete(storage_profile)
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)


# "Used In" Endpoints - Return listings that use each entity type


@router.get("/cpus/{cpu_id}/listings", response_model=list[ListingRead])
async def get_cpu_listings(
    cpu_id: int,
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum number of listings to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of listings to skip"),
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ListingRead]:
    """Get all listings that use this CPU."""
    # Verify CPU exists
    cpu = await session.get(Cpu, cpu_id)
    if not cpu:
        raise HTTPException(status_code=404, detail=f"CPU with id {cpu_id} not found")

    # Query listings
    stmt = (
        select(Listing)
        .where(Listing.cpu_id == cpu_id)
        .order_by(Listing.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    listings = result.scalars().all()

    return [ListingRead.model_validate(listing) for listing in listings]


@router.get("/gpus/{gpu_id}/listings", response_model=list[ListingRead])
async def get_gpu_listings(
    gpu_id: int,
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum number of listings to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of listings to skip"),
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ListingRead]:
    """Get all listings that use this GPU."""
    # Verify GPU exists
    gpu = await session.get(Gpu, gpu_id)
    if not gpu:
        raise HTTPException(status_code=404, detail=f"GPU with id {gpu_id} not found")

    # Query listings
    stmt = (
        select(Listing)
        .where(Listing.gpu_id == gpu_id)
        .order_by(Listing.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    listings = result.scalars().all()

    return [ListingRead.model_validate(listing) for listing in listings]


@router.get("/ram-specs/{ram_spec_id}/listings", response_model=list[ListingRead])
async def get_ram_spec_listings(
    ram_spec_id: int,
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum number of listings to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of listings to skip"),
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ListingRead]:
    """Get all listings that use this RAM specification."""
    # Verify RAM spec exists
    ram_spec = await session.get(RamSpec, ram_spec_id)
    if not ram_spec:
        raise HTTPException(status_code=404, detail=f"RAM spec with id {ram_spec_id} not found")

    # Query listings
    stmt = (
        select(Listing)
        .where(Listing.ram_spec_id == ram_spec_id)
        .order_by(Listing.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    listings = result.scalars().all()

    return [ListingRead.model_validate(listing) for listing in listings]


@router.get("/storage-profiles/{storage_profile_id}/listings", response_model=list[ListingRead])
async def get_storage_profile_listings(
    storage_profile_id: int,
    limit: int = Query(
        default=50, ge=1, le=100, description="Maximum number of listings to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of listings to skip"),
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[ListingRead]:
    """Get all listings that use this storage profile (either primary or secondary)."""
    # Verify storage profile exists
    storage_profile = await session.get(StorageProfile, storage_profile_id)
    if not storage_profile:
        raise HTTPException(
            status_code=404, detail=f"Storage profile with id {storage_profile_id} not found"
        )

    # Query listings (check both primary and secondary storage)
    stmt = (
        select(Listing)
        .where(
            or_(
                Listing.primary_storage_profile_id == storage_profile_id,
                Listing.secondary_storage_profile_id == storage_profile_id,
            )
        )
        .order_by(Listing.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    listings = result.scalars().all()

    return [ListingRead.model_validate(listing) for listing in listings]
