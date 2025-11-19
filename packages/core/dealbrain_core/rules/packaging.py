"""
Ruleset packaging and distribution system.

Handles export/import of complete rulesets with dependency resolution,
compatibility checking, and validation.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field, validator


class PackageMetadata(BaseModel):
    """Metadata for a ruleset package."""

    name: str = Field(..., description="Human-readable package name")
    version: str = Field(..., description="Semantic version (e.g., '1.2.0')")
    author: str = Field(..., description="Package creator")
    description: str = Field(..., description="Package description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    compatibility: Dict[str, Any] = Field(
        default_factory=dict, description="Compatibility requirements"
    )
    tags: List[str] = Field(default_factory=list)

    @validator("version")
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        parts = v.split(".")
        if len(parts) != 3:
            raise ValueError("Version must be in format 'X.Y.Z'")
        if not all(p.isdigit() for p in parts):
            raise ValueError("Version parts must be integers")
        return v


class RulesetExport(BaseModel):
    """Exported ruleset data."""

    id: int
    name: str
    description: Optional[str]
    version: str
    is_active: bool
    metadata_json: Dict[str, Any]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class RuleGroupExport(BaseModel):
    """Exported rule group data."""

    id: int
    ruleset_id: int
    name: str
    category: str
    description: Optional[str]
    display_order: int
    weight: float
    metadata_json: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata for the group"
    )
    created_at: datetime
    updated_at: datetime


class RuleConditionExport(BaseModel):
    """Exported rule condition data."""

    id: int
    rule_id: int
    parent_condition_id: Optional[int]
    field_name: str
    field_type: str
    operator: str
    value_json: Any
    logical_operator: Optional[str]
    group_order: int


class RuleActionExport(BaseModel):
    """Exported rule action data."""

    id: int
    rule_id: int
    action_type: str
    metric: Optional[str]
    value_usd: Optional[float]
    unit_type: Optional[str]
    formula: Optional[str]
    modifiers_json: Dict[str, Any]
    display_order: int


class RuleExport(BaseModel):
    """Exported rule data with conditions and actions."""

    id: int
    group_id: int
    name: str
    description: Optional[str]
    priority: int
    is_active: bool
    evaluation_order: int
    metadata_json: Dict[str, Any]
    created_by: Optional[str]
    version: int
    created_at: datetime
    updated_at: datetime
    conditions: List[RuleConditionExport]
    actions: List[RuleActionExport]


class CustomFieldDefinition(BaseModel):
    """Custom field definition for compatibility."""

    field_name: str
    field_type: str
    entity_type: str
    description: Optional[str]
    required: bool = False
    default_value: Optional[Any] = None


class RulesetPackage(BaseModel):
    """Complete ruleset package in .dbrs format."""

    schema_version: str = Field(default="1.0", description="Package format version")
    metadata: PackageMetadata
    rulesets: List[RulesetExport]
    rule_groups: List[RuleGroupExport]
    rules: List[RuleExport]
    custom_field_definitions: List[CustomFieldDefinition] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(
        default_factory=list, description="Example listings or test cases"
    )

    def to_json(self, indent: int = 2) -> str:
        """Serialize package to JSON string."""
        return self.json(indent=indent, exclude_none=True)

    def to_file(self, path: Path) -> None:
        """Write package to .dbrs file."""
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def from_json(cls, json_str: str) -> "RulesetPackage":
        """Deserialize package from JSON string."""
        return cls.parse_raw(json_str)

    @classmethod
    def from_file(cls, path: Path) -> "RulesetPackage":
        """Load package from .dbrs file."""
        with open(path, "r") as f:
            return cls.parse_raw(f.read())

    def validate_compatibility(
        self, app_version: str, available_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Validate package compatibility with current system.

        Returns dict with:
        - compatible: bool
        - missing_fields: List[str]
        - warnings: List[str]
        """
        result = {"compatible": True, "missing_fields": [], "warnings": []}

        # Check app version compatibility
        min_version = self.metadata.compatibility.get("min_app_version")
        if min_version and self._compare_versions(app_version, min_version) < 0:
            result["compatible"] = False
            result["warnings"].append(
                f"Requires app version {min_version} or higher (current: {app_version})"
            )

        # Check required custom fields
        required_fields = self.metadata.compatibility.get("required_custom_fields", [])
        missing = set(required_fields) - set(available_fields)
        if missing:
            result["missing_fields"] = list(missing)
            result["warnings"].append(f"Missing required custom fields: {', '.join(missing)}")

        return result

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two semantic versions.
        Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        parts1 = [int(p) for p in v1.split(".")]
        parts2 = [int(p) for p in v2.split(".")]

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        return 0

    def get_dependencies(self) -> Dict[str, List[str]]:
        """
        Extract dependencies from the package.

        Returns dict with:
        - custom_fields: List of required custom field names
        - referenced_entities: List of entity types referenced
        """
        dependencies = {"custom_fields": [], "referenced_entities": set()}

        # Extract custom fields from conditions
        for rule in self.rules:
            for condition in rule.conditions:
                if condition.field_name.startswith("custom."):
                    field_name = condition.field_name.replace("custom.", "")
                    dependencies["custom_fields"].append(field_name)

                # Track entity types
                if "." in condition.field_name:
                    entity = condition.field_name.split(".")[0]
                    dependencies["referenced_entities"].add(entity)

        dependencies["custom_fields"] = list(set(dependencies["custom_fields"]))
        dependencies["referenced_entities"] = list(dependencies["referenced_entities"])

        return dependencies

    def generate_readme(self) -> str:
        """Generate README content for the package."""
        lines = [
            f"# {self.metadata.name}",
            "",
            f"**Version:** {self.metadata.version}",
            f"**Author:** {self.metadata.author}",
            f"**Created:** {self.metadata.created_at.strftime('%Y-%m-%d')}",
            "",
            "## Description",
            "",
            self.metadata.description,
            "",
            "## Contents",
            "",
            f"- **Rulesets:** {len(self.rulesets)}",
            f"- **Rule Groups:** {len(self.rule_groups)}",
            f"- **Rules:** {len(self.rules)}",
            "",
        ]

        if self.custom_field_definitions:
            lines.extend(
                [
                    "## Required Custom Fields",
                    "",
                ]
            )
            for field in self.custom_field_definitions:
                lines.append(
                    f"- `{field.field_name}` ({field.field_type}): "
                    f"{field.description or 'No description'}"
                )
            lines.append("")

        if self.metadata.compatibility:
            lines.extend(
                [
                    "## Compatibility",
                    "",
                ]
            )
            for key, value in self.metadata.compatibility.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")

        if self.examples:
            lines.extend(
                [
                    "## Examples",
                    "",
                    f"This package includes {len(self.examples)} example(s) for testing.",
                    "",
                ]
            )

        return "\n".join(lines)


