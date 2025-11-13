---
title: "Deal Builder - Phase 1-3: Backend Database & Service Implementation"
description: "Detailed task breakdown for database schema, repository layer, and business logic service. Covers SavedBuild model, CRUD operations, valuation integration, and metrics calculation."
audience: [ai-agents, developers]
tags: [implementation, database, repository, service, backend, phases-1-3]
created: 2025-11-12
updated: 2025-11-12
category: "product-planning"
status: draft
related:
  - /home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1.md
---

# Phase 1-3: Backend Database, Repository & Service Layer

## Overview

Phases 1-3 establish the data persistence and business logic foundation. This is the critical path for the entire feature - all other phases depend on these layers being stable.

**Timeline**: Days 1-6 (approximately 2 weeks)
**Effort**: 11 story points
**Agents**: data-layer-expert, python-backend-engineer, backend-architect

---

## Phase 1: Database Layer (Days 1-2, 3 story points)

### Task 1.1: Create SavedBuild SQLAlchemy Model

**Assigned to**: data-layer-expert

**Description**: Add SavedBuild ORM model to `apps/api/dealbrain_api/models/core.py` with all required fields, relationships, and soft delete support.

**Technical Details**:

```python
# apps/api/dealbrain_api/models/core.py - Add this class

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Index, func, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets

class SavedBuild(Base):
    """User's saved PC build configuration with pricing and metrics snapshot."""

    __tablename__ = "saved_builds"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # User association (nullable for future multi-user support)
    user_id = Column(String(255), nullable=True, index=True)

    # Build metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=list)
    visibility = Column(String(20), default='private')  # 'private', 'public', 'unlisted'

    # Share token for URL-based access
    share_token = Column(String(64), unique=True, nullable=False, index=True)

    # Component references (foreign keys)
    cpu_id = Column(Integer, ForeignKey('cpus.id'), nullable=True)
    gpu_id = Column(Integer, ForeignKey('gpus.id'), nullable=True)
    ram_spec_id = Column(Integer, ForeignKey('ram_specs.id'), nullable=True)
    primary_storage_profile_id = Column(Integer, ForeignKey('storage_profiles.id'), nullable=True)
    secondary_storage_profile_id = Column(Integer, ForeignKey('storage_profiles.id'), nullable=True)
    ports_profile_id = Column(Integer, ForeignKey('ports_profiles.id'), nullable=True)

    # Pricing snapshot (captured at save time)
    base_price_usd = Column(Numeric(10, 2), nullable=False)
    adjusted_price_usd = Column(Numeric(10, 2), nullable=False)
    component_prices = Column(JSONB, default=dict)  # {"cpu": 189.00, "ram": 45.00, ...}

    # Performance metrics snapshot (captured at save time)
    dollar_per_cpu_mark_multi = Column(Numeric(10, 3), nullable=True)
    dollar_per_cpu_mark_single = Column(Numeric(10, 3), nullable=True)
    composite_score = Column(Numeric(5, 2), nullable=True)

    # Valuation breakdown (full JSON with rule explanations)
    valuation_breakdown = Column(JSONB, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships (for eager loading)
    cpu = relationship("CPU", foreign_keys=[cpu_id], lazy="joined")
    gpu = relationship("GPU", foreign_keys=[gpu_id], lazy="joined")
    ram_spec = relationship("RAMSpec", foreign_keys=[ram_spec_id], lazy="joined")
    primary_storage_profile = relationship("StorageProfile", foreign_keys=[primary_storage_profile_id], lazy="joined")
    secondary_storage_profile = relationship("StorageProfile", foreign_keys=[secondary_storage_profile_id], lazy="joined")

    # Indexes for query optimization
    __table_args__ = (
        Index('idx_user_builds', 'user_id', 'deleted_at'),
        Index('idx_share_token', 'share_token'),
        Index('idx_visibility', 'visibility', 'deleted_at'),
        Index('idx_created_at', 'created_at'),
    )

    @classmethod
    def generate_share_token(cls) -> str:
        """Generate cryptographically secure share token."""
        return secrets.token_urlsafe(32)

    def is_owned_by(self, user_id: str) -> bool:
        """Check if build is owned by user."""
        return self.user_id == user_id

    def is_deleted(self) -> bool:
        """Check if build is soft deleted."""
        return self.deleted_at is not None
```

