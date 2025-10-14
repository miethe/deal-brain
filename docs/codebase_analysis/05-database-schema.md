# Database Schema Documentation

## Overview

Deal Brain uses **PostgreSQL 15** with **SQLAlchemy 2.0 (async)** and **Alembic** for migrations. The database architecture supports:

- Component-based PC listing management
- Three-tier valuation rule system (Ruleset → Group → Rule)
- Dynamic custom fields for extensibility
- Performance metrics tracking
- Audit logging for rule changes and baseline operations
- Port/connectivity profiles
- RAM and storage specifications

### Technology Stack

- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0 with async support (`asyncpg` driver)
- **Migrations**: Alembic (19 migrations as of Oct 2025)
- **Connection**: Async engine with session factory pattern
- **URL Format**: `postgresql+asyncpg://user:pass@host:port/db`

---

## Database Configuration

### Connection Management

```python
# apps/api/dealbrain_api/db.py

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def get_engine() -> AsyncEngine:
    """Singleton async engine."""
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=False, future=True)

def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Configured session factory."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)

@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Transactional scope for async operations."""
    session = get_session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

**Key Features**:
- Singleton engine pattern for connection pooling
- `expire_on_commit=False` prevents detached instance errors
- Context manager for automatic transaction handling
- Dependency injection support for FastAPI routes

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VALUATION SYSTEM                                   │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│ ValuationRuleset │ → RuleGroup      │ → RuleV2         │ → Condition/Action │
│   (id, name,     │   (id, name,     │   (id, name,     │   (conditions,     │
│    version,      │    category,     │    priority,     │    actions,        │
│    is_active,    │    weight,       │    is_active,    │    versions,       │
│    priority)     │    display_order)│    eval_order)   │    audit_logs)     │
└──────────────────┴──────────────────┴──────────────────┴────────────────────┘
         │                                                          ▲
         │ ruleset_id                                               │ rule_id
         ▼                                                          │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            LISTING (Core Entity)                             │
├───────────────┬──────────────┬──────────────┬──────────────┬────────────────┤
│ Listing       │              │              │              │                │
│  id (PK)      │ cpu_id (FK)  │ gpu_id (FK)  │ ruleset_id   │ profile_id (FK)│
│  title        │              │              │ (FK)         │                │
│  price_usd    ├──────────────┼──────────────┼──────────────┼────────────────┤
│  adjusted_    │ ram_spec_id  │ primary_     │ secondary_   │ ports_profile_ │
│   price_usd   │ (FK)         │ storage_     │ storage_     │  id (FK)       │
│  condition    │              │ profile_id   │ profile_id   │                │
│  status       │              │ (FK)         │ (FK)         │                │
│  device_model │              │              │              │                │
│  manufacturer │              │              │              │                │
│  series       │              │              │              │                │
│  model_number │              │              │              │                │
│  form_factor  │              │              │              │                │
└───────────────┴──────────────┴──────────────┴──────────────┴────────────────┘
    │           │              │              │              │
    │           ▼              ▼              ▼              ▼
    │       ┌──────┐    ┌──────────┐  ┌──────────┐  ┌──────────────┐
    │       │ CPU  │    │ RamSpec  │  │ Storage  │  │ PortsProfile │
    │       │      │    │          │  │ Profile  │  │              │
    │       └──────┘    └──────────┘  └──────────┘  └──────────────┘
    │                                                       │
    ▼                                                       ▼
┌──────────────────┐                              ┌────────────────┐
│ ListingComponent │                              │ Port           │
│ (components,     │                              │ (type, count,  │
│  quantities)     │                              │  spec_notes)   │
└──────────────────┘                              └────────────────┘
    │
    ▼
┌──────────────────────┐
│ ListingScoreSnapshot │
│ (score history,      │
│  explain_json)       │
└──────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPORTING SYSTEMS                                   │
├────────────────┬────────────────┬────────────────┬─────────────────────────┤
│ CustomField    │ ImportSession  │ ApplicationSet │ BaselineAuditLog        │
│ Definition     │                │ tings          │                         │
└────────────────┴────────────────┴────────────────┴─────────────────────────┘
```

---

## Core Models

### 1. CPU (Performance Benchmarking)

**Purpose**: CPU catalog with PassMark benchmark data for performance calculations.

```python
# apps/api/dealbrain_api/models/core.py

class Cpu(Base, TimestampMixin):
    __tablename__ = "cpu"

    # Identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(64), nullable=False)  # Intel, AMD

    # Specifications
    socket: Mapped[str | None] = mapped_column(String(64))  # LGA1700, AM5
    cores: Mapped[int | None]
    threads: Mapped[int | None]
    tdp_w: Mapped[int | None]  # Thermal Design Power (watts)
    igpu_model: Mapped[str | None] = mapped_column(String(255))
    release_year: Mapped[int | None]

    # PassMark Benchmarks
    cpu_mark_multi: Mapped[int | None]   # Multi-threaded performance score
    cpu_mark_single: Mapped[int | None]  # Single-threaded performance score
    igpu_mark: Mapped[int | None]        # Integrated GPU score
    passmark_slug: Mapped[str | None] = mapped_column(String(512))
    passmark_category: Mapped[str | None] = mapped_column(String(64))
    passmark_id: Mapped[str | None] = mapped_column(String(64))

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    listings: Mapped[list["Listing"]] = relationship(back_populates="cpu", lazy="selectin")
```

**Key Features**:
- **Unique constraint** on `name` (e.g., "Intel Core i7-13700K")
- **Indexed** `id` for fast lookups
- **PassMark integration** for dollar-per-mark calculations
- **JSON attributes** for extensibility (custom metadata)

**Performance Metrics Usage**:
```python
# Used in Listing performance calculations
dollar_per_cpu_mark_multi = listing.price_usd / cpu.cpu_mark_multi
dollar_per_cpu_mark_single = listing.price_usd / cpu.cpu_mark_single
```

---

### 2. GPU (Graphics Performance)

**Purpose**: Discrete GPU catalog with benchmark scores.

