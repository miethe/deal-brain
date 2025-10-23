# Shared Domain Logic

## Overview

The `packages/core/dealbrain_core/` package contains the pure business logic shared across all Deal Brain services (API, CLI, and future components). This package is infrastructure-agnostic and contains no database, HTTP, or framework-specific code.

**Design Philosophy:**
- Pure domain logic without side effects
- Framework-agnostic implementations
- Shared by API and CLI applications
- Testable in isolation
- Focused on business rules and calculations

**Package Location:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/`

---

## Architecture Principles

### Separation of Concerns

The core package maintains strict boundaries:

```
packages/core/dealbrain_core/    # Pure business logic
├── valuation.py                 # Pricing calculations
├── scoring.py                   # Performance metrics
├── rule_evaluator.py           # Rule evaluation (legacy)
├── enums.py                    # Domain enumerations
├── gpu.py                      # GPU-specific calculations
├── schemas/                    # Pydantic data models
└── rules/                      # Rules engine v2
```

Services layer (in `apps/api/`) orchestrates these domain functions with persistence.

### Immutability

Domain functions are pure and operate on immutable data structures:

```python
# Input data classes are immutable
@dataclass
class ValuationRuleData:
    component_type: ComponentType
    metric: ComponentMetric
    unit_value_usd: float
    # ... condition multipliers

# Functions return new data structures
def compute_adjusted_price(...) -> ValuationResult:
    # Pure calculation with no side effects
    return ValuationResult(...)
```

---

## Valuation Engine

**File:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/valuation.py`

The valuation engine computes adjusted listing prices by applying component-based deductions with condition multipliers.

### Core Data Structures

#### ValuationRuleData

Represents a valuation rule for a specific component type:

```python
@dataclass
class ValuationRuleData:
    component_type: ComponentType  # RAM, SSD, HDD, etc.
    metric: ComponentMetric        # PER_GB, PER_TB, FLAT
    unit_value_usd: float         # Base value per unit
    condition_new: float = 1.0     # Multiplier for NEW condition
    condition_refurb: float = 0.75 # Multiplier for REFURB
    condition_used: float = 0.6    # Multiplier for USED

    def multiplier_for(self, condition: Condition) -> float:
        """Get multiplier for given condition"""
        match condition:
            case Condition.NEW:
                return self.condition_new
            case Condition.REFURB:
                return self.condition_refurb
            case _:
                return self.condition_used
```

#### ComponentValuationInput

Input for a single component to be valued:

```python
@dataclass
class ComponentValuationInput:
    component_type: ComponentType  # Type of component
    quantity: float                # Amount (GB, TB, count)
    label: str                     # Human-readable description
```

#### ValuationLine

Represents a single deduction line in the breakdown:

```python
@dataclass
class ValuationLine:
    label: str                    # "16GB DDR4 RAM"
    component_type: ComponentType # ComponentType.RAM
    quantity: float               # 16
    unit_value: float            # 2.50
    condition_multiplier: float  # 0.75 for REFURB
    deduction_usd: float         # 30.00
```

#### ValuationResult

Complete valuation with breakdown:

```python
@dataclass
class ValuationResult:
    listing_price_usd: float      # Original price
    adjusted_price_usd: float     # After deductions
    lines: list[ValuationLine]    # Breakdown of deductions

    @property
    def total_deductions(self) -> float:
        return sum(line.deduction_usd for line in self.lines)
```

### Core Function: compute_adjusted_price()

The main valuation function:

```python
def compute_adjusted_price(
    listing_price_usd: float,
    condition: Condition,
    rules: Iterable[ValuationRuleData],
    components: Iterable[ComponentValuationInput],
) -> ValuationResult:
    """
    Compute adjusted price by applying component-based deductions.

    Algorithm:
    1. Build lookup table of rules by component type
    2. For each component:
       - Find matching rule
       - Calculate quantity (convert TB to GB if needed)
       - Apply condition multiplier
       - Compute deduction: quantity * unit_value * multiplier
    3. Sum all deductions
    4. Return listing_price - total_deductions (minimum 0)
    """
```

### Usage Example

```python
from dealbrain_core.valuation import (
    compute_adjusted_price,
    ValuationRuleData,
    ComponentValuationInput,
)
from dealbrain_core.enums import ComponentType, ComponentMetric, Condition

# Define valuation rules
rules = [
    ValuationRuleData(
        component_type=ComponentType.RAM,
        metric=ComponentMetric.PER_GB,
        unit_value_usd=2.50,
        condition_new=1.0,
        condition_refurb=0.75,
        condition_used=0.60,
    ),
    ValuationRuleData(
        component_type=ComponentType.SSD,
        metric=ComponentMetric.PER_GB,
        unit_value_usd=0.08,
        condition_new=1.0,
        condition_refurb=0.80,
        condition_used=0.65,
    ),
]

# Define components in the listing
components = [
    ComponentValuationInput(
        component_type=ComponentType.RAM,
        quantity=16,
        label="16GB DDR4 RAM",
    ),
    ComponentValuationInput(
        component_type=ComponentType.SSD,
        quantity=512,
        label="512GB NVMe SSD",
    ),
]

# Compute adjusted price
result = compute_adjusted_price(
    listing_price_usd=500.00,
    condition=Condition.REFURB,
    rules=rules,
    components=components,
)

print(f"Original Price: ${result.listing_price_usd:.2f}")
print(f"Adjusted Price: ${result.adjusted_price_usd:.2f}")
print(f"Total Deductions: ${result.total_deductions:.2f}")

for line in result.lines:
    print(f"  - {line.label}: -${line.deduction_usd:.2f}")

# Output:
# Original Price: $500.00
# Adjusted Price: $440.32
# Total Deductions: $59.68
#   - 16GB DDR4 RAM: -$30.00    (16 * 2.50 * 0.75)
#   - 512GB NVMe SSD: -$26.62   (512 * 0.08 * 0.65)
```