**Acceptance Criteria**:
- Model class created with all fields listed in PRD
- Relationships defined for CPU, GPU, RAM, Storage profiles
- Soft delete support via deleted_at column
- Indexes defined for user_id, share_token, visibility
- Unique constraint on share_token
- Helper methods (generate_share_token, is_owned_by) included
- Model documented with docstrings

**Files Modified**:
- `apps/api/dealbrain_api/models/core.py` - Add SavedBuild class

**Effort**: 1 story point

---

### Task 1.2: Create Alembic Migration

**Assigned to**: data-layer-expert

**Description**: Generate and test Alembic migration that creates the saved_builds table with correct schema and indexes.

**Technical Details**:

```bash
# Generate migration
poetry run alembic revision --autogenerate -m "Add saved_builds table for Deal Builder"

# This creates: apps/api/alembic/versions/XXXX_add_saved_builds_table.py
```

**Migration File Structure**:
```python
# apps/api/alembic/versions/[timestamp]_add_saved_builds_table.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    op.create_table(
        'saved_builds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), server_default='{}'),
        sa.Column('visibility', sa.String(length=20), server_default='private'),
        sa.Column('share_token', sa.String(length=64), nullable=False),
        sa.Column('cpu_id', sa.Integer(), nullable=True),
        sa.Column('gpu_id', sa.Integer(), nullable=True),
        sa.Column('ram_spec_id', sa.Integer(), nullable=True),
        sa.Column('primary_storage_profile_id', sa.Integer(), nullable=True),
        sa.Column('secondary_storage_profile_id', sa.Integer(), nullable=True),
        sa.Column('ports_profile_id', sa.Integer(), nullable=True),
        sa.Column('base_price_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('adjusted_price_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('component_prices', postgresql.JSONB(), server_default='{}'),
        sa.Column('dollar_per_cpu_mark_multi', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('dollar_per_cpu_mark_single', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('composite_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('valuation_breakdown', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cpu_id'], ['cpus.id'], ),
        sa.ForeignKeyConstraint(['gpu_id'], ['gpus.id'], ),
        sa.ForeignKeyConstraint(['ram_spec_id'], ['ram_specs.id'], ),
        sa.ForeignKeyConstraint(['primary_storage_profile_id'], ['storage_profiles.id'], ),
        sa.ForeignKeyConstraint(['secondary_storage_profile_id'], ['storage_profiles.id'], ),
        sa.ForeignKeyConstraint(['ports_profile_id'], ['ports_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_token'),
    )
    op.create_index('idx_user_builds', 'saved_builds', ['user_id', 'deleted_at'])
    op.create_index('idx_share_token', 'saved_builds', ['share_token'])
    op.create_index('idx_visibility', 'saved_builds', ['visibility', 'deleted_at'])
    op.create_index('idx_created_at', 'saved_builds', ['created_at'])

def downgrade() -> None:
    op.drop_index('idx_created_at', 'saved_builds')
    op.drop_index('idx_visibility', 'saved_builds')
    op.drop_index('idx_share_token', 'saved_builds')
    op.drop_index('idx_user_builds', 'saved_builds')
    op.drop_table('saved_builds')
```

**Testing**:
```bash
# Apply migration
poetry run alembic upgrade head

# Verify table exists
poetry run python -c "from dealbrain_api.db import engine; print(engine.execute('SELECT * FROM saved_builds LIMIT 0;'))"

# Verify indexes exist
SELECT indexname FROM pg_indexes WHERE tablename = 'saved_builds';
```

**Acceptance Criteria**:
- Migration file generated with correct schema
- Migration runs without errors (alembic upgrade head succeeds)
- Table created in database with all columns
- All indexes created
- Unique constraint on share_token enforced
- Downgrade works correctly
- Foreign key constraints validated

