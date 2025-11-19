"""Pydantic schemas for valuation rules API"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, model_validator
from dealbrain_core.rules import ActionType, ConditionOperator, LogicalOperator


# --- Condition Schemas ---


class ConditionSchema(BaseModel):
    """Schema for a rule condition"""

    field_name: str = Field(..., description="Field name (supports dot notation)")
    field_type: str = Field(..., description="Field data type")
    operator: str = Field(..., description="Comparison operator")
    value: Any = Field(None, description="Comparison value")
    logical_operator: str | None = Field(None, description="Logical operator for grouping")
    group_order: int = Field(0, description="Order within condition group")


# --- Action Schemas ---


class ActionSchema(BaseModel):
    """Schema for a rule action"""

    action_type: str = Field(..., description="Action type (fixed_value, per_unit, etc.)")
    metric: str | None = Field(None, description="Metric for calculation")
    value_usd: float | None = Field(None, description="Value in USD")
    unit_type: str | None = Field(None, description="Unit type for benchmark calculations")
    formula: str | None = Field(None, description="Custom formula")
    modifiers: dict[str, Any] = Field(
        default_factory=dict,
        description="Modifiers including min_usd, max_usd, clamp flag, explanation, formula_notes, unit",
    )

    @model_validator(mode="after")
    def validate_metric_requirements(self) -> "ActionSchema":
        """Ensure metric is provided for metric-dependent action types."""
        if self.action_type == "per_unit" and not (self.metric and str(self.metric).strip()):
            raise ValueError("metric is required when action_type is 'per_unit'")
        return self


# --- Rule Schemas ---


class RuleCreateRequest(BaseModel):
    """Request schema for creating a rule"""

    group_id: int = Field(..., description="Rule group ID")
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    priority: int = Field(100, description="Rule priority")
    evaluation_order: int = Field(100, description="Evaluation order")
    is_active: bool = Field(True, description="Whether rule is active")
    conditions: list[ConditionSchema] = Field(default_factory=list)
    actions: list[ActionSchema] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleUpdateRequest(BaseModel):
    """Request schema for updating a rule"""

    name: str | None = None
    description: str | None = None
    priority: int | None = None
    evaluation_order: int | None = None
    is_active: bool | None = None
    conditions: list[ConditionSchema] | None = None
    actions: list[ActionSchema] | None = None
    metadata: dict[str, Any] | None = None


class RuleResponse(BaseModel):
    """Response schema for a rule"""

    id: int
    group_id: int
    name: str
    description: str | None
    priority: int
    is_active: bool
    evaluation_order: int
    version: int
    created_by: str | None
    created_at: datetime
    updated_at: datetime
    conditions: list[ConditionSchema]
    actions: list[ActionSchema]
    metadata: dict[str, Any]

    class Config:
        from_attributes = True


# --- Rule Group Schemas ---


class RuleGroupCreateRequest(BaseModel):
    """Request schema for creating a rule group"""

    ruleset_id: int = Field(..., description="Ruleset ID")
    name: str = Field(..., min_length=1, max_length=128)
    category: str = Field(..., min_length=1, max_length=64)
    description: str | None = None
    display_order: int = Field(100)
    weight: float = Field(1.0, ge=0.0, le=1.0)
    is_active: bool = Field(True, description="Whether this group is enabled")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata for the group"
    )
    basic_managed: bool | None = Field(
        None, description="Whether this group is managed by Basic mode"
    )
    entity_key: str | None = Field(
        None, description="Entity type for basic-managed groups (Listing, CPU, GPU, etc.)"
    )

    @model_validator(mode="after")
    def validate_basic_managed_requirements(self) -> "RuleGroupCreateRequest":
        """Ensure basic_managed groups have entity_key."""
        if self.basic_managed and not self.entity_key:
            raise ValueError("entity_key is required when basic_managed is true")
        return self


class RuleGroupUpdateRequest(BaseModel):
    """Request schema for updating a rule group"""

    name: str | None = None
    category: str | None = None
    description: str | None = None
    display_order: int | None = None
    weight: float | None = Field(None, ge=0.0)
    is_active: bool | None = None
    metadata: dict[str, Any] | None = Field(None, description="Arbitrary metadata for the group")
    basic_managed: bool | None = Field(
        None, description="Whether this group is managed by Basic mode"
    )
    entity_key: str | None = Field(
        None, description="Entity type for basic-managed groups (Listing, CPU, GPU, etc.)"
    )

    @model_validator(mode="after")
    def validate_basic_managed_requirements(self) -> "RuleGroupUpdateRequest":
        """Ensure basic_managed groups have entity_key."""
        if self.basic_managed is not None and self.basic_managed and not self.entity_key:
            raise ValueError("entity_key is required when basic_managed is true")
        return self


class RuleGroupResponse(BaseModel):
    """Response schema for a rule group"""

    id: int
    ruleset_id: int
    name: str
    category: str
    description: str | None
    display_order: int
    weight: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]
    basic_managed: bool | None = None
    entity_key: str | None = None
    rules: list[RuleResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# --- Ruleset Schemas ---


class RulesetCreateRequest(BaseModel):
    """Request schema for creating a ruleset"""

    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    version: str = Field("1.0.0", max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(True, description="Whether this ruleset can be applied")
    priority: int = Field(
        10,
        ge=0,
        description="Lower numbers run first when multiple rulesets are active",
    )
    conditions: dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized condition tree controlling when this ruleset applies",
    )


class RulesetUpdateRequest(BaseModel):
    """Request schema for updating a ruleset"""

    name: str | None = None
    description: str | None = None
    version: str | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None
    priority: int | None = Field(
        None,
        ge=0,
        description="Lower numbers run first when multiple rulesets are active",
    )
    conditions: dict[str, Any] | None = Field(
        None,
        description="Serialized condition tree controlling when this ruleset applies",
    )


class RulesetResponse(BaseModel):
    """Response schema for a ruleset"""

    id: int
    name: str
    description: str | None
    version: str
    is_active: bool
    created_by: str | None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]
    priority: int
    conditions: dict[str, Any]
    rule_groups: list[RuleGroupResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# --- Preview Schemas ---


class RulePreviewRequest(BaseModel):
    """Request schema for previewing a rule"""

    conditions: list[ConditionSchema] = Field(default_factory=list)
    actions: list[ActionSchema] = Field(default_factory=list)
    sample_size: int = Field(10, ge=1, le=50)
    category_filter: dict[str, Any] | None = None


class SampleListingResult(BaseModel):
    """Sample listing evaluation result"""

    id: int
    title: str
    original_price: float
    adjustment: float | None = None
    adjusted_price: float | None = None
    price_change_pct: float | None = None


class RulePreviewResponse(BaseModel):
    """Response schema for rule preview"""

    statistics: dict[str, Any]
    sample_matched_listings: list[SampleListingResult]
    sample_non_matched_listings: list[SampleListingResult]


# --- Evaluation Schemas ---


class RuleEvaluationResponse(BaseModel):
    """Response schema for rule evaluation"""

    listing_id: int
    original_price: float
    total_adjustment: float
    adjusted_price: float
    ruleset_id: int
    ruleset_name: str
    matched_rules_count: int
    matched_rules: list[dict[str, Any]]


class BulkEvaluationRequest(BaseModel):
    """Request schema for bulk evaluation"""

    listing_ids: list[int] = Field(..., min_items=1, max_items=1000)
    ruleset_id: int | None = None


class ApplyRulesetRequest(BaseModel):
    """Request schema for applying a ruleset"""

    ruleset_id: int | None = None
    listing_ids: list[int] | None = None  # If None, applies to all


# --- Audit Schemas ---


class AuditLogResponse(BaseModel):
    """Response schema for audit log entry"""

    id: int
    rule_id: int | None
    action: str
    actor: str | None
    changes: dict[str, Any] | None
    impact_summary: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Import/Export Schemas ---


class RuleExportRequest(BaseModel):
    """Request schema for exporting rules"""

    ruleset_id: int
    format: str = Field("json", description="Export format: json, yaml, csv, excel")
    include_inactive: bool = Field(False)


class RuleImportRequest(BaseModel):
    """Request schema for importing rules"""

    format: str = Field(..., description="Import format: json, yaml, csv")
    data: dict[str, Any] | list[dict[str, Any]]
    target_ruleset_id: int | None = None  # If None, creates new ruleset
    overwrite_existing: bool = Field(False)


# --- Package Schemas ---


class PackageMetadataRequest(BaseModel):
    """Request schema for package metadata"""

    name: str = Field(..., min_length=1, description="Package name")
    version: str = Field(..., description="Semantic version (e.g., '1.0.0')")
    author: str | None = Field(None, description="Package author")
    description: str | None = Field(None, description="Package description")
    min_app_version: str | None = Field(None, description="Minimum app version required")
    required_custom_fields: list[str] | None = Field(
        None, description="Required custom field names"
    )
    tags: list[str] | None = Field(None, description="Package tags")
    include_examples: bool = Field(False, description="Include example listings")


class PackageExportResponse(BaseModel):
    """Response schema for package export preview"""

    package_name: str
    package_version: str
    rulesets_count: int
    rule_groups_count: int
    rules_count: int
    custom_fields_count: int
    dependencies: dict[str, Any]
    estimated_size_kb: float
    readme: str


class PackageInstallResponse(BaseModel):
    """Response schema for package installation"""

    success: bool
    message: str
    rulesets_created: int
    rulesets_updated: int
    rule_groups_created: int
    rules_created: int
    warnings: list[str] = Field(default_factory=list)


# --- Formula Validation Schemas ---


class FormulaValidationRequest(BaseModel):
    """Request schema for validating a formula"""

    formula: str = Field(..., min_length=1, description="Formula to validate")
    entity_type: str = Field(
        "Listing", description="Entity type for field context (Listing, CPU, GPU, etc.)"
    )
    sample_context: dict[str, Any] | None = Field(
        None, description="Optional sample context for preview calculation"
    )


class FormulaValidationError(BaseModel):
    """Schema for a formula validation error"""

    message: str = Field(..., description="Error message")
    severity: str = Field("error", description="Error severity (error, warning, info)")
    position: int | None = Field(
        None, description="Character position in formula where error occurred"
    )
    suggestion: str | None = Field(None, description="Suggested fix for the error")


class FormulaValidationResponse(BaseModel):
    """Response schema for formula validation"""

    valid: bool = Field(..., description="Whether the formula is valid")
    errors: list[FormulaValidationError] = Field(
        default_factory=list, description="List of validation errors"
    )
    preview: float | None = Field(None, description="Preview calculation result with sample data")
    used_fields: list[str] = Field(
        default_factory=list, description="List of fields referenced in the formula"
    )
    available_fields: list[str] = Field(
        default_factory=list, description="List of available fields for the entity type"
    )


# --- Legacy aliases (backwards compatibility) ---

RulesetCreate = RulesetCreateRequest
RulesetUpdate = RulesetUpdateRequest
RuleGroupCreate = RuleGroupCreateRequest
RuleGroupUpdate = RuleGroupUpdateRequest
RuleCreate = RuleCreateRequest
RuleUpdate = RuleUpdateRequest
ConditionCreate = ConditionSchema
ActionCreate = ActionSchema