### Special Handling

#### TB to GB Conversion

When metric is `PER_TB`, quantity is divided by 1024:

```python
if rule.metric == ComponentMetric.PER_TB:
    quantity = quantity / 1024
```

#### Minimum Price Floor

Adjusted price never goes below zero:

```python
adjusted_price = max(listing_price_usd - total_deductions, 0.0)
```

---

## Scoring System

**File:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/scoring.py`

The scoring system computes composite scores from weighted metrics and calculates price-to-performance ratios.

### ListingMetrics Dataclass

Container for all performance metrics:

```python
@dataclass
class ListingMetrics:
    cpu_mark_multi: float | None = None      # Multi-thread CPU score
    cpu_mark_single: float | None = None     # Single-thread CPU score
    gpu_score: float | None = None           # GPU performance score
    perf_per_watt: float | None = None       # Power efficiency
    ram_capacity: float | None = None        # RAM capacity score
    expandability: float | None = None       # Upgrade potential
    encoder_capability: float | None = None  # Video encoding
    ports_fit: float | None = None           # Port availability score
```

### Core Functions

#### compute_composite_score()

Aggregate multiple metrics into a single score:

```python
def compute_composite_score(
    weights: Mapping[str, float],
    metrics: ListingMetrics
) -> float:
    """
    Compute weighted average of metrics.

    Args:
        weights: Dict mapping metric names to weights (e.g., {"cpu_mark_multi": 0.4})
        metrics: ListingMetrics instance

    Returns:
        Weighted average score (0.0 if no valid metrics)

    Algorithm:
    1. For each weight key:
       - Get metric value from ListingMetrics
       - Skip if None
       - Accumulate: score += value * weight
       - Track total_weight
    2. Return score / total_weight (or 0 if total_weight == 0)
    """
```

**Example:**

```python
from dealbrain_core.scoring import compute_composite_score, ListingMetrics

metrics = ListingMetrics(
    cpu_mark_multi=12000,
    cpu_mark_single=2800,
    gpu_score=8500,
    ram_capacity=32,
)

weights = {
    "cpu_mark_multi": 0.4,
    "cpu_mark_single": 0.2,
    "gpu_score": 0.3,
    "ram_capacity": 0.1,
}

score = compute_composite_score(weights, metrics)
# Result: (12000*0.4 + 2800*0.2 + 8500*0.3 + 32*0.1) / 1.0 = 8313.2
```

#### dollar_per_metric()

Calculate price-to-performance ratio:

```python
def dollar_per_metric(price_usd: float, metric: float | None) -> float | None:
    """
    Calculate dollars per performance unit.

    Args:
        price_usd: Price in USD
        metric: Performance metric value

    Returns:
        Price per metric point, or None if metric is invalid

    Examples:
        dollar_per_metric(400, 10000) -> 0.04  ($0.04 per CPU Mark point)
        dollar_per_metric(400, None) -> None
        dollar_per_metric(400, 0) -> None
    """
    if not metric or metric <= 0:
        return None
    return round(price_usd / metric, 4)
```

#### apply_rule_group_weights()

Apply weighted rule group adjustments:

```python
def apply_rule_group_weights(
    rule_group_adjustments: dict[str, float],
    rule_group_weights: dict[str, float]
) -> float:
    """
    Apply weighted rule group adjustments to compute total valuation adjustment.

    Args:
        rule_group_adjustments: Dict mapping group names to adjustment amounts
        rule_group_weights: Dict mapping group names to weights (should sum to 1.0)

    Returns:
        Total weighted adjustment amount

    Example:
        >>> adjustments = {"cpu_valuation": 50.0, "ram_valuation": 20.0, "gpu_valuation": 100.0}
        >>> weights = {"cpu_valuation": 0.3, "ram_valuation": 0.2, "gpu_valuation": 0.5}
        >>> apply_rule_group_weights(adjustments, weights)
        75.0  # (50*0.3 + 20*0.2 + 100*0.5)
    """
    if not rule_group_weights:
        # If no weights defined, sum all adjustments equally
        return sum(rule_group_adjustments.values())

    total_adjustment = 0.0
    for group_name, adjustment in rule_group_adjustments.items():
        weight = rule_group_weights.get(group_name, 0.0)
        total_adjustment += adjustment * weight

    return total_adjustment