**Files Created**:
- `apps/api/alembic/versions/[timestamp]_add_saved_builds_table.py`

**Effort**: 1.5 story points

---

### Task 1.3: Validate Schema & Create Test Fixtures

**Assigned to**: data-layer-expert

**Description**: Verify schema correctness, create test fixtures for seed data, and validate model relationships.

**Technical Details**:

```python
# tests/conftest.py - Add these fixtures

@pytest.fixture
async def saved_build_factory(db_session):
    """Factory for creating test SavedBuild instances."""
    async def _create_build(**kwargs):
        build_data = {
            'name': kwargs.get('name', 'Test Build'),
            'user_id': kwargs.get('user_id', 'test_user'),
            'cpu_id': kwargs.get('cpu_id', 1),
            'base_price_usd': 500.0,
            'adjusted_price_usd': 450.0,
            'component_prices': {'cpu': 189.0, 'ram': 45.0},
            'valuation_breakdown': {'rules': []},
            'share_token': SavedBuild.generate_share_token(),
            'visibility': kwargs.get('visibility', 'public'),
        }
        build = SavedBuild(**build_data)
        db_session.add(build)
        await db_session.commit()
        return build

    return _create_build


@pytest.fixture
async def sample_builds(saved_build_factory):
    """Create sample builds for testing."""
    builds = []
    for i in range(3):
        build = await saved_build_factory(
            name=f'Build {i+1}',
            visibility=['private', 'public', 'unlisted'][i]
        )
        builds.append(build)
    return builds
```

**Validation Tests**:
```python
# tests/test_saved_build_model.py

import pytest
from dealbrain_api.models.core import SavedBuild
from datetime import datetime

@pytest.mark.asyncio
async def test_saved_build_model_creation(db_session):
    """Test SavedBuild model can be created."""
    build = SavedBuild(
        name="Test Build",
        base_price_usd=500.0,
        adjusted_price_usd=450.0,
        valuation_breakdown={},
        share_token=SavedBuild.generate_share_token(),
    )
    db_session.add(build)
    await db_session.commit()

    assert build.id is not None
    assert build.created_at is not None
    assert build.visibility == 'private'

@pytest.mark.asyncio
async def test_share_token_uniqueness(db_session):
    """Test share_token unique constraint."""
    token = SavedBuild.generate_share_token()
    build1 = SavedBuild(
        name="Build 1",
        base_price_usd=500.0,
        adjusted_price_usd=450.0,
        valuation_breakdown={},
        share_token=token,
    )
    db_session.add(build1)
    await db_session.commit()

    # Try to create duplicate - should fail
    build2 = SavedBuild(
        name="Build 2",
        base_price_usd=500.0,
        adjusted_price_usd=450.0,
        valuation_breakdown={},
        share_token=token,
    )
    db_session.add(build2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_soft_delete_tracking(db_session):
    """Test soft delete functionality."""
    build = SavedBuild(
        name="Test",
        base_price_usd=500.0,
        adjusted_price_usd=450.0,
        valuation_breakdown={},
        share_token=SavedBuild.generate_share_token(),
    )
    db_session.add(build)
    await db_session.commit()

    assert build.deleted_at is None
    assert not build.is_deleted()

    # Soft delete
    build.deleted_at = datetime.utcnow()
    await db_session.commit()

    assert build.is_deleted()
```

**Acceptance Criteria**:
- Schema validation passes (column types, constraints)
- Test fixtures can create valid SavedBuild instances
- Unique constraint on share_token prevents duplicates
- Soft delete tracking works correctly
- Relationships load correctly (CPU, GPU, etc.)
- Foreign key constraints enforced
- All validation tests pass

**Files Modified/Created**:
- `tests/conftest.py` - Add fixtures
- `tests/test_saved_build_model.py` - Add validation tests

**Effort**: 0.5 story points

---

## Phase 2: Repository Layer (Days 3-4, 3 story points)

### Task 2.1: Create BuilderRepository CRUD Operations

**Assigned to**: python-backend-engineer