```python
class Gpu(Base, TimestampMixin):
    __tablename__ = "gpu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(64), nullable=False)  # NVIDIA, AMD, Intel

    # Benchmarks
    gpu_mark: Mapped[int | None]    # PassMark G3D Mark
    metal_score: Mapped[int | None]  # Apple Metal score (for macOS)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    listings: Mapped[list["Listing"]] = relationship(back_populates="gpu", lazy="selectin")
```

**Key Features**:
- Supports both x86 (gpu_mark) and Apple Silicon (metal_score)
- Unique constraint on GPU name

---

### 3. Listing (Core Entity)

**Purpose**: Represents a single PC listing with pricing, components, and computed metrics.

```python
class Listing(Base, TimestampMixin):
    __tablename__ = "listing"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Basic Information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    listing_url: Mapped[str | None] = mapped_column(Text)
    seller: Mapped[str | None] = mapped_column(String(128))
    device_model: Mapped[str | None] = mapped_column(String(255))  # "HP EliteDesk 800 G9"

    # Pricing & Condition
    price_usd: Mapped[float] = mapped_column(nullable=False)
    price_date: Mapped[datetime | None]
    condition: Mapped[str] = mapped_column(String(16), nullable=False, default=Condition.USED.value)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=ListingStatus.ACTIVE.value)

    # Component Foreign Keys
    cpu_id: Mapped[int | None] = mapped_column(ForeignKey("cpu.id"))
    gpu_id: Mapped[int | None] = mapped_column(ForeignKey("gpu.id"))
    ram_spec_id: Mapped[int | None] = mapped_column(ForeignKey("ram_spec.id", ondelete="SET NULL"))
    primary_storage_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("storage_profile.id", ondelete="SET NULL")
    )
    secondary_storage_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("storage_profile.id", ondelete="SET NULL")
    )
    ports_profile_id: Mapped[int | None] = mapped_column(ForeignKey("ports_profile.id"))

    # Legacy Component Fields (kept for backward compatibility)
    ram_gb: Mapped[int] = mapped_column(default=0)
    ram_notes: Mapped[str | None] = mapped_column(Text)
    primary_storage_gb: Mapped[int] = mapped_column(default=0)
    primary_storage_type: Mapped[str | None] = mapped_column(String(64))
    secondary_storage_gb: Mapped[int | None]
    secondary_storage_type: Mapped[str | None] = mapped_column(String(64))
    os_license: Mapped[str | None] = mapped_column(String(64))
    other_components: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text)

    # Product Metadata (Added in 0013)
    manufacturer: Mapped[str | None] = mapped_column(String(64))  # "HP", "Dell", "Lenovo"
    series: Mapped[str | None] = mapped_column(String(128))       # "EliteDesk", "OptiPlex"
    model_number: Mapped[str | None] = mapped_column(String(128)) # "800 G9"
    form_factor: Mapped[str | None] = mapped_column(String(32))   # "SFF", "USFF", "Mini"

    # Valuation System
    ruleset_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_ruleset.id", ondelete="SET NULL"))
    adjusted_price_usd: Mapped[float | None]  # After applying valuation rules
    valuation_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # Explainability

    # Performance Metrics (Added in 0012)
    dollar_per_cpu_mark_single: Mapped[float | None]           # price / single-thread mark
    dollar_per_cpu_mark_single_adjusted: Mapped[float | None]  # adjusted_price / single mark
    dollar_per_cpu_mark_multi: Mapped[float | None]            # price / multi-thread mark
    dollar_per_cpu_mark_multi_adjusted: Mapped[float | None]   # adjusted_price / multi mark

    # Scoring Metrics
    active_profile_id: Mapped[int | None] = mapped_column(ForeignKey("profile.id"))
    score_cpu_multi: Mapped[float | None]
    score_cpu_single: Mapped[float | None]
    score_gpu: Mapped[float | None]
    score_composite: Mapped[float | None]
    dollar_per_cpu_mark: Mapped[float | None]      # Legacy: same as multi
    dollar_per_single_mark: Mapped[float | None]   # Legacy: single-thread
    perf_per_watt: Mapped[float | None]            # cpu_mark_multi / tdp_w

    # Metadata & Links
    raw_listing_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # Original import data
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    other_urls: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)

    # Relationships
    cpu: Mapped[Cpu | None] = relationship(back_populates="listings", lazy="joined")
    gpu: Mapped[Gpu | None] = relationship(back_populates="listings", lazy="joined")
    ram_spec: Mapped[RamSpec | None] = relationship(back_populates="listings", lazy="joined")
    primary_storage_profile: Mapped[StorageProfile | None] = relationship(
        back_populates="listings_primary", lazy="joined", foreign_keys=[primary_storage_profile_id]
    )
    secondary_storage_profile: Mapped[StorageProfile | None] = relationship(
        back_populates="listings_secondary", lazy="joined", foreign_keys=[secondary_storage_profile_id]
    )
    ports_profile: Mapped[PortsProfile | None] = relationship(back_populates="listings", lazy="joined")
    active_profile: Mapped[Profile | None] = relationship(back_populates="listings", lazy="joined")
    ruleset: Mapped["ValuationRuleset | None"] = relationship(back_populates="listings", lazy="joined")
    components: Mapped[list["ListingComponent"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )
    score_history: Mapped[list["ListingScoreSnapshot"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan", lazy="selectin"
    )

    # Computed Properties
    @property
    def ram_type(self) -> str | None:
        return self.ram_spec.ddr_generation.value if self.ram_spec else None

    @property
    def ram_speed_mhz(self) -> int | None:
        return self.ram_spec.speed_mhz if self.ram_spec else None
```

**Key Features**:
- **Central entity** connecting all components
- **Lazy loading strategies**: `joined` for frequently accessed, `selectin` for collections
- **Cascade delete** for components and score history
- **JSON columns** for extensibility and explainability
- **SET NULL** on component FK deletes (preserve listing if component removed)

**Valuation Breakdown Structure**:
```json
{
  "base_price": 500.0,
  "adjustments": [
    {"rule": "RAM Upgrade", "amount": -50.0, "reason": "32GB vs. baseline 16GB"},
    {"rule": "Condition Penalty", "amount": 25.0, "reason": "Used condition"}
  ],
  "adjusted_price": 475.0
}
```

---

