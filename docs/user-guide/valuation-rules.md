# Valuation Rules User Guide

**Version:** 2.0
**Last Updated:** October 2, 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Getting Started](#getting-started)
4. [Creating Rules](#creating-rules)
5. [Managing Rulesets](#managing-rulesets)
6. [Import/Export](#importexport)
7. [CLI Usage](#cli-usage)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Introduction

The Advanced Valuation Rules System allows you to create sophisticated, condition-based pricing adjustments for your PC listings. Rules can evaluate complex conditions (RAM type, CPU performance, storage generation, etc.) and apply corresponding valuation adjustments.

### Key Features

- **Hierarchical Organization**: Rulesets → Groups → Rules
- **Flexible Conditions**: 15+ operators with nested AND/OR logic
- **Multiple Action Types**: Fixed value, per-unit, benchmark-based, multipliers, formulas
- **Preview Before Applying**: See impact before making changes
- **Import/Export**: Share rules via CSV, JSON, YAML, or packaged `.dbrs` files
- **CLI Automation**: Manage rules programmatically
- **Weighted Scoring**: Integrate with Profile-based scoring

---

## Core Concepts

### Ruleset

A **ruleset** is a named collection of related rules (e.g., "Gaming PC Valuation Q4 2025"). You can have multiple rulesets and activate/deactivate them as needed.

**Attributes:**
- Name (unique)
- Version (semantic versioning)
- Description
- Active/Inactive status
- Metadata (tags, author, etc.)

### Rule Group

A **rule group** organizes rules by component category (CPU, RAM, GPU, Storage, etc.). Groups help organize rules logically and support weighted scoring.

**Attributes:**
- Name
- Category (cpu, gpu, ram, storage, chassis, ports, os)
- Weight (for scoring integration)
- Display order

### Rule

A **rule** defines conditions and actions for valuation adjustments.

**Components:**
- **Conditions**: What must be true for the rule to apply
- **Actions**: What valuation adjustments to make
- **Priority**: Execution order when multiple rules match
- **Active/Inactive**: Whether the rule is currently evaluated

---

## Getting Started

### Accessing the Rules Interface

1. Navigate to **Valuation Rules** in the main menu
2. You'll see a list of rulesets, groups, and rules
3. Use the search bar to filter by name
4. Click **New Ruleset** to get started

### Creating Your First Ruleset

1. Click **New Ruleset**
2. Enter a name (e.g., "My First Ruleset")
3. Add a description (optional)
4. Set version to "1.0.0"
5. Click **Create**

Your new ruleset appears in the list!

---

## Creating Rules

### Rule Builder Wizard

The rule builder is a multi-step wizard that guides you through creating a rule:

**Step 1: Basic Information**
- Rule name
- Description
- Category (which group it belongs to)
- Priority (1-1000, higher = evaluated first)

**Step 2: Define Conditions**

Conditions determine when a rule applies. You can create simple or complex conditions.

#### Simple Condition Example

```
Field: ram_gb
Operator: greater_than_or_equal
Value: 16
```

This matches any listing with 16GB or more RAM.

#### Nested Conditions Example

```
AND Group:
  - cpu.cores >= 8
  - ram_gb >= 16
  OR
  - cpu.cpu_mark_multi > 25000
```

This matches listings that either have (8+ cores AND 16+ GB RAM) OR (CPU benchmark > 25000).

#### Available Operators

**Comparison:**
- `equals`, `not_equals`
- `greater_than`, `less_than`
- `greater_than_or_equal`, `less_than_or_equal`
- `between` (inclusive range)

**String:**
- `contains`, `starts_with`, `ends_with`
- `regex` (pattern matching)

**Set:**
- `in`, `not_in` (list membership)

**Step 3: Configure Actions**

Actions define what valuation adjustments to make when conditions match.

#### Action Types

**1. Fixed Value**
```yaml
action_type: fixed_value
value_usd: 50.00
```
Adds/subtracts a fixed dollar amount.

**2. Per-Unit Pricing**
```yaml
action_type: per_unit
metric: per_gb
value_usd: 3.50
unit_type: ram_gb
```
Calculates value based on quantity (e.g., $3.50 per GB of RAM).

**3. Benchmark-Based**
```yaml
action_type: benchmark_based
metric: cpu_mark_multi
unit_type: per_1000_points
value_usd: 5.00
base_value: 50.00
```
Value proportional to performance benchmarks.

**4. Multiplier**
```yaml
action_type: multiplier
value_usd: 1.15
```
Multiply current valuation by percentage (1.15 = 15% increase).

**5. Additive**
```yaml
action_type: additive
value_usd: -25.00
```
Add or subtract from base value.

**6. Formula**
```yaml
action_type: formula
formula: "max(ram_gb * 3.50, 50.00)"
```
Custom calculation with safe evaluation.

#### Modifiers

Actions can have modifiers that adjust based on condition:

```yaml
modifiers:
  condition_new: 1.0
  condition_refurb: 0.85
  condition_used: 0.70
```

**Step 4: Preview**

Before saving, preview the rule's impact:
- See sample matched listings
- View before/after valuations
- Review impact statistics (count, average change)

---

## Managing Rulesets

### Activating/Deactivating Rulesets

Only active rulesets are evaluated. Toggle the status with the power icon.

### Versioning

When making significant changes:
1. Update the version number (semantic versioning)
2. Add change notes
3. Version history is automatically tracked

### Duplicating Rulesets

To create a similar ruleset:
1. Click the **duplicate** icon
2. Give it a new name
3. Modify as needed

### Deleting Rulesets

**⚠️ Warning:** Deletion is permanent and cascades to all groups and rules.

---

## Import/Export

### Supported Formats

- **CSV**: Tabular data, good for spreadsheet editing
- **JSON**: Structured data, programmatic access
- **YAML**: Human-readable, great for version control
- **Excel**: Formatted spreadsheets with multiple sheets
- **`.dbrs` Package**: Complete ruleset with dependencies

### Exporting Rules

1. Click **Export** on any ruleset
2. Choose format (CSV, JSON, YAML, Excel)
3. Select what to include:
   - Active rules only
   - Include dependencies
   - Include metadata
4. Download file

### Importing Rules

1. Click **Import**
2. Upload file (drag-and-drop or browse)
3. Map fields to schema (if needed)
4. Preview changes
5. Confirm import

#### Import Options

- **Merge Strategy**: Replace, skip duplicates, or merge
- **Validation**: Strict or lenient mode
- **Rollback**: Undo if errors occur

### Ruleset Packages (`.dbrs`)

Packages are self-contained rulesets that include:
- Complete rule definitions
- Custom field definitions
- Dependencies
- Version metadata
- Example data

**Creating a Package:**
1. Click **Package** on a ruleset
2. Fill in metadata (name, version, author, description)
3. Select what to include
4. Export as `.dbrs` file

**Installing a Package:**
1. Click **Install Package**
2. Upload `.dbrs` file
3. Review compatibility check
4. Confirm installation

---

## CLI Usage

The CLI provides automation capabilities for rules management.

### List Rules

```bash
dealbrain-cli rules list
dealbrain-cli rules list --category cpu
dealbrain-cli rules list --ruleset "Gaming PC"
```

### Show Rule Details

```bash
dealbrain-cli rules show <rule-id>
```

### Create Rules

```bash
dealbrain-cli rules create --from-file rule.yaml
```

### Import/Export

```bash
# Export
dealbrain-cli rules export --format json --output rules.json

# Import
dealbrain-cli rules import rules.csv --mapping mappings.json
```

### Preview and Apply

```bash
# Preview impact
dealbrain-cli rules preview <rule-id>

# Apply to listings
dealbrain-cli rules apply "Gaming PC Ruleset"
```

### Package Management

```bash
# Create package
dealbrain-cli rules package "Gaming PC" --output gaming-v1.dbrs

# Install package
dealbrain-cli rules install gaming-v1.dbrs
```

---

## Best Practices

### Rule Organization

1. **Use descriptive names**: "DDR5 RAM Premium" instead of "Rule 1"
2. **Group logically**: Keep CPU rules in CPU group, etc.
3. **Set priorities carefully**: Higher priority = evaluated first
4. **Document with descriptions**: Explain why the rule exists

### Condition Design

1. **Start simple**: Test with simple conditions first
2. **Be specific**: Narrow conditions reduce unexpected matches
3. **Use AND/OR wisely**: Complex logic can be hard to debug
4. **Test thoroughly**: Preview before applying

### Action Configuration

1. **Conservative values**: Start with smaller adjustments
2. **Use modifiers**: Account for condition (new/used)
3. **Test formulas**: Verify formula results with examples
4. **Document calculations**: Explain how values were determined

### Version Control

1. **Use semantic versioning**: Major.Minor.Patch
2. **Track changes**: Document what changed in each version
3. **Export regularly**: Back up your rulesets
4. **Test before promoting**: Preview in staging environment

### Performance

1. **Limit nested conditions**: Deep nesting slows evaluation
2. **Use specific fields**: Avoid wildcards when possible
3. **Deactivate unused rules**: Reduces evaluation overhead
4. **Monitor performance**: Check evaluation times in logs

---

## Troubleshooting

### Rule Not Matching Expected Listings

**Problem:** Rule doesn't match listings you expect it to.

**Solutions:**
1. Check condition operators (>= vs >)
2. Verify field names (use autocomplete)
3. Review AND/OR logic
4. Test with rule preview
5. Check for null/missing values

### Unexpected Valuation Changes

**Problem:** Rule makes larger/smaller changes than expected.

**Solutions:**
1. Check action type and values
2. Verify modifiers are applied correctly
3. Review priority order (higher priority rules first)
4. Check for conflicting rules
5. Test with single listing first

### Import Fails

**Problem:** Import fails with validation errors.

**Solutions:**
1. Check file format matches expected structure
2. Verify required fields are present
3. Review field mappings
4. Check for circular dependencies
5. Use lenient validation mode for testing

### Performance Issues

**Problem:** Rule evaluation is slow.

**Solutions:**
1. Reduce number of active rules
2. Simplify complex conditions
3. Use caching (automatic)
4. Batch process listings
5. Check database indexes

### Package Installation Fails

**Problem:** `.dbrs` package won't install.

**Solutions:**
1. Check compatibility (app version)
2. Verify required custom fields exist
3. Review dependency conflicts
4. Try merge strategy instead of replace
5. Check package integrity (re-download)

---

## Advanced Topics

### Weighted Scoring Integration

Rules can integrate with Profile-based scoring by configuring weights for each rule group.

**Example:**
```json
{
  "profile_name": "Gaming Focus",
  "rule_group_weights": {
    "cpu_valuation": 0.25,
    "gpu_valuation": 0.45,
    "ram_valuation": 0.15,
    "storage_valuation": 0.10,
    "chassis_valuation": 0.05
  }
}
```

Weights must sum to 1.0 and determine how much each category contributes to the final score.

### Custom Field Integration

Rules can reference custom fields defined in the system:

```yaml
conditions:
  - field: custom.ram_generation
    operator: equals
    value: "DDR5"
```

Custom fields must be defined before use in rules.

### Formula Safety

The formula engine uses safe evaluation to prevent code injection:
- Whitelisted functions only (math, max, min, etc.)
- No access to system functions
- No file I/O or network operations
- Automatic sanitization of inputs

**Allowed Functions:**
- Math: `abs`, `ceil`, `floor`, `round`, `max`, `min`
- Logic: `if`, `and`, `or`, `not`
- Operators: `+`, `-`, `*`, `/`, `%`, `**`

---

## Getting Help

- **Documentation**: See [docs/](../../)
- **API Reference**: `/api/docs`
- **CLI Help**: `dealbrain-cli rules --help`
- **Examples**: [docs/examples/rules/](../examples/rules/)
- **Issues**: [GitHub Issues](https://github.com/your-org/deal-brain/issues)

---

**End of User Guide**