**Description**: Implement BuilderRepository class with Create, Read, Update, Delete operations for SavedBuild.

**Technical Details**:

```python
# apps/api/dealbrain_api/repositories/builder_repository.py (NEW FILE)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List
from datetime import datetime

from ..models.core import SavedBuild


class BuilderRepository:
    """Data access layer for SavedBuild operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        base_price_usd: float,
        adjusted_price_usd: float,
        valuation_breakdown: dict,
        user_id: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: str = 'private',
        cpu_id: Optional[int] = None,
        gpu_id: Optional[int] = None,
        ram_spec_id: Optional[int] = None,
        primary_storage_profile_id: Optional[int] = None,
        secondary_storage_profile_id: Optional[int] = None,
        component_prices: Optional[dict] = None,
        dollar_per_cpu_mark_multi: Optional[float] = None,
        dollar_per_cpu_mark_single: Optional[float] = None,
        composite_score: Optional[float] = None,
    ) -> SavedBuild:
        """Create and persist a new SavedBuild."""
        build = SavedBuild(
            name=name,
            user_id=user_id,
            description=description,
            tags=tags or [],
            visibility=visibility,
            share_token=SavedBuild.generate_share_token(),
            cpu_id=cpu_id,
            gpu_id=gpu_id,
            ram_spec_id=ram_spec_id,
            primary_storage_profile_id=primary_storage_profile_id,
            secondary_storage_profile_id=secondary_storage_profile_id,
            base_price_usd=base_price_usd,
            adjusted_price_usd=adjusted_price_usd,
            component_prices=component_prices or {},
            dollar_per_cpu_mark_multi=dollar_per_cpu_mark_multi,
            dollar_per_cpu_mark_single=dollar_per_cpu_mark_single,
            composite_score=composite_score,
            valuation_breakdown=valuation_breakdown,
        )
        self.session.add(build)
        await self.session.commit()
        await self.session.refresh(build)
        return build

    async def get_by_id(self, build_id: int) -> Optional[SavedBuild]:
        """Get build by ID (excludes soft-deleted)."""
        result = await self.session.execute(
            select(SavedBuild).where(
                SavedBuild.id == build_id,
                SavedBuild.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_share_token(self, share_token: str) -> Optional[SavedBuild]:
        """Get build by share token (public/unlisted only)."""
        result = await self.session.execute(
            select(SavedBuild).where(
                SavedBuild.share_token == share_token,
                SavedBuild.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[SavedBuild], int]:
        """List builds for a user with pagination."""
        # Get count
        count_result = await self.session.execute(
            select(func.count(SavedBuild.id)).where(
                SavedBuild.user_id == user_id,
                SavedBuild.deleted_at.is_(None),
            )
        )
        total = count_result.scalar()

        # Get paginated results
        result = await self.session.execute(
            select(SavedBuild).where(
                SavedBuild.user_id == user_id,
                SavedBuild.deleted_at.is_(None),
            )
            .order_by(desc(SavedBuild.created_at))
            .limit(limit)
            .offset(offset)
        )
        builds = result.scalars().all()

        return builds, total

    async def list_public(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[SavedBuild], int]:
        """List public builds with pagination."""
        # Get count
        count_result = await self.session.execute(
            select(func.count(SavedBuild.id)).where(
                SavedBuild.visibility == 'public',
                SavedBuild.deleted_at.is_(None),
            )
        )
        total = count_result.scalar()

        # Get paginated results
        result = await self.session.execute(
            select(SavedBuild).where(
                SavedBuild.visibility == 'public',
                SavedBuild.deleted_at.is_(None),
            )
            .order_by(desc(SavedBuild.created_at))
            .limit(limit)
            .offset(offset)
        )
        builds = result.scalars().all()

        return builds, total

    async def update(
        self,
        build_id: int,
        **kwargs
    ) -> Optional[SavedBuild]:
        """Update a build's mutable fields."""
        build = await self.get_by_id(build_id)
        if not build:
            return None

        # Only allow certain fields to be updated
        updatable_fields = {'name', 'description', 'tags', 'visibility'}
        for field, value in kwargs.items():
            if field in updatable_fields:
                setattr(build, field, value)

        build.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(build)
        return build

    async def soft_delete(self, build_id: int) -> bool:
        """Soft delete a build."""
        build = await self.get_by_id(build_id)
        if not build:
            return False

        build.deleted_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def hard_delete(self, build_id: int) -> bool:
        """Permanently delete a build (use with caution)."""
        build = await self.get_by_id(build_id)
        if not build:
            return False

        await self.session.delete(build)
        await self.session.commit()
        return True
```