### 4. ValuationRuleset (Three-Tier System)

**Purpose**: Top-level container for versioned rule collections.

```python
class ValuationRuleset(Base, TimestampMixin):
    __tablename__ = "valuation_ruleset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = mapped_column(String(128))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    conditions_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    rule_groups: Mapped[list["ValuationRuleGroup"]] = relationship(
        back_populates="ruleset", cascade="all, delete-orphan", lazy="selectin"
    )
    listings: Mapped[list["Listing"]] = relationship(back_populates="ruleset", lazy="selectin")
```

**Indexes**:
- `idx_ruleset_active` on `is_active`
- `idx_ruleset_created_by` on `created_by`

**Use Cases**:
- **Baseline rulesets**: Standard valuation rules (e.g., "Baseline Q4 2025")
- **Custom rulesets**: Client-specific or scenario-based rules
- **Versioning**: Track rule changes over time

---

### 5. ValuationRuleGroup (Category Organization)

**Purpose**: Logical grouping of related rules with weighting.

```python
class ValuationRuleGroup(Base, TimestampMixin):
    __tablename__ = "valuation_rule_group"
    __table_args__ = (UniqueConstraint("ruleset_id", "name", name="uq_rule_group_ruleset_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ruleset_id: Mapped[int] = mapped_column(ForeignKey("valuation_ruleset.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # "performance", "storage", "condition"
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    weight: Mapped[float] = mapped_column(nullable=True, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    ruleset: Mapped[ValuationRuleset] = relationship(back_populates="rule_groups")
    rules: Mapped[list["ValuationRuleV2"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin"
    )
```

**Indexes**:
- `idx_rule_group_ruleset` on `ruleset_id`
- `idx_rule_group_category` on `category`

**Key Features**:
- **Category-based organization**: Group rules by component type or concern
- **Weighted scoring**: Apply different importance to rule groups
- **Display order**: Control UI presentation
- **Cascade delete**: Removing ruleset deletes all groups

**Example Groups**:
```python
groups = [
    {"name": "CPU Performance", "category": "performance", "weight": 1.0},
    {"name": "RAM Configuration", "category": "memory", "weight": 0.8},
    {"name": "Storage Adjustments", "category": "storage", "weight": 0.7}
]
```

---

### 6. ValuationRuleV2 (Individual Rules)

**Purpose**: Individual valuation rule with conditions and actions.

```python
class ValuationRuleV2(Base, TimestampMixin):
    __tablename__ = "valuation_rule_v2"
    __table_args__ = (UniqueConstraint("group_id", "name", name="uq_rule_v2_group_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("valuation_rule_group.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evaluation_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    group: Mapped[ValuationRuleGroup] = relationship(back_populates="rules")
    conditions: Mapped[list["ValuationRuleCondition"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    actions: Mapped[list["ValuationRuleAction"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    versions: Mapped[list["ValuationRuleVersion"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    audit_logs: Mapped[list["ValuationRuleAudit"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
```

**Indexes**:
- `idx_rule_v2_group` on `group_id`
- `idx_rule_v2_active` on `is_active`
- `idx_rule_v2_eval_order` on `(group_id, evaluation_order)`

**Key Features**:
- **Evaluation order**: Control rule execution sequence
- **Version tracking**: Maintain rule history
- **Audit logging**: Track who changed what and when
- **Metadata storage**: Store rule-specific configuration

---

### 7. ValuationRuleCondition (Rule Logic)

**Purpose**: Hierarchical conditions for rule matching.

```python
class ValuationRuleCondition(Base):
    __tablename__ = "valuation_rule_condition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("valuation_rule_v2.id", ondelete="CASCADE"), nullable=False)
    parent_condition_id: Mapped[int | None] = mapped_column(
        ForeignKey("valuation_rule_condition.id", ondelete="CASCADE")
    )
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)  # "cpu_id", "ram_gb", "condition"
    field_type: Mapped[str] = mapped_column(String(32), nullable=False)   # "integer", "string", "enum"
    operator: Mapped[str] = mapped_column(String(32), nullable=False)     # "equals", "gt", "in"
    value_json: Mapped[dict[str, Any] | list[Any] | str | int | float] = mapped_column(JSON, nullable=False)
    logical_operator: Mapped[str | None] = mapped_column(String(8))       # "AND", "OR"
    group_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    # Relationships
    rule: Mapped[ValuationRuleV2] = relationship(back_populates="conditions")
    parent: Mapped["ValuationRuleCondition | None"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["ValuationRuleCondition"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
```

**Indexes**:
- `idx_condition_rule` on `rule_id`
- `idx_condition_parent` on `parent_condition_id`

**Supported Operators**:
- **Comparison**: `equals`, `not_equals`, `gt`, `gte`, `lt`, `lte`
- **Set operations**: `in`, `not_in`
- **String operations**: `contains`, `startswith`, `regex`
- **Logical**: `AND`, `OR` (via `logical_operator`)

**Example Condition Tree**:
```
Rule: "High-End RAM Deduction"
├─ AND
│  ├─ ram_gb >= 32
│  └─ OR
│     ├─ ram_spec.ddr_generation == "ddr5"
│     └─ ram_spec.speed_mhz >= 4800
```

---

### 8. ValuationRuleAction (Rule Effects)

**Purpose**: Define price adjustments when rule conditions match.

```python
class ValuationRuleAction(Base):
    __tablename__ = "valuation_rule_action"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("valuation_rule_v2.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)  # "adjust_price", "set_flag"
    metric: Mapped[str | None] = mapped_column(String(32))                # "ram_gb", "storage_gb"
    value_usd: Mapped[float | None]  # Fixed adjustment amount
    unit_type: Mapped[str | None] = mapped_column(String(32))             # "per_gb", "flat", "multiplier"
    formula: Mapped[str | None] = mapped_column(Text)                     # Python expression
    modifiers_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    # Relationships
    rule: Mapped[ValuationRuleV2] = relationship(back_populates="actions")
```

**Index**:
- `idx_action_rule` on `rule_id`

**Action Types**:
- **adjust_price**: Modify adjusted_price_usd
- **set_metric**: Update computed metrics
- **add_tag**: Add metadata tags

