# Baseline Ruleset Packaging Documentation

## Overview

The `RulesetPackagingService` provides special handling for baseline rulesets during export and import operations. Baseline rulesets are system-provided valuation rules that serve as the foundation for customer-specific adjustments.

## Key Features

### Baseline Identification

Baseline rulesets are identified by the `system_baseline: true` flag in their `metadata_json`:

```python
{
    "system_baseline": True,
    "source_version": "1.0.0",
    "source_hash": "abc123def456",
    "read_only": True,
    "priority": 1  # Must be ≤ 5
}
```

### Export Behavior

#### Default Export (Customer Rulesets)
By default, baseline rulesets are **excluded** from exports to prevent accidental distribution:

```python
# This will fail for baseline rulesets
package = await packaging_service.export_ruleset_to_package(
    session,
    baseline_ruleset_id,
    metadata
)
# ValueError: Ruleset X is a baseline ruleset. Use include_baseline=True
```

#### Explicit Baseline Export
To export baseline rulesets, use the `include_baseline` parameter:

```python
package = await packaging_service.export_ruleset_to_package(
    session,
    baseline_ruleset_id,
    metadata,
    include_baseline=True  # Required for baseline export
)
```

### Import Behavior

#### Baseline Import Modes

The service supports two modes for importing baseline rulesets:

1. **Version Mode (Default)** - Creates a new versioned ruleset:
   ```python
   result = await packaging_service.install_package(
       session,
       package,
       baseline_import_mode="version"  # Default
   )
   # Creates: "System: Baseline v1.1" (inactive by default)
   ```

2. **Replace Mode** - Updates existing baseline (use with caution):
   ```python
   result = await packaging_service.install_package(
       session,
       package,
       baseline_import_mode="replace"
   )
   # Updates existing baseline with same source_hash
   ```

#### Version Numbering

When importing with `version` mode:
- Extracts version from ruleset name (e.g., "System: Baseline v1.0")
- Automatically increments to next available version
- New versions start as **inactive** to prevent immediate impact

#### Priority Validation

Baseline rulesets must have priority ≤ 5 to ensure they execute before customer rules:

```python
# This will fail validation
invalid_baseline = {
    "system_baseline": True,
    "priority": 10  # Error: Must be ≤ 5
}
```

### Metadata Preservation

All baseline metadata is preserved during export/import:

- **Ruleset Metadata**:
  - `system_baseline`: Identifies as baseline
  - `source_version`: Version from source system
  - `source_hash`: Hash for idempotency checks
  - `read_only`: Prevents UI modification

- **Group Metadata**:
  - `entity_key`: Entity identifier for rule group
  - `basic_managed`: Marks as Basic UI managed
  - `read_only`: Prevents modification

## Usage Examples

### Export Baseline for Distribution

```python
from dealbrain_core.rules.packaging import PackageMetadata

# Create package metadata
metadata = PackageMetadata(
    name="baseline-rules-2024Q1",
    version="1.0.0",
    author="System Admin",
    description="Q1 2024 baseline valuation rules"
)

# Export baseline to file
await packaging_service.export_to_file(
    session,
    baseline_ruleset_id,
    metadata,
    "baseline-v1.0.dbrs",
    include_baseline=True
)
```

### Import Baseline Update

```python
# Import new baseline version from file
result = await packaging_service.install_from_file(
    session,
    "baseline-v1.1.dbrs",
    actor="system_admin",
    baseline_import_mode="version"  # Creates new version
)

print(f"Created {result['baseline_versioned']} new baseline versions")
print(f"Warnings: {result['warnings']}")
# Output: Created new baseline version: System: Baseline v1.1 (inactive by default)
```

### Mixed Package Import

Packages can contain both baseline and customer rulesets:

```python
# Import package with mixed content
result = await packaging_service.install_package(
    session,
    mixed_package,
    merge_strategy="replace",      # For customer rulesets
    baseline_import_mode="version"  # For baseline rulesets
)

print(f"Baselines versioned: {result['baseline_versioned']}")
print(f"Customer rulesets created: {result['rulesets_created']}")
```

## Best Practices

1. **Always Version Baselines**: Use `baseline_import_mode="version"` to preserve history
2. **Test Before Activation**: New baseline versions start inactive - test thoroughly before activating
3. **Maintain Source Hash**: Use consistent hashing for idempotency
4. **Document Changes**: Include detailed descriptions in baseline metadata
5. **Validate Priority**: Ensure baseline priority ≤ 5 for proper execution order

## API Reference

### Export Methods

```python
async def export_ruleset_to_package(
    session: AsyncSession,
    ruleset_id: int,
    metadata: PackageMetadata,
    include_examples: bool = False,
    include_baseline: bool = False,  # Must be True for baselines
    active_only: bool = False
) -> RulesetPackage
```

```python
async def export_to_file(
    session: AsyncSession,
    ruleset_id: int,
    metadata: PackageMetadata,
    output_path: str,
    include_baseline: bool = False  # Must be True for baselines
) -> None
```

### Import Methods

```python
async def install_package(
    session: AsyncSession,
    package: RulesetPackage,
    actor: str = "system",
    merge_strategy: Literal["replace", "skip", "merge", "version"] = "replace",
    baseline_import_mode: Literal["version", "replace"] = "version"
) -> Dict[str, Any]
```

```python
async def install_from_file(
    session: AsyncSession,
    file_path: str,
    actor: str = "system",
    merge_strategy: Literal["replace", "skip", "merge", "version"] = "replace",
    baseline_import_mode: Literal["version", "replace"] = "version"
) -> Dict[str, Any]
```

### Result Dictionary

Import operations return a results dictionary:

```python
{
    "rulesets_created": 0,
    "rule_groups_created": 0,
    "rules_created": 0,
    "rulesets_updated": 0,
    "baseline_versioned": 0,  # Number of new baseline versions
    "warnings": []  # List of warning messages
}
```

## Error Handling

Common errors and their meanings:

- **ValueError: "baseline ruleset...include_baseline=True"** - Attempting to export baseline without flag
- **ValueError: "invalid priority...must have priority ≤ 5"** - Baseline priority too high
- **ValueError: "Package not compatible"** - Version or field requirements not met

## Migration Guide

For existing systems with baseline rulesets:

1. **Identify Baselines**: Query for rulesets with naming pattern or metadata
2. **Add Metadata**: Update existing baselines with required metadata fields
3. **Export Current**: Create backup packages of current baselines
4. **Test Import**: Verify version mode creates proper new versions
5. **Activate Carefully**: Switch active baseline only after validation