**Acceptance Criteria**:
- All CRUD operations implemented
- Soft delete respected in all queries (deleted_at filter)
- Pagination working correctly (limit, offset, total count)
- Eager loading configured for relationships
- No N+1 queries (verified with sqlalchemy logging)
- Response times <100ms for typical queries
- Proper error handling (None returns for missing records)

**Files Created**:
- `apps/api/dealbrain_api/repositories/builder_repository.py`

**Effort**: 1.5 story points

---

### Task 2.2: Write Repository Tests

**Assigned to**: python-backend-engineer

**Description**: Comprehensive unit tests for all BuilderRepository methods.

**Technical Details**:

```python
# tests/test_builder_repository.py

import pytest
from dealbrain_api.repositories.builder_repository import BuilderRepository
from dealbrain_api.models.core import SavedBuild


@pytest.mark.asyncio
async def test_create_build(db_session):
    """Test creating a new build."""
    repo = BuilderRepository(db_session)

    build = await repo.create(
        name="Test Build",
        base_price_usd=500.0,
        adjusted_price_usd=450.0,
        valuation_breakdown={"rules": []},
        user_id="user123",
        cpu_id=1,
    )

    assert build.id is not None
    assert build.name == "Test Build"
    assert build.share_token is not None
    assert len(build.share_token) > 20  # Token should be substantial


@pytest.mark.asyncio
async def test_list_user_builds_pagination(db_session, saved_build_factory):
    """Test pagination in list_by_user."""
    repo = BuilderRepository(db_session)
    user_id = "user123"

    # Create 5 builds
    for i in range(5):
        await saved_build_factory(name=f"Build {i}", user_id=user_id)

    # Get first page
    builds_p1, total = await repo.list_by_user(user_id, limit=2, offset=0)
    assert len(builds_p1) == 2
    assert total == 5

    # Get second page
    builds_p2, total = await repo.list_by_user(user_id, limit=2, offset=2)
    assert len(builds_p2) == 2

    # Get third page (partial)
    builds_p3, total = await repo.list_by_user(user_id, limit=2, offset=4)
    assert len(builds_p3) == 1


@pytest.mark.asyncio
async def test_soft_delete_hides_from_queries(db_session, saved_build_factory):
    """Test that soft-deleted builds don't appear in queries."""
    repo = BuilderRepository(db_session)
    user_id = "user123"

    build1 = await saved_build_factory(name="Build 1", user_id=user_id)
    build2 = await saved_build_factory(name="Build 2", user_id=user_id)

    builds, total = await repo.list_by_user(user_id)
    assert total == 2

    # Soft delete build1
    await repo.soft_delete(build1.id)

    builds, total = await repo.list_by_user(user_id)
    assert total == 1
    assert builds[0].id == build2.id
```

**Acceptance Criteria**:
- All CRUD operations tested
- Edge cases covered (empty results, pagination bounds)
- Soft delete verified to hide records
- Relationships tested (CPU, GPU loaded correctly)
- Integration with saved_build_factory fixture works
- Test coverage >90% for repository

**Files Created**:
- `tests/test_builder_repository.py`

**Effort**: 1.5 story points

---

## Phase 3: Service Layer (Days 5-6, 5 story points)

### Task 3.1: Create BuilderService Core Methods

**Assigned to**: python-backend-engineer

**Description**: Implement BuilderService orchestrating valuation calculations, metrics, and persistence.

**Technical Details**:

```python
# apps/api/dealbrain_api/services/builder.py (NEW FILE)

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from decimal import Decimal

from ..repositories.builder_repository import BuilderRepository
from ..models.core import SavedBuild, CPU, ApplicationSettings
from dealbrain_core.valuation import apply_valuation_rules
from dealbrain_core.scoring import calculate_composite_score


class BuilderService:
    """Business logic for PC build configuration and valuation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BuilderRepository(db)

    async def calculate_build_valuation(
        self,
        components: Dict[str, Optional[int]],
    ) -> Dict[str, Any]:
        """
        Calculate valuation and metrics for a build.

        Reuses existing valuation logic from packages/core.

        Args:
            components: {
                'cpu_id': int,
                'gpu_id': int,
                'ram_spec_id': int,
                'primary_storage_profile_id': int,
                'secondary_storage_profile_id': int,
            }

        Returns:
            {
                'pricing': {
                    'base_price': float,
                    'adjusted_price': float,
                    'component_prices': dict,
                },
                'metrics': {
                    'dollar_per_cpu_mark_multi': float,
                    'dollar_per_cpu_mark_single': float,
                    'composite_score': float,
                },
                'valuation_breakdown': dict,
            }
        """
        # Validate components exist in database
        cpu = None
        if components.get('cpu_id'):
            from sqlalchemy import select
            result = await self.db.execute(
                select(CPU).where(CPU.id == components['cpu_id'])
            )
            cpu = result.scalar_one_or_none()
            if not cpu:
                raise ValueError(f"CPU {components['cpu_id']} not found")

        # Estimate base prices from components
        component_prices = await self._estimate_component_prices(components)
        base_price = sum(component_prices.values())

        # Get application settings for valuation thresholds
        from sqlalchemy import select
        result = await self.db.execute(select(ApplicationSettings).limit(1))
        settings = result.scalar_one_or_none()

        # Apply valuation rules (reuse existing logic)
        # Create pseudo-listing object for valuation function
        pseudo_listing = {
            'price_usd': base_price,
            'components': components,
        }

        # For now, simple calculation (can be enhanced)
        adjusted_price = base_price

        # In Phase 2, integrate with actual apply_valuation_rules()
        # from dealbrain_core.valuation import apply_valuation_rules
        # adjusted_price = apply_valuation_rules(pseudo_listing, settings)

        # Calculate metrics if CPU present
        metrics = {}
        if cpu and cpu.cpu_mark_multi:
            metrics['dollar_per_cpu_mark_multi'] = float(
                Decimal(str(adjusted_price)) / Decimal(str(cpu.cpu_mark_multi))
            )
            if cpu.cpu_mark_single:
                metrics['dollar_per_cpu_mark_single'] = float(
                    Decimal(str(adjusted_price)) / Decimal(str(cpu.cpu_mark_single))
                )

            # Composite score (basic implementation)
            metrics['composite_score'] = min(100.0, float(cpu.cpu_mark_multi / 30000 * 100))

        return {
            'pricing': {
                'base_price': base_price,
                'adjusted_price': adjusted_price,
                'component_prices': component_prices,
            },
            'metrics': metrics,
            'valuation_breakdown': {
                'components': component_prices,
                'base_total': base_price,
                'adjustments': [],
                'adjusted_total': adjusted_price,
                'rules_applied': 0,
            },
        }

    async def save_build(
        self,
        name: str,
        components: Dict[str, Optional[int]],
        pricing: Dict[str, float],
        metrics: Dict[str, float],
        valuation_breakdown: Dict,
        user_id: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: str = 'private',
    ) -> SavedBuild:
        """
        Save a build configuration with pricing/metrics snapshot.

        Args:
            name: Build name (required)
            components: Component ID dict
            pricing: Pricing snapshot from calculation
            metrics: Metrics snapshot from calculation
            valuation_breakdown: Full breakdown from calculation
            user_id: Owner (optional for MVP)
            description: Build description
            tags: Custom tags
            visibility: 'private', 'public', 'unlisted'

        Returns:
            Saved SavedBuild instance
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Build name is required")

        # Create via repository
        build = await self.repository.create(
            name=name,
            description=description,
            tags=tags or [],
            visibility=visibility,
            user_id=user_id,
            base_price_usd=pricing['base_price'],
            adjusted_price_usd=pricing['adjusted_price'],
            component_prices=pricing.get('component_prices', {}),
            cpu_id=components.get('cpu_id'),
            gpu_id=components.get('gpu_id'),
            ram_spec_id=components.get('ram_spec_id'),
            primary_storage_profile_id=components.get('primary_storage_profile_id'),
            secondary_storage_profile_id=components.get('secondary_storage_profile_id'),
            dollar_per_cpu_mark_multi=metrics.get('dollar_per_cpu_mark_multi'),
            dollar_per_cpu_mark_single=metrics.get('dollar_per_cpu_mark_single'),
            composite_score=metrics.get('composite_score'),
            valuation_breakdown=valuation_breakdown,
        )

        return build

    async def get_build(self, build_id: int) -> Optional[SavedBuild]:
        """Get a single build by ID."""
        return await self.repository.get_by_id(build_id)

    async def get_build_by_share_token(self, share_token: str) -> Optional[SavedBuild]:
        """Get a build by share token (public sharing)."""
        return await self.repository.get_by_share_token(share_token)

    async def list_user_builds(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[SavedBuild], int]:
        """List builds for a user."""
        return await self.repository.list_by_user(user_id, limit, offset)

    async def list_public_builds(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[SavedBuild], int]:
        """List public builds."""
        return await self.repository.list_public(limit, offset)

    async def update_build(
        self,
        build_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        visibility: Optional[str] = None,
    ) -> Optional[SavedBuild]:
        """Update mutable fields of a build."""
        update_dict = {}
        if name is not None:
            update_dict['name'] = name
        if description is not None:
            update_dict['description'] = description
        if tags is not None:
            update_dict['tags'] = tags
        if visibility is not None:
            update_dict['visibility'] = visibility

        return await self.repository.update(build_id, **update_dict)

    async def delete_build(self, build_id: int) -> bool:
        """Soft delete a build."""
        return await self.repository.soft_delete(build_id)

    # Private helper methods

    async def _estimate_component_prices(
        self,
        components: Dict[str, Optional[int]],
    ) -> Dict[str, float]:
        """
        Estimate prices for components.

        In MVP, return placeholder values.
        In Phase 2, query actual pricing from component tables.
        """
        prices = {}

        # CPU
        if cpu_id := components.get('cpu_id'):
            from sqlalchemy import select
            result = await self.db.execute(
                select(CPU).where(CPU.id == cpu_id)
            )
            cpu = result.scalar_one_or_none()
            if cpu and cpu.estimated_price:
                prices['cpu'] = float(cpu.estimated_price)

        # TODO: Add RAM, GPU, Storage prices in Phase 2

        return prices
```