**Example Actions**:
```python
# Deduct $5 per GB over 16GB RAM
{
    "action_type": "adjust_price",
    "metric": "ram_gb",
    "value_usd": -5.0,
    "unit_type": "per_gb",
    "formula": "(listing.ram_gb - 16) * value_usd"
}

# Apply condition multiplier
{
    "action_type": "adjust_price",
    "unit_type": "multiplier",
    "value_usd": 0.75,  # 75% of base price for used condition
    "formula": "base_price * value_usd"
}
```

---

### 9. Profile (Scoring Configuration)

**Purpose**: Define weighted scoring profiles for ranking listings.

```python
class Profile(Base, TimestampMixin):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weights_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    rule_group_weights: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    listings: Mapped[list["Listing"]] = relationship(back_populates="active_profile", lazy="selectin")
```

**Example Profile**:
```json
{
  "name": "Gaming Performance",
  "weights_json": {
    "score_cpu_multi": 0.3,
    "score_cpu_single": 0.4,
    "score_gpu": 0.3
  },
  "rule_group_weights": {
    "CPU Performance": 1.0,
    "GPU Performance": 1.2,
    "Storage": 0.5
  }
}
```

---

### 10. PortsProfile & Port (I/O Connectivity)

**Purpose**: Catalog port configurations for connectivity tracking.

```python
class PortsProfile(Base, TimestampMixin):
    __tablename__ = "ports_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    ports: Mapped[list["Port"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    listings: Mapped[list["Listing"]] = relationship(back_populates="ports_profile", lazy="selectin")


class Port(Base, TimestampMixin):
    __tablename__ = "port"
    __table_args__ = (UniqueConstraint("ports_profile_id", "type", "spec_notes", name="uq_port_profile_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ports_profile_id: Mapped[int] = mapped_column(ForeignKey("ports_profile.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # PortType enum value
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    spec_notes: Mapped[str | None] = mapped_column(String(255))   # "USB 3.2 Gen2", "10Gbps"

    # Relationships
    profile: Mapped[PortsProfile] = relationship(back_populates="ports")
```

**Port Types** (from `dealbrain_core.enums.PortType`):
```python
USB_A, USB_C, THUNDERBOLT, HDMI, DISPLAYPORT,
RJ45_1G, RJ45_2_5G, RJ45_10G, AUDIO, SDXC,
PCIE_X16, PCIE_X8, M2_SLOT, SATA_BAY, OTHER
```

**Example Port Profile**:
```python
{
  "name": "HP EliteDesk 800 G9 SFF",
  "ports": [
    {"type": "usb_a", "count": 4, "spec_notes": "USB 3.2 Gen1"},
    {"type": "usb_c", "count": 2, "spec_notes": "USB 3.2 Gen2"},
    {"type": "hdmi", "count": 1, "spec_notes": "HDMI 2.0"},
    {"type": "displayport", "count": 2, "spec_notes": "DP 1.4"},
    {"type": "rj45_1g", "count": 1, "spec_notes": "Intel I219-LM"}
  ]
}
```

---

### 11. RamSpec (Memory Configuration)

**Purpose**: Structured RAM specifications with generation, speed, and capacity.

```python
class RamSpec(Base, TimestampMixin):
    __tablename__ = "ram_spec"
    __table_args__ = (
        UniqueConstraint(
            "ddr_generation", "speed_mhz", "module_count",
            "capacity_per_module_gb", "total_capacity_gb",
            name="uq_ram_spec_dimensions"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str | None] = mapped_column(String(128))  # "32GB DDR5-4800 (2x16GB)"
    ddr_generation: Mapped[RamGeneration] = mapped_column(
        SAEnum(RamGeneration, name="ram_generation", native_enum=True),
        nullable=False,
        default=RamGeneration.UNKNOWN
    )
    speed_mhz: Mapped[int | None] = mapped_column(Integer)
    module_count: Mapped[int | None] = mapped_column(Integer)
    capacity_per_module_gb: Mapped[int | None] = mapped_column(Integer)
    total_capacity_gb: Mapped[int | None] = mapped_column(Integer)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    listings: Mapped[list["Listing"]] = relationship(back_populates="ram_spec", lazy="selectin")
```

**RamGeneration Enum**:
```python
DDR3, DDR4, DDR5, LPDDR4, LPDDR4X, LPDDR5, LPDDR5X, HBM2, HBM3, UNKNOWN
```

**Key Features**:
- **Unique constraint** prevents duplicate specs
- **PostgreSQL enum** for RAM generation
- **Flexible metadata** in `attributes_json`

**Example Specs**:
```python
[
    {"label": "16GB DDR4-3200", "ddr_generation": "ddr4", "speed_mhz": 3200, "total_capacity_gb": 16},
    {"label": "32GB DDR5-4800 (2x16GB)", "ddr_generation": "ddr5", "speed_mhz": 4800,
     "module_count": 2, "capacity_per_module_gb": 16, "total_capacity_gb": 32}
]
```

---

### 12. StorageProfile (Storage Configuration)

**Purpose**: Structured storage specifications with medium, capacity, and performance tier.

```python
class StorageProfile(Base, TimestampMixin):
    __tablename__ = "storage_profile"
    __table_args__ = (
        UniqueConstraint(
            "medium", "interface", "form_factor", "capacity_gb", "performance_tier",
            name="uq_storage_profile_dimensions"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str | None] = mapped_column(String(128))  # "512GB NVMe PCIe 4.0"
    medium: Mapped[StorageMedium] = mapped_column(
        SAEnum(StorageMedium, name="storage_medium", native_enum=True),
        nullable=False,
        default=StorageMedium.UNKNOWN
    )
    interface: Mapped[str | None] = mapped_column(String(64))         # "PCIe 4.0 x4", "SATA III"
    form_factor: Mapped[str | None] = mapped_column(String(64))       # "M.2 2280", "2.5-inch"
    capacity_gb: Mapped[int | None] = mapped_column(Integer)
    performance_tier: Mapped[str | None] = mapped_column(String(64))  # "High", "Medium", "Entry"
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    listings_primary: Mapped[list["Listing"]] = relationship(
        back_populates="primary_storage_profile",
        foreign_keys="Listing.primary_storage_profile_id",
        lazy="selectin"
    )
    listings_secondary: Mapped[list["Listing"]] = relationship(
        back_populates="secondary_storage_profile",
        foreign_keys="Listing.secondary_storage_profile_id",
        lazy="selectin"
    )
```

