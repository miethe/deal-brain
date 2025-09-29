import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

try:  # pragma: no cover - conditional dependency for local test harness
    import aiosqlite  # type: ignore  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ImportError:  # pragma: no cover - executed only when optional dep missing
    AIOSQLITE_AVAILABLE = False


@pytest.fixture
def anyio_backend():  # pragma: no cover - test configuration helper
    return "asyncio"


from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.core import CustomFieldAuditLog, Listing
from apps.api.dealbrain_api.services.custom_fields import CustomFieldService, FieldDependencyError


@pytest.mark.anyio("asyncio")
async def test_field_dependency_guardrails_and_audit():
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    service = CustomFieldService()

    async with async_session() as session:
        listing = Listing(
            title="Test listing",
            price_usd=100.0,
            attributes_json={"warranty": "Yes"},
        )
        session.add(listing)
        await session.commit()

        field = await service.create_field(
            session,
            entity="listing",
            key="warranty",
            label="Warranty",
            data_type="string",
            created_by="tests",
        )
        await session.commit()

        usage = await service.field_usage(session, field)
        assert usage.total == 1

        with pytest.raises(FieldDependencyError):
            await service.delete_field(session, field_id=field.id)

        deleted_usage = await service.delete_field(session, field_id=field.id, force=True)
        assert deleted_usage.total == 1
        await session.commit()

        events = await service.history(session, field_id=field.id)
        assert len(events) >= 2
        assert {event.action for event in events} >= {"created", "soft_deleted"}

        audit_records = (
            await session.execute(select(CustomFieldAuditLog).where(CustomFieldAuditLog.field_id == field.id))
        ).scalars().all()
        assert audit_records