**Acceptance Criteria**:
- All core methods implemented
- calculate_build_valuation returns correct structure
- save_build creates persistent record with snapshot
- get_build and list methods work correctly
- Validation catches invalid inputs
- Error handling with descriptive messages
- Methods properly documented with docstrings

**Files Created**:
- `apps/api/dealbrain_api/services/builder.py`

**Effort**: 3 story points

---

### Task 3.2: Integration Tests & Validation

**Assigned to**: backend-architect

**Description**: Comprehensive tests validating BuilderService calculations match existing valuation system.

**Technical Details**:

```python
# tests/test_builder_service.py

import pytest
from dealbrain_api.services.builder import BuilderService
from decimal import Decimal


@pytest.mark.asyncio
async def test_calculate_build_valuation_basic(db_session):
    """Test basic build valuation calculation."""
    service = BuilderService(db_session)

    components = {
        'cpu_id': 1,
        'ram_spec_id': 1,
        'primary_storage_profile_id': 1,
    }

    result = await service.calculate_build_valuation(components)

    assert 'pricing' in result
    assert 'metrics' in result
    assert 'valuation_breakdown' in result
    assert result['pricing']['adjusted_price'] > 0
    assert result['pricing']['base_price'] > 0


@pytest.mark.asyncio
async def test_save_and_retrieve_build(db_session):
    """Test end-to-end save and retrieve."""
    service = BuilderService(db_session)

    # Calculate
    components = {'cpu_id': 1}
    calc_result = await service.calculate_build_valuation(components)

    # Save
    build = await service.save_build(
        name="Test Build",
        components=components,
        pricing=calc_result['pricing'],
        metrics=calc_result['metrics'],
        valuation_breakdown=calc_result['valuation_breakdown'],
        user_id="test_user",
        visibility="public",
    )

    assert build.id is not None
    assert build.name == "Test Build"
    assert build.share_token is not None

    # Retrieve
    retrieved = await service.get_build(build.id)
    assert retrieved.id == build.id
    assert retrieved.name == "Test Build"

    # Share token lookup
    shared = await service.get_build_by_share_token(build.share_token)
    assert shared.id == build.id


@pytest.mark.asyncio
async def test_metrics_calculation_accuracy(db_session):
    """Test metrics calculation against expected values."""
    service = BuilderService(db_session)

    components = {'cpu_id': 1}
    result = await service.calculate_build_valuation(components)

    # If CPU has CPU Mark data, verify formula
    metrics = result['metrics']
    if 'dollar_per_cpu_mark_multi' in metrics:
        expected = result['pricing']['adjusted_price'] / 30000  # Example CPU Mark
        # Allow small variance due to rounding
        assert abs(metrics['dollar_per_cpu_mark_multi'] - expected) < 0.001


@pytest.mark.asyncio
async def test_build_deletion(db_session):
    """Test soft delete functionality."""
    service = BuilderService(db_session)

    build = await service.save_build(
        name="To Delete",
        components={},
        pricing={'base_price': 100, 'adjusted_price': 100},
        metrics={},
        valuation_breakdown={},
    )

    assert await service.get_build(build.id) is not None

    # Soft delete
    deleted = await service.delete_build(build.id)
    assert deleted is True

    # Should not retrieve after delete
    assert await service.get_build(build.id) is None
```