```

#### validate_rule_group_weights()

Validate weight configuration:

```python
def validate_rule_group_weights(weights: dict[str, float]) -> tuple[bool, str | None]:
    """
    Validate that rule group weights are valid.

    Args:
        weights: Dict mapping rule group names to weights

    Returns:
        Tuple of (is_valid, error_message)

    Validation Rules:
    - All weights must be non-negative
    - All weights must be <= 1.0
    - Weights must sum to approximately 1.0 (within 0.01 tolerance)

    Examples:
        >>> validate_rule_group_weights({"cpu": 0.5, "ram": 0.3, "gpu": 0.2})
        (True, None)

        >>> validate_rule_group_weights({"cpu": 0.5, "ram": 0.3})
        (False, "Weights must sum to 1.0 (got 0.800)")

        >>> validate_rule_group_weights({"cpu": -0.2, "ram": 1.2})
        (False, "Weight for 'cpu' must be non-negative (got -0.2)")
    """
```

---

## Rule Evaluator (Legacy)

**File:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/rule_evaluator.py`

The legacy rule evaluator provides simple condition evaluation. This is being superseded by the Rules v2 system (see below).

### ConditionNode

Tree node representing a condition:

```python
@dataclass
class ConditionNode:
    field_name: str | None         # None for group nodes
    operator: str | None           # "equals", "greater_than", etc.
    value: Any | None
    logical_operator: str          # "AND" or "OR"
    children: list[ConditionNode] | None = None

    def is_group(self) -> bool:
        return self.field_name is None and self.children is not None

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Recursively evaluate this condition/group against context."""
```

### Supported Operators

- **Equality:** `equals`, `not_equals`
- **Comparison:** `greater_than`, `less_than`, `gte`, `lte`, `between`
- **String:** `contains`, `starts_with`, `ends_with`
- **Set:** `in`, `not_in`

### evaluate_conditions()

Main evaluation function:

```python
def evaluate_conditions(
    conditions: list[dict],
    context: dict[str, Any]
) -> tuple[bool, list[dict]]:
    """
    Evaluate a list of conditions against a context.

    Returns:
        Tuple of (matched: bool, condition_results: list[dict])

    condition_results contains:
        - condition: Human-readable condition string
        - matched: Whether condition passed
        - actual_value: Value from context
        - expected: Expected value from condition
    """
```

---

## Enumerations

**File:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/enums.py`

Domain enumerations used throughout the application.

### Condition

Listing condition states:

```python
class Condition(str, Enum):
    NEW = "new"
    REFURB = "refurb"
    USED = "used"
```

### RamGeneration

RAM technology types:

```python
class RamGeneration(str, Enum):
    DDR3 = "ddr3"
    DDR4 = "ddr4"
    DDR5 = "ddr5"
    LPDDR4 = "lpddr4"
    LPDDR4X = "lpddr4x"
    LPDDR5 = "lpddr5"
    LPDDR5X = "lpddr5x"
    HBM2 = "hbm2"
    HBM3 = "hbm3"
    UNKNOWN = "unknown"
```

### ComponentType

Types of valued components:

```python
class ComponentType(str, Enum):
    RAM = "ram"
    SSD = "ssd"
    HDD = "hdd"
    OS_LICENSE = "os_license"
    WIFI = "wifi"
    GPU = "gpu"
    MISC = "misc"
```

### ComponentMetric

Measurement units for component valuation:

```python
class ComponentMetric(str, Enum):
    PER_GB = "per_gb"
    PER_TB = "per_tb"
    FLAT = "flat"
    PER_RAM_SPEC_GB = "per_ram_spec_gb"
    PER_RAM_SPEED = "per_ram_speed"
    PER_PRIMARY_STORAGE_GB = "per_primary_storage_gb"
    PER_SECONDARY_STORAGE_GB = "per_secondary_storage_gb"
```

### ListingStatus

Listing lifecycle states:

```python
class ListingStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING = "pending"
```

### PortType

Port and connectivity types:

```python
class PortType(str, Enum):
    USB_A = "usb_a"
    USB_C = "usb_c"
    THUNDERBOLT = "thunderbolt"
    HDMI = "hdmi"
    DISPLAYPORT = "displayport"
    RJ45_1G = "rj45_1g"
    RJ45_2_5G = "rj45_2_5g"
    RJ45_10G = "rj45_10g"
    AUDIO = "audio"
    SDXC = "sdxc"
    PCIE_X16 = "pcie_x16"
    PCIE_X8 = "pcie_x8"
    M2_SLOT = "m2_slot"
    SATA_BAY = "sata_bay"
    OTHER = "other"
```

### StorageMedium

Storage technology types:

```python
class StorageMedium(str, Enum):
    NVME = "nvme"
    SATA_SSD = "sata_ssd"
    HDD = "hdd"
    HYBRID = "hybrid"
    EMMC = "emmc"
    UFS = "ufs"
    UNKNOWN = "unknown"