class PackageBuilder:
    """Builder for creating ruleset packages."""

    def __init__(self):
        self.rulesets: List[RulesetExport] = []
        self.rule_groups: List[RuleGroupExport] = []
        self.rules: List[RuleExport] = []
        self.custom_fields: List[CustomFieldDefinition] = []
        self.examples: List[Dict[str, Any]] = []

    def add_ruleset(self, ruleset: RulesetExport) -> "PackageBuilder":
        """Add a ruleset to the package."""
        self.rulesets.append(ruleset)
        return self

    def add_rule_group(self, group: RuleGroupExport) -> "PackageBuilder":
        """Add a rule group to the package."""
        self.rule_groups.append(group)
        return self

    def add_rule(self, rule: RuleExport) -> "PackageBuilder":
        """Add a rule to the package."""
        self.rules.append(rule)
        return self

    def add_custom_field(self, field: CustomFieldDefinition) -> "PackageBuilder":
        """Add a custom field definition to the package."""
        self.custom_fields.append(field)
        return self

    def add_example(self, example: Dict[str, Any]) -> "PackageBuilder":
        """Add an example to the package."""
        self.examples.append(example)
        return self

    def build(self, metadata: PackageMetadata) -> RulesetPackage:
        """Build the complete package."""
        return RulesetPackage(
            metadata=metadata,
            rulesets=self.rulesets,
            rule_groups=self.rule_groups,
            rules=self.rules,
            custom_field_definitions=self.custom_fields,
            examples=self.examples,
        )


def create_package_metadata(
    name: str,
    version: str,
    author: str,
    description: str,
    min_app_version: Optional[str] = None,
    required_custom_fields: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> PackageMetadata:
    """Helper to create package metadata."""
    compatibility = {}
    if min_app_version:
        compatibility["min_app_version"] = min_app_version
    if required_custom_fields:
        compatibility["required_custom_fields"] = required_custom_fields

    return PackageMetadata(
        name=name,
        version=version,
        author=author,
        description=description,
        compatibility=compatibility,
        tags=tags or [],
    )
