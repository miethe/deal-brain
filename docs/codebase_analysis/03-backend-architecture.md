# Backend Architecture Documentation

## Overview

The Deal Brain backend is built on FastAPI with SQLAlchemy 2.0 async ORM, following a layered architecture pattern with clear separation of concerns. The system emphasizes domain logic reusability, async patterns, and explainable pricing adjustments.

## 1. Application Structure

### 1.1 FastAPI Application Creation

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/app.py`

```python
def create_app() -> FastAPI:
    """Create and configure the FastAPI app instance."""
    settings = get_settings()
    app = FastAPI(
        title="Deal Brain API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware - allows all origins in development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Prometheus metrics instrumentation
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    # Include all API routers
    app.include_router(api_router)

    return app
```

**Key Features:**
- Factory pattern for app creation
- Automatic API documentation at `/docs` and `/redoc`
- Prometheus metrics exposed at `/metrics`
- Health check endpoint for orchestration
- Centralized middleware configuration

### 1.2 Settings Management

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/settings.py`

Uses `pydantic-settings` for environment-based configuration:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment & Logging
    environment: str = "development"
    log_level: str = "INFO"

    # Database URLs
    database_url: str  # async: postgresql+asyncpg://...
    sync_database_url: str | None = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # File Storage
    import_root: Path = PROJECT_ROOT / "data" / "imports"
    export_root: Path = PROJECT_ROOT / "data" / "exports"
    upload_root: Path = PROJECT_ROOT / "data" / "uploads"

    # Security
    secret_key: str = "changeme"

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Observability
    prometheus_enabled: bool = True
    otel_exporter_otlp_endpoint: str | None = None

    # Feature Flags
    analytics_enabled: bool = True

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
```

**Best Practices:**
- Singleton pattern via `@lru_cache` for settings
- Type hints for all configuration values
- Sensible defaults for development
- Path resolution relative to project root

### 1.3 Middleware Stack

The application applies middleware in this order:

1. **CORS Middleware** - Cross-origin resource sharing (permissive in development)
2. **Prometheus Instrumentator** - Request/response metrics collection

Future middleware considerations:
- Authentication/authorization middleware
- Rate limiting
- Request ID tracking
- Structured logging middleware

## 2. API Layer

### 2.1 Route Organization

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/`

API routes are organized by domain with a centralized router:

```python
# apps/api/dealbrain_api/api/__init__.py
router = APIRouter()
router.include_router(admin.router)
router.include_router(baseline.router)
router.include_router(catalog.router)
router.include_router(listings.router)
router.include_router(rankings.router)
router.include_router(dashboard.router)
router.include_router(health.router)
router.include_router(imports.router)
router.include_router(fields.router)
router.include_router(custom_fields.router)
router.include_router(field_data.router)
router.include_router(metrics.router)
router.include_router(rules.router)
router.include_router(entities.router)
router.include_router(settings.router)
```

### 2.2 Key Endpoints

#### 2.2.1 Listings API (`/v1/listings`)

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/listings.py`

**Core Operations:**
- `GET /v1/listings` - List all listings with pagination
- `POST /v1/listings` - Create new listing with components
- `GET /v1/listings/{listing_id}` - Get single listing
- `PUT /v1/listings/{listing_id}` - Full update with components
- `PATCH /v1/listings/{listing_id}` - Partial field updates
- `GET /v1/listings/schema` - Dynamic schema (core + custom fields)

**Valuation Management:**
- `GET /v1/listings/{listing_id}/valuation-breakdown` - Detailed breakdown
- `PATCH /v1/listings/{listing_id}/valuation-overrides` - Override ruleset selection
- `POST /v1/listings/{listing_id}/recalculate-metrics` - Force recalculation

**Bulk Operations:**
- `POST /v1/listings/bulk-update` - Update multiple listings
- `POST /v1/listings/bulk-recalculate-metrics` - Recalculate many listings

**Ports Management:**
- `POST /v1/listings/{listing_id}/ports` - Update ports data
- `GET /v1/listings/{listing_id}/ports` - Get ports data

**Example: Valuation Breakdown Response**

```python
@router.get("/{listing_id}/valuation-breakdown", response_model=ValuationBreakdownResponse)
async def get_valuation_breakdown(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> ValuationBreakdownResponse:
    """Get detailed valuation breakdown for a listing."""
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    breakdown = listing.valuation_breakdown or {}

    # Parse adjustments from JSON breakdown
    adjustments = []
    for payload in breakdown.get("adjustments", []):
        actions = [
            ValuationAdjustmentAction(
                action_type=action.get("action_type"),
                metric=action.get("metric"),
                value=float(action.get("value") or 0.0),
                details=action.get("details"),
            )
            for action in payload.get("actions", [])
        ]
        adjustments.append(
            ValuationAdjustmentDetail(
                rule_id=payload.get("rule_id"),
                rule_name=payload.get("rule_name"),
                adjustment_amount=float(payload.get("adjustment_usd") or 0.0),
                actions=actions,
            )
        )

    return ValuationBreakdownResponse(
        listing_id=listing.id,
        base_price_usd=float(listing.price_usd),
        adjusted_price_usd=float(listing.adjusted_price_usd or listing.price_usd),
        total_adjustment=float(breakdown.get("total_adjustment", 0)),
        adjustments=adjustments,
    )
```

#### 2.2.2 Catalog API (`/v1/catalog`)

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/catalog.py`

Manages component catalogs and profiles:

**CPU Management:**
- `GET /v1/catalog/cpus` - List all CPUs
- `POST /v1/catalog/cpus` - Create CPU entry

**GPU Management:**
- `GET /v1/catalog/gpus` - List all GPUs
- `POST /v1/catalog/gpus` - Create GPU entry

**Profile Management:**
- `GET /v1/catalog/profiles` - List scoring profiles
- `POST /v1/catalog/profiles` - Create profile with weights

**RAM Specifications:**
- `GET /v1/catalog/ram-specs` - List RAM specs with search/filtering
- `POST /v1/catalog/ram-specs` - Create/get-or-create RAM spec

**Storage Profiles:**
- `GET /v1/catalog/storage-profiles` - List storage profiles
- `POST /v1/catalog/storage-profiles` - Create/get-or-create storage profile

**Ports Profiles:**
- `GET /v1/catalog/ports-profiles` - List ports profiles
- `POST /v1/catalog/ports-profiles` - Create ports profile with port definitions

**Example: RAM Spec Search**

```python
@router.get("/ram-specs", response_model=list[RamSpecRead])
async def list_ram_specs(
    search: str | None = Query(None, description="Filter by label, generation, or capacity"),
    generation: RamGeneration | None = Query(None),
    min_capacity_gb: int | None = Query(None, ge=0),
    max_capacity_gb: int | None = Query(None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(session_dependency),
) -> Sequence[RamSpecRead]:
    stmt = select(RamSpec)

    # Apply filters
    if generation:
        stmt = stmt.where(RamSpec.ddr_generation == generation)
    if min_capacity_gb is not None:
        stmt = stmt.where(RamSpec.total_capacity_gb >= min_capacity_gb)
    if max_capacity_gb is not None:
        stmt = stmt.where(RamSpec.total_capacity_gb <= max_capacity_gb)

    # Full-text search across multiple fields
    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(RamSpec.label).like(term),
                func.lower(cast(RamSpec.ddr_generation, String)).like(term),
                func.cast(RamSpec.total_capacity_gb, String).like(term),
            )
        )

    # Order by capacity and speed
    stmt = stmt.order_by(
        RamSpec.total_capacity_gb.desc().nulls_last(),
        RamSpec.speed_mhz.desc().nulls_last(),
        RamSpec.updated_at.desc(),
    )

    result = await session.execute(stmt.limit(limit))
    specs = result.scalars().unique().all()
    return [RamSpecRead.model_validate(spec) for spec in specs]
```

#### 2.2.3 Rules API (`/api/v1`)

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/rules.py`

Comprehensive valuation rules management with three-tier hierarchy:

**Ruleset Endpoints:**
- `POST /rulesets` - Create new ruleset
- `GET /rulesets` - List all rulesets (with active filter)
- `GET /rulesets/{ruleset_id}` - Get ruleset with nested groups/rules
- `PUT /rulesets/{ruleset_id}` - Update ruleset
- `DELETE /rulesets/{ruleset_id}` - Delete ruleset (cascades)

**Rule Group Endpoints:**
- `POST /rule-groups` - Create rule group
- `GET /rule-groups` - List groups (filter by ruleset/category)
- `GET /rule-groups/{group_id}` - Get group with rules
- `PUT /rule-groups/{group_id}` - Update group

**Rule Endpoints:**
- `POST /valuation-rules` - Create rule with conditions/actions
- `GET /valuation-rules` - List rules (filter by group/active)
- `GET /valuation-rules/{rule_id}` - Get rule details
- `PUT /valuation-rules/{rule_id}` - Update rule
- `DELETE /valuation-rules/{rule_id}` - Delete rule

**Evaluation & Preview:**
- `POST /valuation-rules/preview` - Preview rule impact before saving
- `POST /valuation-rules/evaluate/{listing_id}` - Evaluate single listing
- `POST /valuation-rules/apply` - Apply ruleset to listings

**Packaging (Import/Export):**
- `POST /rulesets/{ruleset_id}/package` - Export ruleset as `.dbrs` file
- `POST /rulesets/install` - Install `.dbrs` package
- `POST /rulesets/{ruleset_id}/package/preview` - Preview export contents

**Audit:**
- `GET /valuation-rules/audit-log` - Get audit history

**Example: Rule Creation**

```python
@router.post("/valuation-rules", response_model=RuleResponse)
async def create_rule(
    request: RuleCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new valuation rule with conditions and actions."""
    service = RulesService()

    # Validate parent group exists
    group = await service.get_rule_group(session, request.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Rule group not found")

    # Validate modifiers JSON for each action
    if request.actions:
        for action in request.actions:
            validate_modifiers_json(action.modifiers, action.action_type)

    # Convert Pydantic models to dicts
    conditions = [c.dict() for c in request.conditions] if request.conditions else []
    actions = [a.dict() for a in request.actions] if request.actions else []

    try:
        rule = await service.create_rule(
            session=session,
            group_id=request.group_id,
            name=request.name,
            description=request.description,
            priority=request.priority,
            evaluation_order=request.evaluation_order,
            conditions=conditions,
            actions=actions,
            metadata=request.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RuleResponse(
        id=rule.id,
        group_id=rule.group_id,
        name=rule.name,
        conditions=request.conditions,
        actions=request.actions,
        metadata=rule.metadata_json,
    )
```

#### 2.2.4 Baseline API (`/api/v1/baseline`)

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/baseline.py`

Manages baseline valuation system with version control:

**Core Endpoints:**
- `GET /baseline/meta` - Get active baseline metadata (field definitions)
- `POST /baseline/instantiate` - Create ruleset from baseline JSON (idempotent)
- `POST /baseline/diff` - Compare candidate baseline against current
- `POST /baseline/adopt` - Adopt selected changes, create new version

**Override Management (Stub):**
- `GET /baseline/overrides/{entity_key}` - Get entity overrides
- `POST /baseline/overrides` - Create/update override
- `DELETE /baseline/overrides/{entity_key}/{field_name}` - Delete field override
- `DELETE /baseline/overrides/{entity_key}` - Delete all entity overrides

**Utilities:**
- `GET /baseline/preview` - Preview override impact
- `GET /baseline/export` - Export current baseline with overrides
- `POST /baseline/validate` - Validate baseline JSON structure

#### 2.2.5 Dashboard API (`/v1/dashboard`)

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/dashboard.py`

Provides aggregated KPI data:

```python
@router.get("", response_model=dict)
async def dashboard(
    budget: float = Query(default=400.0),
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    """Get dashboard KPIs: best value, best perf/watt, best under budget."""
    top_value = await _fetch_listing(session, Listing.dollar_per_cpu_mark, asc)
    top_perf_watt = await _fetch_listing(session, Listing.perf_per_watt, desc)
    under_budget = await _fetch_under_budget(session, budget)

    return {
        "best_value": ListingRead.model_validate(top_value).model_dump() if top_value else None,
        "best_perf_per_watt": ListingRead.model_validate(top_perf_watt).model_dump() if top_perf_watt else None,
        "best_under_budget": [ListingRead.model_validate(item).model_dump() for item in under_budget],
    }
```

### 2.3 Request/Response Schemas

All API schemas use **Pydantic v2** models from `dealbrain_core.schemas`:

**Location**: `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/`

**Key Schema Modules:**
- `listing.py` - ListingCreate, ListingRead, ListingUpdate
- `catalog.py` - CpuCreate, CpuRead, GpuCreate, RamSpecCreate, etc.
- `baseline.py` - BaselineMetadataResponse, BaselineAdoptRequest, etc.
- `imports.py` - SpreadsheetSeed, ImportJob schemas

**Schema Best Practices:**
```python
class ListingCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    listing_url: str | None = None
    price_usd: float
    condition: Condition = Condition.USED
    status: ListingStatus = ListingStatus.ACTIVE

    # Foreign keys
    cpu_id: int | None = None
    gpu_id: int | None = None
    ram_spec_id: int | None = None

    # Components (nested)
    components: list[ListingComponentCreate] | None = None

    # Validation
    @field_validator('price_usd')
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v
```

## 3. Service Layer

The service layer orchestrates business logic, database operations, and domain logic.

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/`

### 3.1 Listings Service

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/listings.py`

**Core Responsibilities:**
- Listing CRUD operations
- Component synchronization
- Metrics calculation (CPU Mark efficiency, GPU scores)
- Valuation rule application
- Performance metric recalculation

**Key Functions:**

```python
async def create_listing(
    session: AsyncSession,
    payload: dict[str, Any]
) -> Listing:
    """Create a new listing with normalized payload."""
    payload = _normalize_listing_payload(payload)
    await _prepare_component_relationships(session, payload)

    # Filter to mutable fields only
    fields = {k: v for k, v in payload.items() if k in MUTABLE_LISTING_FIELDS}

    listing = Listing(**fields)
    session.add(listing)
    await session.flush()
    return listing


async def apply_listing_metrics(
    session: AsyncSession,
    listing: Listing
) -> Listing:
    """Calculate and apply all valuation and performance metrics."""
    # 1. Apply valuation rules
    evaluation_service = RuleEvaluationService()
    evaluation = await evaluation_service.evaluate_listing(
        session,
        listing.id,
        ruleset_id=listing.ruleset_id
    )

    # Update adjusted price and breakdown
    listing.adjusted_price_usd = evaluation["adjusted_price_usd"]
    listing.valuation_breakdown = evaluation["breakdown"]

    # 2. Calculate performance metrics
    if listing.cpu and listing.cpu.cpu_mark_multi:
        listing.dollar_per_cpu_mark = (
            listing.adjusted_price_usd / listing.cpu.cpu_mark_multi
        )

    # 3. Calculate composite score
    metrics = ListingMetrics(
        cpu_multi_score=listing.score_cpu_multi,
        cpu_single_score=listing.score_cpu_single,
        gpu_score=listing.score_gpu,
    )
    listing.score_composite = compute_composite_score(metrics, weights)

    await session.flush()
    return listing
```

**Bulk Operations:**

```python
async def bulk_update_listing_metrics(
    session: AsyncSession,
    listing_ids: list[int] | None = None
) -> int:
    """Recalculate metrics for multiple listings."""
    stmt = select(Listing.id).order_by(Listing.id)
    if listing_ids:
        stmt = stmt.where(Listing.id.in_(listing_ids))

    count = 0
    async for listing_id in await session.stream_scalars(stmt):
        try:
            await update_listing_metrics(session, listing_id)
            count += 1
        except Exception as exc:
            logger.exception(f"Failed to update listing {listing_id}", exc_info=exc)

    await session.commit()
    return count
```

### 3.2 Rules Service

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/rules.py`

**Responsibilities:**
- Ruleset/group/rule CRUD
- Condition/action validation
- Version management
- Audit logging
- Automatic recalculation triggers

**Key Methods:**

```python
class RulesService:
    def __init__(self, *, trigger_recalculation: bool = True):
        """Initialize with optional recalculation suppression."""
        self._trigger_recalculation = trigger_recalculation

    async def create_ruleset(
        self,
        session: AsyncSession,
        name: str,
        description: str | None = None,
        version: str = "1.0.0",
        conditions: dict[str, Any] | None = None,
        is_active: bool = True,
    ) -> ValuationRuleset:
        """Create a new valuation ruleset."""
        # Validate condition structure
        if conditions:
            build_condition_from_dict(conditions)

        ruleset = ValuationRuleset(
            name=name,
            description=description,
            version=version,
            conditions_json=conditions or {},
            is_active=is_active,
        )

        session.add(ruleset)
        await session.commit()
        await session.refresh(ruleset)

        # Audit trail
        await self._audit_action(
            session,
            rule_id=None,
            action="ruleset_created",
            changes={"ruleset_id": ruleset.id, "name": name}
        )

        # Trigger recalculation if enabled
        if self._trigger_recalculation:
            enqueue_listing_recalculation(
                ruleset_id=ruleset.id,
                reason="ruleset_created"
            )

        return ruleset

    async def create_rule(
        self,
        session: AsyncSession,
        group_id: int,
        name: str,
        conditions: list[dict[str, Any]],
        actions: list[dict[str, Any]],
        priority: int = 100,
    ) -> ValuationRuleV2:
        """Create a rule with conditions and actions."""
        # Validate group exists
        group = await self.get_rule_group(session, group_id)
        if not group:
            raise ValueError("Rule group not found")

        # Create rule
        rule = ValuationRuleV2(
            group_id=group_id,
            name=name,
            priority=priority,
        )
        session.add(rule)
        await session.flush()

        # Create conditions
        for cond_data in conditions:
            condition = ValuationRuleCondition(
                rule_id=rule.id,
                field_name=cond_data["field_name"],
                field_type=cond_data["field_type"],
                operator=cond_data["operator"],
                value_json=cond_data["value"],
            )
            session.add(condition)

        # Create actions
        for action_data in actions:
            action = ValuationRuleAction(
                rule_id=rule.id,
                action_type=action_data["action_type"],
                metric=action_data.get("metric"),
                value_usd=action_data.get("value_usd"),
                modifiers_json=action_data.get("modifiers", {}),
            )
            session.add(action)

        await session.commit()
        await session.refresh(rule)
        return rule
```

### 3.3 Rule Evaluation Service

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/rule_evaluation.py`

**Responsibilities:**
- Evaluate rules against listing context
- Apply actions (adjustments, deductions)
- Generate valuation breakdown
- Prometheus metrics instrumentation

**Evaluation Flow:**

```python
class RuleEvaluationService:
    def __init__(self):
        self.evaluator = RuleEvaluator()  # Core domain evaluator
        self._cache = {}  # Simple in-memory cache

    async def evaluate_listing(
        self,
        session: AsyncSession,
        listing_id: int,
        ruleset_id: int | None = None
    ) -> dict[str, Any]:
        """Evaluate listing against rulesets."""
        # 1. Load listing with relationships
        listing = await session.get(
            Listing,
            listing_id,
            options=[
                selectinload(Listing.cpu),
                selectinload(Listing.gpu),
                selectinload(Listing.ram_spec),
                selectinload(Listing.primary_storage_profile),
            ]
        )

        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # 2. Build evaluation context
        context = build_context_from_listing(listing)

        # 3. Get applicable rulesets
        if ruleset_id:
            rulesets = [await self._get_ruleset(session, ruleset_id)]
        else:
            rulesets = await self._get_rulesets_for_evaluation(
                session,
                context,
                disabled_rulesets=listing.attributes_json.get("valuation_disabled_rulesets", [])
            )

        # 4. Evaluate each ruleset in priority order
        total_adjustment = 0.0
        adjustments = []

        for ruleset in rulesets:
            rules = await self._get_rules_from_ruleset(session, ruleset.id)

            # Evaluate rules with timing
            with valuation_evaluation_duration.labels(ruleset_name=ruleset.name).time():
                evaluation_results = self.evaluator.evaluate_ruleset(rules, context)

            # Process results
            for result in evaluation_results:
                if result["matched"]:
                    adjustment = self._calculate_adjustment(result, listing)
                    total_adjustment += adjustment
                    adjustments.append({
                        "rule_id": result["rule_id"],
                        "rule_name": result["rule_name"],
                        "adjustment_usd": adjustment,
                        "actions": result["actions"],
                    })

        # 5. Return breakdown
        return {
            "listing_id": listing_id,
            "base_price_usd": listing.price_usd,
            "adjusted_price_usd": listing.price_usd + total_adjustment,
            "total_adjustment": total_adjustment,
            "adjustments": adjustments,
            "breakdown": {
                "ruleset": {"id": rulesets[0].id, "name": rulesets[0].name},
                "adjustments": adjustments,
                "total_adjustment": total_adjustment,
            }
        }
```

### 3.4 Component Catalog Service

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/component_catalog.py`

**Responsibilities:**
- Get-or-create pattern for RAM specs and storage profiles
- Normalization of storage medium types
- Label generation for specifications

**Key Functions:**

```python
async def get_or_create_ram_spec(
    session: AsyncSession,
    payload: dict[str, Any]
) -> RamSpec:
    """Get existing or create new RAM spec (idempotent)."""
    # Normalize payload
    normalized = normalize_ram_spec_payload(
        payload,
        fallback_total_gb=payload.get("total_capacity_gb"),
        fallback_generation=payload.get("ddr_generation"),
        fallback_speed=payload.get("speed_mhz"),
    )

    if not normalized:
        raise ValueError("Insufficient RAM spec data")

    # Check for existing spec
    stmt = select(RamSpec).where(
        RamSpec.ddr_generation == normalized["ddr_generation"],
        RamSpec.speed_mhz == normalized["speed_mhz"],
        RamSpec.total_capacity_gb == normalized["total_capacity_gb"],
    )

    existing = await session.scalar(stmt)
    if existing:
        return existing

    # Create new spec
    spec = RamSpec(**normalized)
    session.add(spec)
    await session.flush()
    return spec
```

### 3.5 Baseline Loader Service

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/baseline_loader.py`

**Responsibilities:**
- Load baseline rulesets from JSON files
- Idempotent instantiation (hash-based deduplication)
- Diff calculation between baselines
- Selective adoption of changes
- Version management

**Key Methods:**

```python
class BaselineLoaderService:
    async def load_from_path(
        self,
        session: AsyncSession,
        source_path: Path,
        actor: str = "system",
        ensure_basic_for_ruleset: int | None = None,
    ) -> LoadResult:
        """Load baseline from JSON file (idempotent)."""
        # 1. Read and hash file
        content = source_path.read_text()
        source_hash = hashlib.sha256(content.encode()).hexdigest()
        baseline_data = json.loads(content)

        # 2. Check if already loaded
        existing = await session.scalar(
            select(ValuationRuleset).where(
                ValuationRuleset.metadata_json["source_hash"].astext == source_hash
            )
        )

        if existing:
            return LoadResult(
                status="skipped",
                ruleset_id=existing.id,
                source_hash=source_hash,
                skipped_reason="ruleset_with_hash_exists",
            )

        # 3. Create ruleset
        ruleset = await self._create_baseline_ruleset(
            session,
            baseline_data,
            source_hash,
            actor
        )

        return LoadResult(
            status="created",
            ruleset_id=ruleset.id,
            source_hash=source_hash,
            created_groups=len(ruleset.rule_groups),
            created_rules=sum(len(g.rules) for g in ruleset.rule_groups),
        )

    async def diff_baseline(
        self,
        session: AsyncSession,
        candidate_json: dict[str, Any],
    ) -> BaselineDiffResponse:
        """Compare candidate baseline against current active baseline."""
        # Get current baseline
        current = await self.get_active_baseline(session)
        if not current:
            return BaselineDiffResponse(
                added_fields=list(candidate_json.get("fields", {}).keys()),
                changed_fields=[],
                removed_fields=[],
            )

        # Extract field metadata
        current_fields = current.metadata_json.get("fields", {})
        candidate_fields = candidate_json.get("fields", {})

        # Calculate diff
        added = set(candidate_fields.keys()) - set(current_fields.keys())
        removed = set(current_fields.keys()) - set(candidate_fields.keys())
        changed = []

        for key in set(current_fields.keys()) & set(candidate_fields.keys()):
            if current_fields[key] != candidate_fields[key]:
                changed.append(key)

        return BaselineDiffResponse(
            added_fields=list(added),
            changed_fields=changed,
            removed_fields=list(removed),
        )
```

### 3.6 Custom Fields Service

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/custom_fields.py`

**Responsibilities:**
- Dynamic field definition management
- Field value CRUD operations
- Type validation
- Dropdown option management

## 4. Database Layer

### 4.1 SQLAlchemy 2.0 Async Configuration

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/db.py`

```python
class Base(DeclarativeBase):
    pass

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

def get_engine() -> AsyncEngine:
    """Return singleton async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True
        )
    return _engine

def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return configured session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False
        )
    return _session_factory

@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide transactional scope for async operations."""
    session = get_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def session_dependency() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for injecting sessions."""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

**Key Patterns:**
- Singleton engine and session factory
- `session_scope()` for service-layer operations
- `session_dependency()` for FastAPI route injection
- Automatic commit on success, rollback on error
- `expire_on_commit=False` to avoid lazy-load issues after commit

### 4.2 Database Models

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`

**Model Hierarchy:**

```
TimestampMixin (created_at, updated_at)
  ├── Cpu (name, manufacturer, benchmark scores)
  ├── Gpu (name, manufacturer, gpu_mark)
  ├── RamSpec (generation, speed, capacity)
  ├── StorageProfile (medium, interface, capacity)
  ├── Profile (scoring weights)
  ├── PortsProfile (port definitions)
  │     └── Port (type, count, spec_notes)
  ├── ValuationRuleset (name, version, priority, conditions)
  │     └── ValuationRuleGroup (category, display_order, weight)
  │           └── ValuationRuleV2 (name, priority, evaluation_order)
  │                 ├── ValuationRuleCondition (field, operator, value)
  │                 ├── ValuationRuleAction (action_type, metric, value)
  │                 ├── ValuationRuleVersion (snapshot_json)
  │                 └── ValuationRuleAudit (action, actor, changes)
  └── Listing (price, condition, adjusted_price, breakdown)
        ├── ListingComponent (type, quantity, unit_value)
        └── ListingScoreSnapshot (profile, metrics)
```

**Key Model: Listing**

```python
class Listing(Base, TimestampMixin):
    __tablename__ = "listing"

    # Identity
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Pricing
    price_usd: Mapped[float] = mapped_column(nullable=False)
    adjusted_price_usd: Mapped[float | None]
    valuation_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Status
    condition: Mapped[str] = mapped_column(String(16), default=Condition.USED.value)
    status: Mapped[str] = mapped_column(String(16), default=ListingStatus.ACTIVE.value)

    # Foreign Keys
    cpu_id: Mapped[int | None] = mapped_column(ForeignKey("cpu.id"))
    gpu_id: Mapped[int | None] = mapped_column(ForeignKey("gpu.id"))
    ram_spec_id: Mapped[int | None] = mapped_column(ForeignKey("ram_spec.id"))
    primary_storage_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("storage_profile.id", ondelete="SET NULL")
    )
    ruleset_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_ruleset.id"))

    # Denormalized Fields (from specs)
    ram_gb: Mapped[int] = mapped_column(default=0)
    primary_storage_gb: Mapped[int] = mapped_column(default=0)
    primary_storage_type: Mapped[str | None] = mapped_column(String(64))

    # Performance Metrics
    score_cpu_multi: Mapped[float | None]
    score_cpu_single: Mapped[float | None]
    score_gpu: Mapped[float | None]
    score_composite: Mapped[float | None]
    dollar_per_cpu_mark: Mapped[float | None]

    # JSON Fields
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    other_urls: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)

    # Relationships
    cpu: Mapped["Cpu | None"] = relationship(back_populates="listings", lazy="selectin")
    gpu: Mapped["Gpu | None"] = relationship(back_populates="listings", lazy="selectin")
    ram_spec: Mapped["RamSpec | None"] = relationship(back_populates="listings", lazy="selectin")
    primary_storage_profile: Mapped["StorageProfile | None"] = relationship(...)
    ruleset: Mapped["ValuationRuleset | None"] = relationship(...)