```

---

## Schemas Package

**Directory:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/`

Pydantic schemas for data validation and serialization.

### Base Schema

**File:** `base.py`

```python
class DealBrainModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,    # Accept alias names
        from_attributes=True      # Allow ORM model conversion
    )
```

All schemas inherit from `DealBrainModel` for consistent configuration.

### Catalog Schemas

**File:** `catalog.py`

#### CPU Schemas

```python
class CpuBase(DealBrainModel):
    name: str
    manufacturer: str
    socket: str | None = None
    cores: int | None = None
    threads: int | None = None
    tdp_w: int | None = None
    igpu_model: str | None = None
    cpu_mark_multi: int | None = None
    cpu_mark_single: int | None = None
    igpu_mark: int | None = None
    release_year: int | None = None
    notes: str | None = None
    passmark_slug: str | None = None
    passmark_category: str | None = None
    passmark_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

class CpuCreate(CpuBase): pass
class CpuRead(CpuBase):
    id: int
    created_at: datetime
    updated_at: datetime
```

#### GPU Schemas

```python
class GpuBase(DealBrainModel):
    name: str
    manufacturer: str
    gpu_mark: int | None = None
    metal_score: int | None = None
    notes: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

class GpuCreate(GpuBase): pass
class GpuRead(GpuBase):
    id: int
    created_at: datetime
    updated_at: datetime
```

#### ValuationRule Schemas

```python
class ValuationRuleBase(DealBrainModel):
    name: str
    component_type: ComponentType
    metric: ComponentMetric
    unit_value_usd: float
    condition_new: float = 1.0
    condition_refurb: float = 0.75
    condition_used: float = 0.6
    age_curve_json: dict[str, Any] | None = None
    notes: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
```

#### Profile Schemas

```python
class ProfileBase(DealBrainModel):
    name: str
    description: str | None = None
    weights_json: dict[str, float]
    is_default: bool = False
```

#### Storage and RAM Schemas

```python
class RamSpecBase(DealBrainModel):
    label: str | None = None
    ddr_generation: RamGeneration = RamGeneration.UNKNOWN
    speed_mhz: int | None = None
    module_count: int | None = None
    capacity_per_module_gb: int | None = None
    total_capacity_gb: int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None

class StorageProfileBase(DealBrainModel):
    label: str | None = None
    medium: StorageMedium = StorageMedium.UNKNOWN
    interface: str | None = None
    form_factor: str | None = None
    capacity_gb: int | None = None
    performance_tier: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
```

### Listing Schemas

**File:** `listing.py`

```python
class ListingLink(DealBrainModel):
    url: str
    label: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        # Ensures http:// or https:// with valid host
        pass

class ListingBase(DealBrainModel):
    title: str
    listing_url: str | None = None
    other_urls: list[ListingLink] = Field(default_factory=list)
    seller: str | None = None
    price_usd: float
    price_date: datetime | None = None
    condition: Condition = Condition.USED
    status: ListingStatus = ListingStatus.ACTIVE

    # Foreign keys
    cpu_id: int | None = None
    gpu_id: int | None = None
    ports_profile_id: int | None = None
    ram_spec_id: int | None = None
    primary_storage_profile_id: int | None = None
    secondary_storage_profile_id: int | None = None

    # Direct fields
    ram_gb: int = 0
    ram_notes: str | None = None
    primary_storage_gb: int = 0
    primary_storage_type: str | None = None
    secondary_storage_gb: int | None = None
    secondary_storage_type: str | None = None

    # Product metadata
    manufacturer: str | None = None
    series: str | None = None
    model_number: str | None = None
    form_factor: str | None = None

class ListingRead(ListingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    adjusted_price_usd: float | None = None
    valuation_breakdown: dict[str, Any] | None = None

    # Performance metrics
    dollar_per_cpu_mark_single: float | None = None
    dollar_per_cpu_mark_single_adjusted: float | None = None
    dollar_per_cpu_mark_multi: float | None = None
    dollar_per_cpu_mark_multi_adjusted: float | None = None

    # Relationships
    cpu: CpuRead | None = None
    gpu: GpuRead | None = None
    ram_spec: RamSpecRead | None = None
```

### Import Schemas

**File:** `imports.py`

```python
class SpreadsheetSeed(DealBrainModel):
    """Data structure for Excel import pipeline"""
    cpus: List[CpuCreate] = Field(default_factory=list)
    gpus: List[GpuCreate] = Field(default_factory=list)
    valuation_rules: List[ValuationRuleCreate] = Field(default_factory=list)
    profiles: List[ProfileCreate] = Field(default_factory=list)
    ports_profiles: List[PortsProfileCreate] = Field(default_factory=list)
    ram_specs: List[RamSpecCreate] = Field(default_factory=list)
    storage_profiles: List[StorageProfileCreate] = Field(default_factory=list)
    listings: List[ListingCreate] = Field(default_factory=list)
```

### Baseline Schemas

**File:** `baseline.py`

Schemas for baseline valuation system:

```python
class BaselineFieldMetadata(BaseModel):
    """Metadata for a single baseline field"""
    field_name: str
    field_type: str
    proper_name: str | None = None
    description: str | None = None
    explanation: str | None = None
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    formula: str | None = None
    dependencies: list[str] | None = None
    nullable: bool = False
    notes: str | None = None
    valuation_buckets: list[dict[str, Any]] | None = None

class BaselineMetadataResponse(DealBrainModel):
    """Response schema for baseline metadata endpoint"""
    version: str
    entities: list[BaselineEntityMetadata] = Field(default_factory=list)
    source_hash: str
    is_active: bool
    schema_version: str | None = None
    generated_at: str | None = None
    ruleset_id: int | None = None
    ruleset_name: str | None = None

class BaselineInstantiateRequest(BaseModel):
    """Request schema for baseline instantiation"""
    baseline_path: str
    create_adjustments_group: bool = True
    actor: str | None = None
```

### Custom Field Schemas

**File:** `custom_field.py`

```python
class CustomFieldDefinitionBase(DealBrainModel):
    entity: str
    key: str
    label: str
    data_type: str = "string"
    description: str | None = None
    required: bool = False
    default_value: Any | None = None
    options: list[str] | None = None
    is_active: bool = True
    is_locked: bool = False
    visibility: str = "public"
    created_by: str | None = None
    validation: dict[str, Any] | None = None
    display_order: int = 100
```

---

## Rules Package (v2)

**Directory:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/`

The Rules v2 system provides flexible condition evaluation and action execution for advanced valuation scenarios.

### Architecture

```
rules/
├── __init__.py          # Public API exports
├── conditions.py        # Condition evaluation
├── actions.py           # Action execution
├── evaluator.py         # Rule orchestration
├── formula.py           # Safe formula evaluation
└── packaging.py         # Ruleset import/export
```

### Conditions System

**File:** `conditions.py`

#### ConditionOperator Enum

```python
class ConditionOperator(str, Enum):
    # Equality
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"

    # Comparison
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    BETWEEN = "between"

    # String
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"

    # Set
    IN = "in"
    NOT_IN = "not_in"

    # Existence
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
```

#### Condition Class

Single evaluatable condition:

```python
class Condition:
    def __init__(
        self,
        field_name: str,        # "cpu.cores", "ram_gb", "custom.warranty_months"
        field_type: str,        # "number", "string", "boolean"
        operator: ConditionOperator,
        value: Any = None
    ):
        self.field_name = field_name
        self.field_type = field_type
        self.operator = operator
        self.value = value

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate condition against context.
        Supports dot notation: "cpu.cores" -> context["cpu"]["cores"]
        """
```

**Example:**

```python
from dealbrain_core.rules import Condition, ConditionOperator

# CPU cores >= 8
condition = Condition(
    field_name="cpu.cores",
    field_type="number",
    operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
    value=8
)

context = {
    "cpu": {"cores": 12, "threads": 24},
    "ram_gb": 32
}

result = condition.evaluate(context)  # True
```

#### ConditionGroup Class

Combine multiple conditions with logical operators:

```python
class LogicalOperator(str, Enum):
    AND = "and"
    OR = "or"
    NOT = "not"

class ConditionGroup:
    def __init__(
        self,
        conditions: list[Condition | ConditionGroup],
        logical_operator: LogicalOperator = LogicalOperator.AND
    ):
        self.conditions = conditions
        self.logical_operator = logical_operator

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate all conditions with logical operator"""
```

**Example:**

```python
from dealbrain_core.rules import Condition, ConditionGroup, LogicalOperator

# (cpu.cores >= 8) AND (ram_gb >= 16)
group = ConditionGroup(
    conditions=[
        Condition("cpu.cores", "number", "gte", 8),
        Condition("ram_gb", "number", "gte", 16)
    ],
    logical_operator=LogicalOperator.AND
)

result = group.evaluate(context)
```

### Actions System

**File:** `actions.py`

#### ActionType Enum

```python
class ActionType(str, Enum):
    FIXED_VALUE = "fixed_value"          # Set specific dollar amount
    PER_UNIT = "per_unit"                # Value based on quantity
    BENCHMARK_BASED = "benchmark_based"  # Value proportional to score
    MULTIPLIER = "multiplier"            # Apply percentage
    ADDITIVE = "additive"                # Add/subtract fixed amount
    FORMULA = "formula"                  # Custom calculation
```

#### Action Class

```python
class Action:
    def __init__(
        self,
        action_type: ActionType,
        metric: str | None = None,          # "ram_gb", "cpu.cpu_mark_multi"
        value_usd: float | None = None,
        unit_type: str | None = None,       # "per_1000_points"
        formula: str | None = None,         # "ram_gb * 2.5 + cpu_mark / 1000"
        modifiers: dict[str, Any] | None = None
    ):
        pass

    def calculate(
        self,
        context: dict[str, Any],
        formula_engine: FormulaEngine = None
    ) -> float:
        """Calculate adjustment value based on action type"""