**StorageMedium Enum**:
```python
NVME, SATA_SSD, HDD, HYBRID, EMMC, UFS, UNKNOWN
```

**Key Features**:
- **Dual relationships**: Supports primary and secondary storage
- **Unique constraint** prevents duplicate profiles
- **Performance tier** for valuation adjustments

**Example Profiles**:
```python
[
    {"label": "512GB NVMe · PCIe 4.0", "medium": "nvme", "interface": "PCIe 4.0 x4",
     "capacity_gb": 512, "performance_tier": "High"},
    {"label": "1TB SATA SSD · 2.5\"", "medium": "sata_ssd", "form_factor": "2.5-inch",
     "capacity_gb": 1024, "performance_tier": "Medium"}
]
```

---

## Supporting Models

### 13. ListingComponent (Component Tracking)

**Purpose**: Track individual components and their valuation adjustments.

```python
class ListingComponent(Base, TimestampMixin):
    __tablename__ = "listing_component"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)  # ComponentType enum
    name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(default=1)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    adjustment_value_usd: Mapped[float | None]  # Applied adjustment amount

    # Relationships
    listing: Mapped[Listing] = relationship(back_populates="components")
```

**ComponentType Enum**:
```python
RAM, SSD, HDD, OS_LICENSE, WIFI, GPU, MISC
```

---

### 14. ListingScoreSnapshot (Score History)

**Purpose**: Track historical scoring data for trend analysis.

```python
class ListingScoreSnapshot(Base, TimestampMixin):
    __tablename__ = "listing_score_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profile.id"))
    score_composite: Mapped[float | None]
    adjusted_price_usd: Mapped[float | None]
    dollar_per_cpu_mark: Mapped[float | None]
    dollar_per_single_mark: Mapped[float | None]
    perf_per_watt: Mapped[float | None]
    explain_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationships
    listing: Mapped[Listing] = relationship(back_populates="score_history")
    profile: Mapped[Profile | None] = relationship()
```

**Use Case**: Track how scores change over time as rules or prices are updated.

---

### 15. CustomFieldDefinition (Dynamic Fields)

**Purpose**: Define custom fields per entity type without schema changes.

```python
class CustomFieldDefinition(Base, TimestampMixin):
    __tablename__ = "custom_field_definition"
    __table_args__ = (
        UniqueConstraint("entity", "key", name="uq_custom_field_entity_key"),
        Index("ix_custom_field_definition_entity", "entity"),
        Index("ix_custom_field_definition_order", "entity", "display_order")
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)  # "listing", "cpu", "gpu"
    key: Mapped[str] = mapped_column(String(64), nullable=False)     # "warranty_months", "certification"
    label: Mapped[str] = mapped_column(String(128), nullable=False)  # "Warranty Period (Months)"
    data_type: Mapped[str] = mapped_column(String(32), nullable=False, default="string")
    description: Mapped[str | None] = mapped_column(Text)
    required: Mapped[bool] = mapped_column(nullable=False, default=False)
    default_value: Mapped[Any | None] = mapped_column(JSON)
    options: Mapped[list[str] | None] = mapped_column(JSON)  # For dropdown/select fields
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="public")
    created_by: Mapped[str | None] = mapped_column(String(128))
    validation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    deleted_at: Mapped[datetime | None]

    # Relationships
    audit_events: Mapped[list["CustomFieldAuditLog"]] = relationship(
        back_populates="field", cascade="all, delete-orphan", lazy="selectin"
    )
```

**Supported Data Types**:
```python
"string", "integer", "float", "boolean", "date", "datetime", "select", "multiselect", "json"
```

**Example Fields**:
```python
[
    {"entity": "listing", "key": "warranty_months", "label": "Warranty (Months)",
     "data_type": "integer", "default_value": 12},
    {"entity": "listing", "key": "certification", "label": "Certification",
     "data_type": "select", "options": ["None", "Energy Star", "EPEAT Gold"]}
]
```

**Storage**: Field values stored in `attributes_json` on entity models.

---

### 16. ApplicationSettings (System Configuration)

**Purpose**: Store system-wide settings (e.g., valuation thresholds).

```python
class ApplicationSettings(Base, TimestampMixin):
    __tablename__ = "application_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
```

**Example Settings**:
```python
{
    "key": "valuation_thresholds",
    "value_json": {
        "great_deal": -50.0,  # $50+ below baseline
        "good_deal": -20.0,   # $20-$50 below baseline
        "fair": 20.0,         # Within $20 of baseline
        "premium": 50.0       # $20-$50 above baseline
    }
}
```

---

### 17. ImportSession (Import Tracking)

**Purpose**: Track Excel import sessions with conflict resolution.

```python
class ImportSession(Base, TimestampMixin):
    __tablename__ = "import_session"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128))
    checksum: Mapped[str | None] = mapped_column(String(64))  # SHA256 hash
    upload_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    sheet_meta_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    mappings_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    conflicts_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    preview_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    declared_entities_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(128))

    # Relationships
    audit_events: Mapped[list["ImportSessionAudit"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )
```

**Status Values**: `pending`, `mapping`, `preview`, `importing`, `completed`, `failed`

---

### 18. BaselineAuditLog (Baseline Operations)

**Purpose**: Audit log for baseline valuation rule operations.

```python
class BaselineAuditLog(Base):
    __tablename__ = "baseline_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, index=True)
    actor_name: Mapped[str | None] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    result: Mapped[str] = mapped_column(String(16), nullable=False, default="success")
    error_message: Mapped[str | None] = mapped_column(Text)

    # Operation-specific fields
    ruleset_id: Mapped[int | None] = mapped_column(Integer, index=True)
    source_hash: Mapped[str | None] = mapped_column(String(64), index=True)  # Git commit or file hash
    version: Mapped[str | None] = mapped_column(String(32))
    entity_key: Mapped[str | None] = mapped_column(String(128))
    field_name: Mapped[str | None] = mapped_column(String(128))

    # Impact tracking
    affected_listings_count: Mapped[int | None] = mapped_column(Integer)
    total_adjustment_change: Mapped[float | None] = mapped_column(JSON)
```