```

**Relationship Loading Strategies:**
- `lazy="selectin"` - Eager load in separate query (N+1 prevention)
- Explicit `selectinload()` in queries for fine-grained control
- `expire_on_commit=False` to avoid extra queries after commit

### 4.3 Alembic Migrations

**Location**: `/mnt/containers/deal-brain/apps/api/alembic/`

**Configuration**: `alembic.ini` at project root

**Creating Migrations:**

```bash
# Auto-generate migration from model changes
poetry run alembic revision --autogenerate -m "Add baseline metadata fields"

# Apply migrations
make migrate
# or
poetry run alembic upgrade head

# Rollback one version
poetry run alembic downgrade -1
```

**Migration Best Practices:**
- Always review auto-generated migrations
- Add data migrations separately (not in schema changes)
- Use batch operations for large tables
- Test migrations against production-like data volumes
- Never delete migrations that have been deployed

**Example Migration:**

```python
"""Add valuation_breakdown JSON column

Revision ID: abc123def456
Create Date: 2024-10-12 10:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'abc123def456'
down_revision = 'xyz789abc123'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('listing',
        sa.Column('valuation_breakdown',
                  postgresql.JSON(astext_type=sa.Text()),
                  nullable=True)
    )

def downgrade():
    op.drop_column('listing', 'valuation_breakdown')
```

## 5. Background Tasks

### 5.1 Celery Worker Configuration

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/worker.py`

```python
from celery import Celery

celery_app = Celery("dealbrain")
celery_app.config_from_object({
    "broker_url": "redis://redis:6379/0",
    "result_backend": "redis://redis:6379/0",
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
})

# Simple health check task
@celery_app.task
def ping() -> str:
    return "pong"

# Import task modules to register with Celery
from .tasks import valuation as _valuation_tasks
```

**Starting Worker:**

```bash
# Via Docker Compose
make up

# Manual (for debugging)
poetry run celery -A dealbrain_api.worker worker --loglevel=info
```

### 5.2 Task Types

#### Bulk Recalculation Task

**Location**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/valuation.py`

```python
@celery_app.task(name="valuation.recalculate_listings", bind=True)
def recalculate_listings_task(
    self,
    *,
    listing_ids: Iterable[int | str | None] | None = None,
    ruleset_id: int | None = None,
    batch_size: int = 100,
    include_inactive: bool = False,
    reason: str | None = None,
) -> dict[str, int]:
    """Celery task for bulk listing valuation recalculation."""
    normalized_ids = _normalize_listing_ids(listing_ids)

    logger.info(
        "Starting valuation recalculation",
        extra={
            "requested_ids": len(normalized_ids) or "all",
            "ruleset_id": ruleset_id,
            "reason": reason,
        },
    )

    # Run async logic in event loop
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            _recalculate_listings_async(
                listing_ids=normalized_ids or None,
                ruleset_id=ruleset_id,
                batch_size=batch_size,
                include_inactive=include_inactive,
            )
        )
    finally:
        asyncio.set_event_loop(None)

async def _recalculate_listings_async(
    *,
    listing_ids: Sequence[int] | None = None,
    batch_size: int = 100,
) -> dict[str, int]:
    """Async implementation of bulk recalculation."""
    counters = {"processed": 0, "succeeded": 0, "failed": 0}

    async with session_scope() as session:
        stmt = select(Listing.id).order_by(Listing.id)
        if listing_ids:
            stmt = stmt.where(Listing.id.in_(listing_ids))

        # Stream IDs and process in batches
        ids_batch = []
        async for listing_id in await session.stream_scalars(stmt):
            ids_batch.append(listing_id)
            if len(ids_batch) >= batch_size:
                await _process_batch(session, ids_batch, counters)
                ids_batch = []

        # Process remaining
        if ids_batch:
            await _process_batch(session, ids_batch, counters)

        await session.commit()

    return counters
```

**Enqueuing Tasks:**

```python
def enqueue_listing_recalculation(
    *,
    listing_ids: Iterable[int] | None = None,
    ruleset_id: int | None = None,
    reason: str | None = None,
    use_celery: bool = True,
) -> None:
    """Schedule listing valuation recalculation."""
    payload = {
        "listing_ids": list(listing_ids) if listing_ids else None,
        "ruleset_id": ruleset_id,
        "reason": reason,
    }

    try:
        if use_celery:
            recalculate_listings_task.delay(**payload)
            logger.debug("Queued valuation recalculation", extra=payload)
            return
    except Exception as exc:
        logger.warning("Falling back to synchronous recalculation", exc_info=exc)

    # Synchronous fallback (for tests/dev)
    recalculate_listings_task(**payload)
```

## 6. Best Practices

### 6.1 Async Patterns

**Always Use Async/Await:**

```python
# Good
async def get_listing(session: AsyncSession, listing_id: int) -> Listing | None:
    result = await session.execute(select(Listing).where(Listing.id == listing_id))
    return result.scalar_one_or_none()

# Bad - blocking in async context
def get_listing_sync(session: Session, listing_id: int) -> Listing:
    return session.query(Listing).filter(Listing.id == listing_id).first()
```

**Use `selectinload()` for Relationships:**

```python
# Good - single query per relationship
stmt = (
    select(Listing)
    .options(
        selectinload(Listing.cpu),
        selectinload(Listing.gpu),
        selectinload(Listing.ram_spec),
    )
    .where(Listing.id == listing_id)
)
listing = await session.scalar(stmt)

# Bad - N+1 queries
listing = await session.get(Listing, listing_id)
cpu_name = listing.cpu.name  # Triggers lazy load
```

**Stream Large Result Sets:**

```python
# Good - memory-efficient streaming
async with session_scope() as session:
    stmt = select(Listing.id).order_by(Listing.id)
    async for listing_id in await session.stream_scalars(stmt):
        process(listing_id)

# Bad - loads all into memory
listings = await session.execute(select(Listing))
for listing in listings.scalars().all():
    process(listing)
```

### 6.2 Error Handling

**Structured Exception Handling:**

```python
@router.post("/listings", response_model=ListingRead)
async def create_listing_endpoint(
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    try:
        listing = await create_listing(session, payload.model_dump())
        await session.commit()
        return ListingRead.model_validate(listing)
    except ValueError as exc:
        # Client errors (400)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        # Constraint violations (409)
        await session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate entry") from exc
    except Exception as exc:
        # Unexpected errors (500)
        logger.exception("Failed to create listing", exc_info=exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Internal error") from exc
```

**Custom Exceptions:**

```python
class RuleEvaluationError(Exception):
    """Raised when rule evaluation fails."""
    pass

class BaselineConflictError(Exception):
    """Raised when baseline changes conflict."""
    pass
```

### 6.3 Transaction Management

**Use Dependency Injection for Routes:**

```python
# Good - automatic commit/rollback
@router.post("/listings")
async def create_listing(
    payload: ListingCreate,
    session: AsyncSession = Depends(session_dependency),  # Managed by dependency
):
    listing = await create_listing_service(session, payload)
    # Commit handled by session_dependency on success
    return listing
```

**Use `session_scope()` for Services:**

```python
# Good - explicit transaction control
async def batch_import_listings(listings_data: list[dict]) -> int:
    async with session_scope() as session:
        count = 0
        for data in listings_data:
            listing = Listing(**data)
            session.add(listing)
            count += 1
        # Commit handled by context manager
        return count
```

**Nested Transactions (Savepoints):**

```python
async def update_listing_with_fallback(session: AsyncSession, listing_id: int):
    async with session.begin_nested():  # Savepoint
        try:
            listing = await session.get(Listing, listing_id)
            await apply_complex_update(session, listing)
        except Exception:
            # Rollback to savepoint, outer transaction continues
            raise
```

### 6.4 Dependency Injection

**Session Dependency:**

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import session_dependency

@router.get("/listings/{listing_id}")
async def get_listing(
    listing_id: int,
    session: AsyncSession = Depends(session_dependency),
) -> ListingRead:
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Not found")
    return ListingRead.model_validate(listing)
```

**Settings Dependency:**

```python
from fastapi import Depends
from ..settings import Settings, get_settings

@router.get("/config")
async def get_config(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "environment": settings.environment,
        "analytics_enabled": settings.analytics_enabled,
    }
```

**Custom Service Dependencies:**

```python
def get_rules_service() -> RulesService:
    return RulesService(trigger_recalculation=True)

@router.post("/rules")
async def create_rule(
    request: RuleCreateRequest,
    service: RulesService = Depends(get_rules_service),
    session: AsyncSession = Depends(session_dependency),
):
    return await service.create_rule(session, request)
```

## 7. Performance Considerations

### 7.1 Database Query Optimization

**Indexes:**
- Ensure indexes on foreign keys
- Add indexes for frequently filtered columns (status, created_at)
- Use covering indexes for common query patterns

**Query Patterns:**
```python
# Efficient: Single query with joins
stmt = (
    select(Listing)
    .join(Listing.cpu)
    .join(Listing.gpu)
    .where(Cpu.cpu_mark_multi > 10000)
    .options(selectinload(Listing.ram_spec))
)

# Avoid: Multiple separate queries
listings = await session.execute(select(Listing).where(...))
for listing in listings.scalars():
    cpu = await session.get(Cpu, listing.cpu_id)  # N+1 problem
```

### 7.2 Caching Strategy

**In-Memory Caching (Service Layer):**
```python
class RuleEvaluationService:
    def __init__(self):
        self._cache = {}  # TODO: Replace with Redis

    async def get_ruleset_cached(self, session: AsyncSession, ruleset_id: int):
        cache_key = f"ruleset:{ruleset_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        ruleset = await session.get(ValuationRuleset, ruleset_id)
        self._cache[cache_key] = ruleset
        return ruleset
```

**Redis Integration (Future):**
- Cache catalog data (CPUs, GPUs, profiles)
- Cache ruleset hierarchies
- Invalidate on updates

### 7.3 Monitoring & Observability

**Prometheus Metrics:**
- Request duration histograms
- Database connection pool metrics
- Rule evaluation timings
- Cache hit rates

**Structured Logging:**
```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Valuation recalculation complete",
    extra={
        "processed": counters["processed"],
        "succeeded": counters["succeeded"],
        "failed": counters["failed"],
        "duration_ms": duration,
    },
)
```

## Summary

The Deal Brain backend follows a clean, layered architecture:

1. **Application Layer** - FastAPI app with middleware, settings, and routing
2. **API Layer** - RESTful endpoints organized by domain
3. **Service Layer** - Business logic orchestration and transaction management
4. **Database Layer** - SQLAlchemy async ORM with migrations
5. **Background Tasks** - Celery workers for bulk operations

**Key Strengths:**
- Async-first design for high concurrency
- Clear separation of concerns (API → Service → Domain → Database)
- Comprehensive rule evaluation with explainability
- Type safety with Pydantic schemas
- Observability with Prometheus metrics

**File Reference:**
- App: `/mnt/containers/deal-brain/apps/api/dealbrain_api/app.py`
- Settings: `/mnt/containers/deal-brain/apps/api/dealbrain_api/settings.py`
- Database: `/mnt/containers/deal-brain/apps/api/dealbrain_api/db.py`
- Models: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`
- API Routes: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/`
- Services: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/`
- Tasks: `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/`