```

**Action Examples:**

```python
from dealbrain_core.rules import Action, ActionType

# Fixed value: Add $50
action1 = Action(
    action_type=ActionType.FIXED_VALUE,
    value_usd=50.0
)

# Per-unit: $2.50 per GB of RAM
action2 = Action(
    action_type=ActionType.PER_UNIT,
    metric="ram_gb",
    value_usd=2.50
)

# Benchmark-based: $5 per 1000 CPU Mark points
action3 = Action(
    action_type=ActionType.BENCHMARK_BASED,
    metric="cpu.cpu_mark_multi",
    value_usd=5.0,
    unit_type="per_1000_points"
)

# Formula: Custom calculation
action4 = Action(
    action_type=ActionType.FORMULA,
    formula="ram_gb * 2.5 + cpu_mark_multi / 1000 * 5.0"
)

# With condition modifiers
action5 = Action(
    action_type=ActionType.PER_UNIT,
    metric="ram_gb",
    value_usd=2.50,
    modifiers={
        "condition_new": 1.0,
        "condition_refurb": 0.75,
        "condition_used": 0.60
    }
)

context = {
    "ram_gb": 16,
    "cpu": {"cpu_mark_multi": 12000},
    "condition": "refurb"
}

value = action5.calculate(context)  # 16 * 2.50 * 0.75 = 30.00
```

#### ActionEngine

Execute multiple actions:

```python
class ActionEngine:
    def __init__(self, formula_engine: FormulaEngine = None):
        self.formula_engine = formula_engine

    def execute_actions(
        self,
        actions: list[Action],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute multiple actions and return combined results.

        Returns:
            {
                "total_adjustment": float,
                "breakdown": [
                    {"action_type": "per_unit", "metric": "ram_gb", "value": 30.00},
                    ...
                ]
            }
        """
```

### Formula System

**File:** `formula.py`

Safe formula evaluation using AST parsing.

#### FormulaParser

Validates formulas before evaluation:

```python
class FormulaParser:
    """Parse formula strings to ensure they are safe for evaluation"""

    # Allowed operators: +, -, *, /, //, %, **
    ALLOWED_OPERATORS = {
        ast.Add, ast.Sub, ast.Mult, ast.Div,
        ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd
    }

    # Allowed functions: abs, min, max, round, sqrt, floor, ceil, etc.
    ALLOWED_FUNCTIONS = {
        "abs", "min", "max", "round", "int", "float",
        "sum", "sqrt", "pow", "floor", "ceil"
    }

    def parse(self, formula: str) -> ast.Expression:
        """Parse and validate formula safety"""
```

#### FormulaEngine

Evaluate formulas against context:

```python
class FormulaEngine:
    def __init__(self):
        self.parser = FormulaParser()

    def evaluate(self, formula: str, context: dict[str, Any]) -> float:
        """
        Safely evaluate formula against context.

        Examples:
            "ram_gb * 2.5"
            "cpu_mark_multi / 1000 * 5.0"
            "max(ram_gb * 2.5, 50)"
            "ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0"
        """
```

**Formula Examples:**

```python
from dealbrain_core.rules import FormulaEngine

engine = FormulaEngine()

context = {
    "ram_gb": 16,
    "cpu": {"cpu_mark_multi": 12000, "cores": 8},
    "condition": "refurb"
}

# Simple arithmetic
result1 = engine.evaluate("ram_gb * 2.5", context)  # 40.0

# Nested field access
result2 = engine.evaluate("cpu_mark_multi / 1000 * 5", context)  # 60.0

# Functions
result3 = engine.evaluate("max(ram_gb * 2.5, 50)", context)  # 50.0

# Conditional
result4 = engine.evaluate(
    "ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0",
    context
)  # 40.0

# Complex
result5 = engine.evaluate(
    "(ram_gb * 2.5 + cpu_mark_multi / 1000 * 5) * (0.75 if condition == 'refurb' else 1.0)",
    context
)  # (40 + 60) * 0.75 = 75.0
```

### Rule Evaluator

**File:** `evaluator.py`

Orchestrates condition checking and action execution.

#### RuleEvaluationResult

```python
@dataclass
class RuleEvaluationResult:
    rule_id: int
    rule_name: str
    matched: bool
    adjustment_value: float = 0.0
    breakdown: list[dict[str, Any]] | None = None
    error: str | None = None
```

#### RuleEvaluator Class

```python
class RuleEvaluator:
    def __init__(self, formula_engine: FormulaEngine = None):
        self.formula_engine = formula_engine or FormulaEngine()
        self.action_engine = ActionEngine(self.formula_engine)

    def evaluate_rule(
        self,
        rule_id: int,
        rule_name: str,
        conditions: Condition | ConditionGroup | list[Condition],
        actions: list[Action],
        context: dict[str, Any],
        is_active: bool = True
    ) -> RuleEvaluationResult:
        """
        Evaluate a single rule against context.

        Algorithm:
        1. Check if rule is active (skip if not)
        2. Evaluate conditions (return no match if false)
        3. Execute actions
        4. Return result with adjustment value and breakdown
        """
```

**Complete Example:**

```python
from dealbrain_core.rules import (
    RuleEvaluator,
    Condition,
    ConditionGroup,
    Action,
    ActionType,
    build_context_from_listing
)

# Create evaluator
evaluator = RuleEvaluator()

# Define conditions: (cpu.cores >= 8) AND (ram_gb >= 16)
conditions = ConditionGroup(
    conditions=[
        Condition("cpu.cores", "number", "gte", 8),
        Condition("ram_gb", "number", "gte", 16)
    ],
    logical_operator="and"
)

# Define actions
actions = [
    Action(
        action_type=ActionType.PER_UNIT,
        metric="ram_gb",
        value_usd=2.50,
        modifiers={"condition_refurb": 0.75}
    ),
    Action(
        action_type=ActionType.BENCHMARK_BASED,
        metric="cpu.cpu_mark_multi",
        value_usd=5.0,
        unit_type="per_1000_points"
    )
]

# Build context from listing
context = {
    "cpu": {"cores": 12, "cpu_mark_multi": 12000},
    "ram_gb": 16,
    "condition": "refurb"
}

# Evaluate rule
result = evaluator.evaluate_rule(
    rule_id=1,
    rule_name="High-Performance Desktop Valuation",
    conditions=conditions,
    actions=actions,
    context=context,
    is_active=True
)

print(f"Matched: {result.matched}")
print(f"Adjustment: ${result.adjustment_value:.2f}")
print(f"Breakdown: {result.breakdown}")

# Output:
# Matched: True
# Adjustment: $90.00
# Breakdown: [
#     {"action_type": "per_unit", "metric": "ram_gb", "value": 30.0},
#     {"action_type": "benchmark_based", "metric": "cpu.cpu_mark_multi", "value": 60.0}
# ]
```

#### Batch Evaluation

```python
def evaluate_ruleset(
    self,
    rules: list[dict[str, Any]],
    context: dict[str, Any],
    stop_on_first_match: bool = False
) -> list[RuleEvaluationResult]:
    """
    Evaluate multiple rules in a ruleset.

    Args:
        rules: List of rule dictionaries
        context: Context with listing data
        stop_on_first_match: Stop after first matching rule

    Returns:
        List of RuleEvaluationResult for each rule
    """
```

#### Context Builder

```python
def build_context_from_listing(listing: Any) -> dict[str, Any]:
    """
    Build evaluation context from a listing object.

    Extracts:
    - Core listing fields (price_usd, condition, ram_gb, etc.)
    - Nested CPU data (cpu.cores, cpu.cpu_mark_multi, etc.)
    - Nested GPU data
    - RAM spec data
    - Storage profile data
    - Custom fields from attributes_json
    """
```

### Packaging System

**File:** `packaging.py`

Import/export rulesets as `.dbrs` (DealBrain RuleSet) files.

#### RulesetPackage

```python
class RulesetPackage(BaseModel):
    schema_version: str = "1.0"
    metadata: PackageMetadata
    rulesets: List[RulesetExport]
    rule_groups: List[RuleGroupExport]
    rules: List[RuleExport]
    custom_field_definitions: List[CustomFieldDefinition] = []
    examples: List[Dict[str, Any]] = []

    def to_file(self, path: Path) -> None:
        """Write package to .dbrs file"""

    @classmethod
    def from_file(cls, path: Path) -> "RulesetPackage":
        """Load package from .dbrs file"""

    def validate_compatibility(
        self,
        app_version: str,
        available_fields: List[str]
    ) -> Dict[str, Any]:
        """Validate package compatibility with current system"""
```

**Usage:**

```python
from pathlib import Path
from dealbrain_core.rules.packaging import (
    RulesetPackage,
    PackageMetadata,
    create_package_metadata
)

# Create package
metadata = create_package_metadata(
    name="SFF PC Valuation Rules",
    version="1.0.0",
    author="Deal Brain",
    description="Baseline valuation rules for small form factor PCs",
    min_app_version="0.1.0",
    required_custom_fields=["warranty_months"],
    tags=["sff", "baseline", "pc"]
)

package = RulesetPackage(
    metadata=metadata,
    rulesets=[...],
    rule_groups=[...],
    rules=[...],
)

# Export to file
package.to_file(Path("baseline_v1.dbrs"))

# Import from file
loaded = RulesetPackage.from_file(Path("baseline_v1.dbrs"))

# Check compatibility
compat = loaded.validate_compatibility(
    app_version="0.2.0",
    available_fields=["warranty_months", "seller_rating"]
)
print(compat["compatible"])  # True/False
print(compat["warnings"])    # List of compatibility warnings
```

---

## GPU Utilities

**File:** `/mnt/containers/deal-brain/packages/core/dealbrain_core/gpu.py`

GPU-specific calculations for Apple devices.

```python
def compute_gpu_score(
    *,
    gpu_mark: Optional[float],
    metal_score: Optional[float],
    is_apple: bool
) -> Optional[float]:
    """
    Compute composite GPU score.

    For Apple devices:
        80% Metal score + 20% GPU Mark

    For non-Apple devices:
        GPU Mark only

    Returns None if no valid score available.
    """
    if is_apple:
        metal_component = metal_score or 0.0
        gpu_component = gpu_mark or metal_component
        if metal_component or gpu_component:
            return 0.8 * metal_component + 0.2 * gpu_component
        return None

    return float(gpu_mark) if gpu_mark else None
```

---

## Usage Patterns

### From API Service Layer

```python
# apps/api/dealbrain_api/services/listings.py

from dealbrain_core.valuation import compute_adjusted_price, ValuationRuleData
from dealbrain_core.scoring import compute_composite_score, ListingMetrics
from dealbrain_core.enums import ComponentType, ComponentMetric

async def apply_valuation(listing: Listing, rules: list[ValuationRule]):
    # Convert DB models to domain objects
    rule_data = [
        ValuationRuleData(
            component_type=rule.component_type,
            metric=rule.metric,
            unit_value_usd=rule.unit_value_usd,
            condition_new=rule.condition_new,
            condition_refurb=rule.condition_refurb,
            condition_used=rule.condition_used,
        )
        for rule in rules
    ]

    # Compute adjusted price
    result = compute_adjusted_price(
        listing_price_usd=listing.price_usd,
        condition=listing.condition,
        rules=rule_data,
        components=listing.components,
    )

    # Update listing
    listing.adjusted_price_usd = result.adjusted_price_usd
    listing.valuation_breakdown = {
        "lines": [line.__dict__ for line in result.lines],
        "total_deductions": result.total_deductions,
    }
```

### From CLI

```python
# apps/cli/dealbrain_cli/commands/explain.py

from dealbrain_core.valuation import compute_adjusted_price

def explain_listing(listing_id: int):
    # Fetch from database
    listing = db.query(Listing).get(listing_id)
    rules = db.query(ValuationRule).all()

    # Compute valuation
    result = compute_adjusted_price(...)

    # Display breakdown
    console.print(f"Original Price: ${result.listing_price_usd:.2f}")
    console.print(f"Adjusted Price: ${result.adjusted_price_usd:.2f}")
    for line in result.lines:
        console.print(f"  - {line.label}: -${line.deduction_usd:.2f}")
```

---

## Testing Domain Logic

Since domain logic is pure and infrastructure-agnostic, it's straightforward to test:

```python
# tests/test_valuation.py

from dealbrain_core.valuation import compute_adjusted_price, ValuationRuleData
from dealbrain_core.enums import ComponentType, ComponentMetric, Condition

def test_compute_adjusted_price_with_ram():
    rules = [
        ValuationRuleData(
            component_type=ComponentType.RAM,
            metric=ComponentMetric.PER_GB,
            unit_value_usd=2.50,
            condition_refurb=0.75,
        )
    ]

    components = [
        ComponentValuationInput(
            component_type=ComponentType.RAM,
            quantity=16,
            label="16GB RAM",
        )
    ]

    result = compute_adjusted_price(
        listing_price_usd=500.00,
        condition=Condition.REFURB,
        rules=rules,
        components=components,
    )

    assert result.adjusted_price_usd == 470.00
    assert len(result.lines) == 1
    assert result.lines[0].deduction_usd == 30.00
```

---

## Design Benefits

### Infrastructure Independence

Domain logic has zero dependencies on:
- Database (SQLAlchemy, Alembic)
- Web framework (FastAPI, Flask)
- CLI framework (Typer)
- External services

This enables:
- Easy testing without mocks
- Reusability across applications
- Framework migration flexibility

### Type Safety

All domain functions use type hints and dataclasses:

```python
def compute_adjusted_price(
    listing_price_usd: float,
    condition: Condition,
    rules: Iterable[ValuationRuleData],
    components: Iterable[ComponentValuationInput],
) -> ValuationResult:
    # Type-checked inputs and outputs
```

### Explicit Data Flow

No hidden state or side effects:

```python
# Input -> Function -> Output
result = compute_adjusted_price(price, condition, rules, components)

# Result contains all data needed
print(result.adjusted_price_usd)
print(result.total_deductions)
for line in result.lines:
    print(line.label, line.deduction_usd)
```

---

## Summary

The shared domain logic in `packages/core/dealbrain_core/` provides:

1. **Valuation Engine** - Component-based pricing with condition multipliers
2. **Scoring System** - Weighted metric aggregation and price/performance ratios
3. **Rule Evaluator (Legacy)** - Simple condition evaluation
4. **Rules v2 System** - Advanced rule engine with formulas and packaging
5. **Enumerations** - Shared constants for conditions, components, ports, storage
6. **Schemas** - Pydantic models for data validation
7. **GPU Utilities** - Apple Metal score calculations

**Key Principles:**
- Pure functions without side effects
- Infrastructure independence
- Type-safe interfaces
- Testable in isolation
- Shared across API and CLI

**File References:**
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/valuation.py`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/scoring.py`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/rule_evaluator.py`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/enums.py`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/`
- `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/`
