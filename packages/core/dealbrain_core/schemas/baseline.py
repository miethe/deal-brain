"""Pydantic schemas for baseline valuation API"""

from typing import Any

from pydantic import BaseModel, Field

from .base import DealBrainModel

# --- Field-level metadata ---

class BaselineFieldMetadata(BaseModel):
    """Metadata for a single baseline field"""

    field_name: str = Field(..., description="Field identifier (e.g., 'condition_multiplier')")
    field_type: str = Field(..., description="Field data type")
    proper_name: str | None = Field(None, description="Human-readable field name")
    description: str | None = Field(None, description="Short field description")
    explanation: str | None = Field(None, description="Detailed explanation for UI")
    unit: str | None = Field(None, description="Unit type (USD, multiplier, etc.)")
    min_value: float | None = Field(None, description="Minimum value from buckets")
    max_value: float | None = Field(None, description="Maximum value from buckets")
    formula: str | None = Field(None, description="Formula expression if applicable")
    dependencies: list[str] | None = Field(None, description="List of field dependencies")
    nullable: bool = Field(False, description="Whether field can be null")
    notes: str | None = Field(None, description="Additional notes")
    valuation_buckets: list[dict[str, Any]] | None = Field(None, description="Valuation bucket definitions")


# --- Entity-level metadata ---

class BaselineEntityMetadata(BaseModel):
    """Metadata for a baseline entity"""

    entity_key: str = Field(..., description="Entity identifier (e.g., 'Listing', 'CPU')")
    fields: list[BaselineFieldMetadata] = Field(default_factory=list, description="List of fields in this entity")


# --- Baseline metadata response ---

class BaselineMetadataResponse(DealBrainModel):
    """Response schema for baseline metadata endpoint"""

    version: str = Field(..., description="Baseline version string")
    entities: list[BaselineEntityMetadata] = Field(default_factory=list, description="Entity metadata")
    source_hash: str = Field(..., description="SHA256 hash of source baseline")
    is_active: bool = Field(..., description="Whether this baseline is currently active")
    schema_version: str | None = Field(None, description="Schema version from baseline JSON")
    generated_at: str | None = Field(None, description="Generation timestamp from baseline JSON")
    ruleset_id: int | None = Field(None, description="Associated ruleset ID if exists")
    ruleset_name: str | None = Field(None, description="Associated ruleset name if exists")


# --- Baseline instantiation ---

class BaselineInstantiateRequest(BaseModel):
    """Request schema for baseline instantiation"""

    baseline_path: str = Field(..., description="Path to baseline JSON file")
    create_adjustments_group: bool = Field(
        True,
        description="Whether to create a 'Basic · Adjustments' group in non-baseline ruleset"
    )
    actor: str | None = Field(None, description="User/system actor performing instantiation")


class BaselineInstantiateResponse(DealBrainModel):
    """Response schema for baseline instantiation"""

    ruleset_id: int | None = Field(None, description="Created or existing ruleset ID")
    version: str = Field(..., description="Baseline version")
    created: bool = Field(..., description="Whether a new ruleset was created (false if already exists)")
    hash_match: bool = Field(..., description="Whether source hash matched existing ruleset")
    source_hash: str = Field(..., description="SHA256 hash of the baseline")
    ruleset_name: str | None = Field(None, description="Name of the ruleset")
    created_groups: int = Field(0, description="Number of groups created")
    created_rules: int = Field(0, description="Number of rules created")
    skipped_reason: str | None = Field(None, description="Reason for skipping if applicable")


# --- Baseline diff ---

class BaselineFieldDiff(BaseModel):
    """Diff for a single field"""

    entity_key: str = Field(..., description="Entity this field belongs to")
    field_name: str = Field(..., description="Field identifier")
    proper_name: str | None = Field(None, description="Human-readable name")
    change_type: str = Field(..., description="Type of change: 'added', 'changed', or 'removed'")
    old_value: dict[str, Any] | None = Field(None, description="Previous field definition (for changed/removed)")
    new_value: dict[str, Any] | None = Field(None, description="New field definition (for added/changed)")
    value_diff: dict[str, Any] | None = Field(None, description="Specific value changes for 'changed' type")