**Acceptance Criteria**:
- All tests passing
- Calculations within tolerance of expected values (±1%)
- Edge cases covered (no CPU, no components, etc.)
- Integration with repository working correctly
- Error handling tested (invalid IDs, validation failures)
- Database transactions working correctly (commits/rollbacks)

**Files Created**:
- `tests/test_builder_service.py`

**Effort**: 2 story points

---

## Summary: Phase 1-3 Deliverables

| Artifact | File | Status |
|----------|------|--------|
| SavedBuild Model | `apps/api/dealbrain_api/models/core.py` | Ready for implementation |
| Alembic Migration | `apps/api/alembic/versions/[timestamp]_add_saved_builds.py` | Ready for implementation |
| BuilderRepository | `apps/api/dealbrain_api/repositories/builder_repository.py` | Ready for implementation |
| BuilderService | `apps/api/dealbrain_api/services/builder.py` | Ready for implementation |
| Repository Tests | `tests/test_builder_repository.py` | Ready for implementation |
| Service Tests | `tests/test_builder_service.py` | Ready for implementation |
| Model Tests | `tests/test_saved_build_model.py` | Ready for implementation |

## Quality Gates for Phase 1-3 Completion

Before proceeding to Phase 4 (API layer):

- [ ] Migration runs successfully (`alembic upgrade head`)
- [ ] SavedBuild table exists with correct schema
- [ ] All indexes created and working
- [ ] BuilderRepository tests passing (>90% coverage)
- [ ] BuilderService tests passing (>85% coverage)
- [ ] Soft delete working correctly (filters respected)
- [ ] No N+1 queries in service/repository
- [ ] Response times <100ms for typical operations
- [ ] Documentation in docstrings complete
- [ ] Code review approved

---

**Total Effort**: 11 story points
**Timeline**: Days 1-6 (~2 weeks)
**Agents**: data-layer-expert (4pts), python-backend-engineer (6pts), backend-architect (1pt)

Next phase: [Phase 4: API Layer Integration](./phase-4-integration.md)