**Indexed Fields**: `operation`, `actor_id`, `timestamp`, `ruleset_id`, `source_hash`

**Operation Types**:
- `import_baseline`: Imported baseline rules from Excel
- `adopt_baseline`: Applied baseline ruleset to listings
- `override_field`: Manual field override
- `recalculate_metrics`: Bulk recalculation triggered

---

## JSON Column Patterns

### 1. attributes_json (Extensibility)

**Purpose**: Store arbitrary metadata without schema changes.

**Used in**: `CPU`, `GPU`, `Listing`, `PortsProfile`, `RamSpec`, `StorageProfile`

**Pattern**:
```python
attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
```

**Example Usage**:
```python
cpu.attributes_json = {
    "tdp_min": 35,
    "tdp_max": 125,
    "boost_clock_ghz": 5.4,
    "l3_cache_mb": 30,
    "custom_warranty_months": 36
}

listing.attributes_json = {
    "refurb_grade": "A",
    "warranty_remaining_days": 365,
    "bios_version": "2.14.0",
    "custom_notes": "Minor cosmetic wear on top panel"
}
```

---

### 2. valuation_breakdown (Explainability)

**Purpose**: Track rule applications for transparency.

**Structure**:
```json
{
  "base_price": 500.0,
  "ruleset": "Baseline Q4 2025",
  "ruleset_id": 1,
  "applied_groups": [
    {
      "group_name": "CPU Performance",
      "rules": [
        {
          "rule_name": "i7-13700K Premium",
          "description": "High-end CPU adjustment",
          "adjustment": -30.0,
          "metadata": {"cpu_name": "Intel Core i7-13700K"}
        }
      ]
    },
    {
      "group_name": "RAM Configuration",
      "rules": [
        {
          "rule_name": "32GB Deduction",
          "description": "Above baseline 16GB",
          "adjustment": -50.0,
          "calculation": "(32 - 16) * $5.00"
        }
      ]
    }
  ],
  "total_adjustments": -80.0,
  "adjusted_price": 420.0
}
```

---

### 3. metadata_json (Rule Configuration)

**Purpose**: Store rule-specific configuration and parameters.

**Used in**: `ValuationRuleset`, `ValuationRuleV2`, `ListingComponent`

**Example**:
```python
# Rule metadata
rule.metadata_json = {
    "category": "performance",
    "tags": ["cpu", "high-end"],
    "documentation_url": "https://docs.example.com/rules/cpu-premium",
    "last_validated": "2025-10-01",
    "baseline_source": "market_analysis_q4_2025.xlsx"
}

# Ruleset metadata
ruleset.metadata_json = {
    "source": "baseline_valuation_rules_oct_2025.xlsx",
    "author": "Deal Brain Team",
    "effective_date": "2025-10-01",
    "review_cycle_days": 90
}
```

---

### 4. value_json (Dynamic Rule Values)

**Purpose**: Store condition values as structured data.

**Used in**: `ValuationRuleCondition`

**Example**:
```python
# Simple value
condition.value_json = 32  # ram_gb equals 32

# List of values (IN operator)
condition.value_json = ["ddr4", "ddr5"]  # ddr_generation in ["ddr4", "ddr5"]

# Complex object
condition.value_json = {
    "min": 16,
    "max": 64,
    "unit": "GB"
}
```

---

## Relationships and Foreign Keys

### Cascade Behaviors

| Relationship | Parent → Child | ON DELETE Behavior |
|---|---|---|
| `ValuationRuleset → RuleGroup` | 1:N | CASCADE (delete groups when ruleset deleted) |
| `ValuationRuleGroup → RuleV2` | 1:N | CASCADE (delete rules when group deleted) |
| `ValuationRuleV2 → Condition/Action` | 1:N | CASCADE (delete conditions/actions with rule) |
| `Listing → ListingComponent` | 1:N | CASCADE (delete components with listing) |
| `Listing → CPU/GPU` | N:1 | None (NULL FK on CPU/GPU delete) |
| `Listing → RamSpec/StorageProfile` | N:1 | SET NULL (preserve listing data) |
| `PortsProfile → Port` | 1:N | CASCADE (delete ports with profile) |
| `ValuationRuleCondition` (self-ref) | 1:N | CASCADE (hierarchical delete) |

### Lazy Loading Strategies

```python
# Joined: Load with parent in single query (for frequently accessed)
cpu: Mapped[Cpu | None] = relationship(back_populates="listings", lazy="joined")

# Selectin: Separate query with WHERE IN (for collections)
ports: Mapped[list["Port"]] = relationship(back_populates="profile", lazy="selectin")

# Lazy (default): Load on access (use sparingly)
# No explicit lazy parameter
```

---

## Indexes and Constraints

### Primary Keys

All models use **auto-incrementing integer** primary keys except:
- `ImportSession`: UUID (for distributed systems)
- `ApplicationSettings`: String key (key-value store)

### Unique Constraints

```sql
-- Prevent duplicate entries
ALTER TABLE cpu ADD CONSTRAINT cpu_name_unique UNIQUE (name);
ALTER TABLE gpu ADD CONSTRAINT gpu_name_unique UNIQUE (name);
ALTER TABLE valuation_ruleset ADD CONSTRAINT valuation_ruleset_name_unique UNIQUE (name);

-- Composite uniqueness
ALTER TABLE valuation_rule_group
    ADD CONSTRAINT uq_rule_group_ruleset_name UNIQUE (ruleset_id, name);

ALTER TABLE valuation_rule_v2
    ADD CONSTRAINT uq_rule_v2_group_name UNIQUE (group_id, name);

-- Prevent duplicate components
ALTER TABLE ram_spec
    ADD CONSTRAINT uq_ram_spec_dimensions
    UNIQUE (ddr_generation, speed_mhz, module_count, capacity_per_module_gb, total_capacity_gb);

ALTER TABLE storage_profile
    ADD CONSTRAINT uq_storage_profile_dimensions
    UNIQUE (medium, interface, form_factor, capacity_gb, performance_tier);
```