class BaselineDiffSummary(BaseModel):
    """Summary statistics for diff operation"""

    added_count: int = Field(0, description="Number of fields added")
    changed_count: int = Field(0, description="Number of fields changed")
    removed_count: int = Field(0, description="Number of fields removed")
    total_changes: int = Field(0, description="Total number of changes")


class BaselineDiffRequest(BaseModel):
    """Request schema for baseline diff"""

    candidate_json: dict[str, Any] = Field(..., description="Candidate baseline JSON structure to compare")
    actor: str | None = Field(None, description="User/system actor performing diff")


class BaselineDiffResponse(DealBrainModel):
    """Response schema for baseline diff"""

    added: list[BaselineFieldDiff] = Field(default_factory=list, description="Fields added in candidate")
    changed: list[BaselineFieldDiff] = Field(default_factory=list, description="Fields changed in candidate")
    removed: list[BaselineFieldDiff] = Field(default_factory=list, description="Fields removed in candidate")
    summary: BaselineDiffSummary = Field(..., description="Summary statistics")
    current_version: str | None = Field(None, description="Current baseline version")
    candidate_version: str | None = Field(None, description="Candidate baseline version")


# --- Baseline adopt ---

class BaselineAdoptRequest(BaseModel):
    """Request schema for baseline adoption"""

    candidate_json: dict[str, Any] = Field(..., description="Candidate baseline JSON to adopt")
    selected_changes: list[str] | None = Field(
        None,
        description="Optional list of field IDs to adopt (entity.field format). If omitted, all changes are adopted."
    )
    trigger_recalculation: bool = Field(
        False,
        description="Whether to trigger listing recalculation after adoption"
    )
    actor: str | None = Field(None, description="User/system actor performing adoption")


class BaselineAdoptResponse(DealBrainModel):
    """Response schema for baseline adoption"""

    new_ruleset_id: int = Field(..., description="ID of the newly created ruleset")
    new_version: str = Field(..., description="Version string of the new ruleset")
    changes_applied: int = Field(..., description="Number of changes applied")
    recalculation_job_id: str | None = Field(None, description="Job ID if recalculation was triggered")
    adopted_fields: list[str] = Field(default_factory=list, description="List of adopted field IDs")
    skipped_fields: list[str] = Field(default_factory=list, description="List of fields that were in diff but not adopted")
    previous_ruleset_id: int | None = Field(None, description="ID of the previous active baseline ruleset")
    audit_log_id: int | None = Field(None, description="ID of the audit log entry")


# --- Baseline hydration ---

class HydrateBaselineRequest(BaseModel):
    """Request schema for baseline rule hydration"""

    actor: str | None = Field("system", description="User/system actor performing hydration")


class HydrationSummaryItem(BaseModel):
    """Summary item for a single hydrated rule"""

    original_rule_id: int = Field(..., description="ID of the original placeholder rule")
    field_name: str = Field(..., description="Name of the field that was hydrated")
    field_type: str = Field(..., description="Type of field (enum_multiplier, formula, fixed, etc.)")
    expanded_rule_ids: list[int] = Field(default_factory=list, description="IDs of the expanded rules created")


class HydrateBaselineResponse(DealBrainModel):
    """Response schema for baseline rule hydration"""

    status: str = Field(..., description="Hydration status (success, error, etc.)")
    ruleset_id: int = Field(..., description="ID of the ruleset that was hydrated")
    hydrated_rule_count: int = Field(..., description="Number of placeholder rules that were hydrated")
    created_rule_count: int = Field(..., description="Total number of expanded rules created")
    hydration_summary: list[HydrationSummaryItem] = Field(default_factory=list, description="Summary of hydration per rule")


__all__ = [
    "BaselineFieldMetadata",
    "BaselineEntityMetadata",
    "BaselineMetadataResponse",
    "BaselineInstantiateRequest",
    "BaselineInstantiateResponse",
    "BaselineFieldDiff",
    "BaselineDiffSummary",
    "BaselineDiffRequest",
    "BaselineDiffResponse",
    "BaselineAdoptRequest",
    "BaselineAdoptResponse",
    "HydrateBaselineRequest",
    "HydrationSummaryItem",
    "HydrateBaselineResponse",
]