### Foreign Key Indexes

```sql
-- Automatically indexed by PostgreSQL (FK columns)
CREATE INDEX idx_listing_cpu_id ON listing(cpu_id);
CREATE INDEX idx_listing_gpu_id ON listing(gpu_id);
CREATE INDEX idx_listing_ruleset_id ON listing(ruleset_id);

-- Composite indexes for sorting/filtering
CREATE INDEX idx_rule_v2_eval_order ON valuation_rule_v2(group_id, evaluation_order);
CREATE INDEX idx_custom_field_definition_order ON custom_field_definition(entity, display_order);
```

### Query Optimization Indexes

```sql
-- Status filtering
CREATE INDEX idx_ruleset_active ON valuation_ruleset(is_active);
CREATE INDEX idx_rule_v2_active ON valuation_rule_v2(is_active);

-- Audit log queries
CREATE INDEX idx_baseline_audit_operation ON baseline_audit_log(operation);
CREATE INDEX idx_baseline_audit_timestamp ON baseline_audit_log(timestamp);
CREATE INDEX idx_baseline_audit_source_hash ON baseline_audit_log(source_hash);

-- Custom field lookups
CREATE INDEX idx_custom_field_definition_entity ON custom_field_definition(entity);
```

---

## Migration Strategy

### Alembic Configuration

```ini
# alembic.ini
[alembic]
script_location = apps/api/alembic
sqlalchemy.url = sqlite:///./dealbrain.db  # Overridden by env.py
```

**Actual URL**: Set via `DEALBRAIN_DATABASE_URL` environment variable (PostgreSQL).

### Migration Workflow

```bash
# Generate migration from model changes
poetry run alembic revision --autogenerate -m "Add baseline audit log"

# Review generated migration
vim apps/api/alembic/versions/0019_add_baseline_audit_log.py

# Apply migration
make migrate  # Equivalent to: poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Check current version
poetry run alembic current
```

### Key Migrations

| Version | Date | Description |
|---------|------|-------------|
| 0001 | Sep 20 | Initial schema (CPU, GPU, Listing, Profile) |
| 0008 | Oct 1 | Replace valuation rules with v2 three-tier system |
| 0010 | Oct 3 | Add ApplicationSettings table |
| 0012 | Oct 5 | Add listing performance metrics (dollar_per_cpu_mark variants) |
| 0013 | Oct 5 | Add listing metadata fields (manufacturer, series, model_number, form_factor) |
| 0015 | Oct 8 | Add listing other_urls and ruleset priority |
| 0017 | Oct 11 | Introduce RamSpec and StorageProfile with enum types |
| 0019 | Oct 13 | Add BaselineAuditLog for baseline operations |

### Migration Best Practices

#### 1. **Zero-Downtime Migrations**

```python
def upgrade():
    # Step 1: Add nullable column
    op.add_column('listing', sa.Column('new_field', sa.String(128), nullable=True))

    # Step 2: Backfill data
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE listing SET new_field = 'default_value' WHERE new_field IS NULL")
    )

    # Step 3: Make non-nullable (optional)
    op.alter_column('listing', 'new_field', nullable=False)
```

#### 2. **Enum Type Creation (PostgreSQL)**

```python
def upgrade():
    # Create enum if not exists (idempotent)
    bind = op.get_bind()
    bind.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ram_generation') THEN
                CREATE TYPE ram_generation AS ENUM ('ddr3', 'ddr4', 'ddr5', 'unknown');
            END IF;
        END$$;
    """))

    # Use existing enum in table
    op.create_table(
        'ram_spec',
        sa.Column('ddr_generation',
            postgresql.ENUM('ddr3', 'ddr4', 'ddr5', name='ram_generation', create_type=False),
            nullable=False
        )
    )
```

#### 3. **Data Backfill with Caching**

```python
def _backfill_components(bind: Any) -> None:
    """Efficient backfill with caching to avoid N+1 queries."""
    metadata = sa.MetaData()
    metadata.reflect(bind=bind, only=("listing", "ram_spec"))

    listing_table = metadata.tables["listing"]
    ram_spec_table = metadata.tables["ram_spec"]

    ram_cache: dict[tuple, int] = {}  # Cache created specs

    listings = list(bind.execute(
        sa.select(listing_table.c.id, listing_table.c.ram_gb)
    ))

    for row in listings:
        key = (row.ram_gb,)
        if key not in ram_cache:
            # Create spec
            spec_id = bind.execute(
                ram_spec_table.insert().values(total_capacity_gb=row.ram_gb).returning(ram_spec_table.c.id)
            ).scalar_one()
            ram_cache[key] = spec_id

        # Update listing
        bind.execute(
            listing_table.update().where(listing_table.c.id == row.id).values(ram_spec_id=ram_cache[key])
        )
```

#### 4. **Safe Column Removal**

```python
def upgrade():
    # Step 1: Make column nullable (if not already)
    op.alter_column('listing', 'old_column', nullable=True)

    # Step 2: Deploy code that no longer uses the column
    # (Deploy application before running this migration)

    # Step 3: Drop column
    op.drop_column('listing', 'old_column')
```

---

## Performance Considerations

### 1. **Connection Pooling**

SQLAlchemy's async engine uses connection pooling by default:

```python
# Default pool configuration
engine = create_async_engine(
    database_url,
    pool_size=5,          # Core connections
    max_overflow=10,      # Additional connections
    pool_pre_ping=True,   # Validate connections before use
    echo=False            # Disable SQL logging in production
)
```

**Tuning**:
- Increase `pool_size` for high-concurrency APIs
- Monitor with `pg_stat_activity` in PostgreSQL

### 2. **Query Optimization**

```python
# ❌ Bad: N+1 query problem
listings = await session.execute(select(Listing))
for listing in listings.scalars():
    print(listing.cpu.name)  # Triggers separate query per listing

# ✅ Good: Eager loading
stmt = select(Listing).options(joinedload(Listing.cpu))
listings = await session.execute(stmt)
for listing in listings.scalars():
    print(listing.cpu.name)  # Already loaded
```

### 3. **Batch Operations**

```python
# Insert multiple records efficiently
async with session_scope() as session:
    listings = [
        Listing(title=f"Listing {i}", price_usd=100.0 * i)
        for i in range(1000)
    ]
    session.add_all(listings)
    # Commits in single transaction
```

### 4. **Index Coverage**

```sql
-- Ensure queries use indexes
EXPLAIN ANALYZE
SELECT * FROM listing
WHERE status = 'active' AND price_usd < 500
ORDER BY created_at DESC
LIMIT 10;

-- Add covering index if needed
CREATE INDEX idx_listing_status_price_created
ON listing(status, price_usd, created_at DESC);
```

---

## Database Monitoring

### Key Metrics

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'dealbrain';

-- Slow queries (> 1 second)
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

---

## Code Examples

### 1. **Creating a Listing with Components**

```python
from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.models.core import Listing, Cpu, RamSpec, StorageProfile

async def create_listing_example():
    async with session_scope() as session:
        # Fetch or create CPU
        cpu = await session.execute(
            select(Cpu).where(Cpu.name == "Intel Core i7-13700K")
        )
        cpu = cpu.scalar_one_or_none()

        if not cpu:
            cpu = Cpu(
                name="Intel Core i7-13700K",
                manufacturer="Intel",
                cores=16,
                threads=24,
                cpu_mark_multi=45000,
                cpu_mark_single=4200
            )
            session.add(cpu)
            await session.flush()  # Get CPU ID

        # Create RAM spec
        ram_spec = RamSpec(
            label="32GB DDR5-4800",
            ddr_generation=RamGeneration.DDR5,
            speed_mhz=4800,
            total_capacity_gb=32
        )
        session.add(ram_spec)
        await session.flush()

        # Create storage profile
        storage = StorageProfile(
            label="1TB NVMe PCIe 4.0",
            medium=StorageMedium.NVME,
            interface="PCIe 4.0 x4",
            capacity_gb=1024,
            performance_tier="High"
        )
        session.add(storage)
        await session.flush()

        # Create listing
        listing = Listing(
            title="HP EliteDesk 800 G9 - i7-13700K",
            price_usd=899.99,
            condition=Condition.REFURB,
            manufacturer="HP",
            series="EliteDesk",
            model_number="800 G9",
            form_factor="SFF",
            cpu_id=cpu.id,
            ram_spec_id=ram_spec.id,
            primary_storage_profile_id=storage.id
        )
        session.add(listing)
        # Commit happens in context manager exit

    return listing.id
```

### 2. **Querying with Filters**

```python
from sqlalchemy import and_, or_

async def find_best_deals():
    async with session_scope() as session:
        stmt = (
            select(Listing)
            .options(
                joinedload(Listing.cpu),
                joinedload(Listing.ram_spec),
                joinedload(Listing.primary_storage_profile)
            )
            .where(
                and_(
                    Listing.status == ListingStatus.ACTIVE,
                    Listing.adjusted_price_usd.isnot(None),
                    Listing.adjusted_price_usd < 500,
                    or_(
                        Listing.condition == Condition.NEW,
                        Listing.condition == Condition.REFURB
                    )
                )
            )
            .order_by(Listing.dollar_per_cpu_mark_multi_adjusted.asc())
            .limit(10)
        )

        result = await session.execute(stmt)
        return result.scalars().all()
```

### 3. **Applying Valuation Rules**

```python
async def apply_valuation_ruleset(listing_id: int, ruleset_id: int):
    async with session_scope() as session:
        # Load listing with all dependencies
        stmt = (
            select(Listing)
            .options(
                joinedload(Listing.cpu),
                joinedload(Listing.ram_spec),
                selectinload(Listing.components)
            )
            .where(Listing.id == listing_id)
        )
        listing = (await session.execute(stmt)).scalar_one()

        # Load ruleset with groups and rules
        ruleset_stmt = (
            select(ValuationRuleset)
            .options(
                selectinload(ValuationRuleset.rule_groups)
                .selectinload(ValuationRuleGroup.rules)
                .selectinload(ValuationRuleV2.conditions),
                selectinload(ValuationRuleset.rule_groups)
                .selectinload(ValuationRuleGroup.rules)
                .selectinload(ValuationRuleV2.actions)
            )
            .where(ValuationRuleset.id == ruleset_id)
        )
        ruleset = (await session.execute(ruleset_stmt)).scalar_one()

        # Apply rules (simplified logic)
        total_adjustment = 0.0
        breakdown = {"base_price": listing.price_usd, "applied_groups": []}

        for group in ruleset.rule_groups:
            if not group.is_active:
                continue

            group_data = {"group_name": group.name, "rules": []}

            for rule in group.rules:
                if not rule.is_active:
                    continue

                # Evaluate conditions (simplified)
                if evaluate_conditions(rule.conditions, listing):
                    # Apply actions
                    adjustment = calculate_adjustment(rule.actions, listing)
                    total_adjustment += adjustment

                    group_data["rules"].append({
                        "rule_name": rule.name,
                        "adjustment": adjustment
                    })

            if group_data["rules"]:
                breakdown["applied_groups"].append(group_data)

        listing.adjusted_price_usd = listing.price_usd + total_adjustment
        listing.valuation_breakdown = breakdown
        listing.ruleset_id = ruleset_id
```

---

## Summary

Deal Brain's database schema provides:

1. **Comprehensive Component Tracking**: CPU, GPU, RAM, storage, ports
2. **Flexible Valuation System**: Three-tier ruleset → group → rule architecture
3. **Performance Metrics**: Dollar-per-mark calculations for CPU efficiency
4. **Extensibility**: JSON columns and custom fields for dynamic attributes
5. **Audit Logging**: Track rule changes and baseline operations
6. **Migration Safety**: Alembic with 19+ migrations, best practices for zero downtime
7. **Query Optimization**: Strategic indexing, eager loading, relationship management

**Key Files**:
- Models: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`
- DB Config: `/mnt/containers/deal-brain/apps/api/dealbrain_api/db.py`
- Migrations: `/mnt/containers/deal-brain/apps/api/alembic/versions/`
- Enums: `/mnt/containers/deal-brain/packages/core/dealbrain_core/enums.py`
