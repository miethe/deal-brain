# Formula Reference Documentation

## Overview

The Formula Reference (`data/formula_reference.json`) is a comprehensive JSON schema that documents all entities, fields, operators, functions, and syntax patterns available for use in baseline rule formulas.

## Purpose

This reference serves three key purposes:

1. **AI Guidance**: Token-efficient documentation for AI systems generating baseline rules
2. **User Documentation**: Clear reference for users creating custom formulas
3. **Import Validation**: Exact field paths and types as they should appear in imported JSON

## Generating the Reference

The reference is automatically generated from the database schema and custom field definitions:

```bash
poetry run python scripts/generate_formula_reference.py
```

**When to regenerate:**
- After database schema changes (new fields, models, or relationships)
- After adding or modifying custom field definitions
- After updating the FormulaParser (new functions, operators)
- Before creating import templates or AI prompts

## Structure

### Top-Level Schema

```json
{
  "version": "1.0.0",
  "generated_at": "2025-10-17T...",
  "description": "Formula reference for baseline rule creation",
  "entities": { ... },
  "custom_fields": { ... },
  "enums": { ... },
  "operators": { ... },
  "functions": { ... },
  "syntax_patterns": { ... },
  "examples": { ... },
  "notes": { ... }
}
```

### Entities

The `entities` section documents all available data models and their fields:

**Available Entities:**
- `listing` - Primary listing entity (root context)
- `cpu` - CPU specifications (nullable foreign key)
- `gpu` - GPU specifications (nullable foreign key)
- `ram_spec` - RAM specifications (nullable foreign key)
- `primary_storage` - Primary storage profile (nullable foreign key)
- `secondary_storage` - Secondary storage profile (nullable foreign key)
- `ports_profile` - Connectivity ports profile (nullable foreign key)

**Entity Field Format:**
```json
{
  "entity_name": {
    "description": "Human-readable description",
    "access_pattern": "How to access fields",
    "nullable": true/false,
    "note": "Additional context",
    "fields": {
      "field_name": {
        "type": "integer|float|string|boolean|datetime|json|enum",
        "description": "What this field represents",
        "nullable": true/false,
        "example": "entity.field_name",
        "enum_type": "EnumClassName",  // if type is "enum"
        "values": ["val1", "val2"],   // if type is "enum"
        "default": "default_value"     // if field has default
      }
    }
  }
}
```

### Custom Fields

Custom fields are dynamically defined per entity in the database:

```json
{
  "custom_fields": {
    "listing": [
      {
        "field_key": "warranty_months",
        "field_type": "number",
        "description": "Warranty duration in months",
        "access_pattern": "listing.custom_fields.warranty_months",
        "required": false,
        "options": ["option1", "option2"],  // for enum/multiselect
        "default_value": 12                  // if has default
      }
    ]
  }
}
```

### Enums

Enumeration types and their valid values:

```json
{
  "enums": {
    "Condition": {
      "description": "Listing item condition",
      "values": ["new", "refurb", "used"],
      "usage": "Used in listing.condition field"
    }
  }
}
```

### Operators

All supported arithmetic, comparison, and logical operators:

```json
{
  "operators": {
    "arithmetic": {
      "+": "Addition",
      "-": "Subtraction",
      "*": "Multiplication",
      "/": "Division (returns float)",
      "//": "Floor division (returns integer)",
      "%": "Modulo (remainder)",
      "**": "Exponentiation"
    },
    "comparison": {
      "==": "Equal to",
      "!=": "Not equal to",
      "<": "Less than",
      "<=": "Less than or equal to",
      ">": "Greater than",
      ">=": "Greater than or equal to"
    },
    "logical": {
      "and": "Logical AND",
      "or": "Logical OR",
      "not": "Logical NOT"
    }
  }
}
```

### Functions

All available built-in functions:

```json
{
  "functions": {
    "clamp": {
      "signature": "clamp(value, min_val, max_val)",
      "description": "Constrains value between min and max",
      "example": "clamp(gpu.gpu_mark / 1000, 0, 500)",
      "returns": "float"
    }
  }
}
```

**Available Functions:**
- `abs(value)` - Absolute value
- `min(a, b, ...)` - Minimum value
- `max(a, b, ...)` - Maximum value
- `round(value, ndigits=0)` - Round to n decimal places
- `int(value)` - Convert to integer
- `float(value)` - Convert to float
- `sum(iterable)` - Sum of values
- `sqrt(value)` - Square root
- `pow(base, exponent)` - Exponentiation
- `floor(value)` - Round down to integer
- `ceil(value)` - Round up to integer
- `clamp(value, min_val, max_val)` - Constrain between min and max

### Syntax Patterns

Common syntax patterns with examples:

```json
{
  "syntax_patterns": {
    "ternary": {
      "syntax": "value_if_true if condition else value_if_false",
      "description": "Conditional expression",
      "examples": [
        "50 if cpu.tdp_w > 120 else 0",
        "price_usd * 0.1 if condition == 'new' else 0"
      ]
    }
  }
}
```

### Examples

Real-world formula examples with explanations:

```json
{
  "examples": {
    "basic_ram_valuation": {
      "formula": "ram_gb * 2.5",
      "description": "Value RAM at $2.50 per gigabyte",
      "use_case": "Simple per-unit pricing"
    }
  }
}
```

## Using the Reference

### For AI Systems

When prompting AI systems to generate baseline rules:

1. Load the complete `data/formula_reference.json` into context
2. Reference specific sections as needed (entities, functions, examples)
3. Validate generated formulas against available fields and operators

### For Users

When creating custom formulas:

1. Review the `entities` section to see available fields
2. Check `enums` for valid values for enum fields
3. Use `functions` and `operators` for calculations
4. Reference `examples` for common patterns
5. Review `syntax_patterns` for advanced usage

### For Import Validation

When validating imported baseline rules:

1. Verify all referenced fields exist in `entities` or `custom_fields`
2. Check enum values against `enums` definitions
3. Validate function calls against `functions`
4. Ensure operators are in `operators` lists

## Field Access Patterns

### Direct Field Access (Listing)

Listing fields can be accessed directly or with prefix:

```python
price_usd                    # Direct access
listing.price_usd            # Prefixed access (equivalent)
ram_gb                       # Direct access
listing.ram_gb               # Prefixed access
```

### Related Entity Access (Dot Notation)

Foreign key relationships require dot notation:

```python
cpu.cpu_mark_multi           # CPU benchmark score
cpu.cores                    # Number of CPU cores
gpu.gpu_mark                 # GPU benchmark score
ram_spec.ddr_generation      # DDR generation (DDR4, DDR5, etc.)
primary_storage.medium       # Storage type (NVME, SATA_SSD, etc.)
primary_storage.capacity_gb  # Storage capacity
```

### Custom Field Access

Custom fields use nested access pattern:

```python
listing.custom_fields.warranty_months
cpu.custom_fields.efficiency_rating
```

## Null Safety

Foreign key relationships are nullable. Always handle potential null values:

```python
# UNSAFE: May fail if listing has no CPU
cpu.cpu_mark_multi * 5.0

# SAFE: Provides default value
(cpu.cpu_mark_multi or 0) * 5.0

# SAFE: Using conditional
cpu.cpu_mark_multi * 5.0 if cpu else 0
```

## Type Coercion

The formula engine automatically coerces results to float:

```python
ram_gb * 2.5              # Returns: float
int(ram_gb / 8)           # Returns: float (cast to int, then to float)
round(price_usd * 0.15)   # Returns: float
```

## Operator Precedence

Standard Python operator precedence applies:

1. `**` (exponentiation)
2. `*`, `/`, `//`, `%` (multiplication, division, modulo)
3. `+`, `-` (addition, subtraction)
4. Comparisons (`<`, `<=`, `>`, `>=`, `==`, `!=`)
5. `not` (logical NOT)
6. `and` (logical AND)
7. `or` (logical OR)

Use parentheses to control evaluation order:

```python
ram_gb * 2.5 + cpu.cores       # Addition last
(ram_gb + cpu.cores) * 2.5     # Addition first
```

## Common Patterns

### Per-Unit Pricing

```python
ram_gb * 2.5                   # $2.50 per GB of RAM
primary_storage_gb * 0.05      # $0.05 per GB of storage
```

### Benchmark-Based Valuation

```python
(cpu.cpu_mark_multi / 1000) * 8.0        # CPU value from benchmark
clamp((gpu.gpu_mark / 1000) * 5.0, 0, 500)  # GPU value with cap
```

### Conditional Pricing

```python
50 if cpu.tdp_w > 120 else 0                           # TDP penalty
ram_gb * 3.0 if ram_gb >= 32 else ram_gb * 2.5        # Tiered pricing
10 if ram_spec.ddr_generation == 'ddr5' else 0        # Feature bonus
```

### Condition Multipliers

```python
base_value = ram_gb * 2.5 + (cpu.cpu_mark_multi / 1000) * 8.0
base_value * (1.0 if condition == 'new' else 0.85 if condition == 'refurb' else 0.7)
```

### Efficiency Metrics

```python
(cpu.cpu_mark_multi / max(cpu.tdp_w, 1)) * 2.0     # Performance per watt
round((cpu.cpu_mark_single / cpu.tdp_w) * 10, 2)   # Single-thread efficiency
```

## Best Practices

1. **Always handle null values** for foreign key relationships
2. **Use clamp()** to enforce minimum/maximum bounds
3. **Use round()** for precise decimal places in USD values
4. **Avoid division by zero** with `max(value, 1)` or conditionals
5. **Keep formulas readable** - use parentheses and whitespace
6. **Test formulas** with edge cases (null values, zero values, extreme values)
7. **Document complex formulas** in rule descriptions

## Validation

Formula validation occurs at multiple stages:

1. **Syntax validation** - Parser checks for valid Python expression syntax
2. **Security validation** - Only allowed operators, functions, and patterns
3. **Field validation** - Referenced fields must exist in entities or custom fields
4. **Type validation** - Operations must be compatible with field types
5. **Execution validation** - Formula must evaluate without runtime errors

## Limitations

- **No loops or iterations** - Formulas are single expressions only
- **No assignments** - Cannot define variables within formulas
- **No imports** - Cannot use external libraries
- **No side effects** - Formulas must be pure calculations
- **Limited string operations** - Primarily numeric/boolean operations

## Updates and Maintenance

### When Schema Changes

After modifying database models:

```bash
# 1. Apply migrations
make migrate

# 2. Regenerate reference
poetry run python scripts/generate_formula_reference.py

# 3. Update any affected formulas or import templates
```

### When Custom Fields Change

After adding/modifying custom fields via the UI or API:

```bash
# Regenerate to reflect latest custom fields
poetry run python scripts/generate_formula_reference.py
```

### Versioning

The reference includes a `version` field for tracking changes:

- **Patch version** (1.0.X): Documentation or description updates
- **Minor version** (1.X.0): New fields, functions, or entities added
- **Major version** (X.0.0): Breaking changes to structure or access patterns

## Examples from Reference

### Basic RAM Valuation
```python
ram_gb * 2.5
```
Value RAM at $2.50 per gigabyte.

### CPU Performance Valuation
```python
(cpu.cpu_mark_multi / 1000) * 8.0
```
Value CPU based on multi-thread PassMark score.

### Conditional RAM Pricing
```python
ram_gb * 3.0 if ram_gb >= 16 else ram_gb * 2.5
```
Higher per-GB price for 16GB+ configurations.

### TDP Penalty
```python
50 if cpu.tdp_w > 120 else 0
```
Apply $50 penalty for high-TDP CPUs (over 120W).

### Clamped GPU Value
```python
clamp((gpu.gpu_mark / 1000) * 8.0, 0, 500)
```
GPU valuation with minimum $0 and maximum $500 cap.

### DDR5 Bonus
```python
10 if ram_spec.ddr_generation == 'ddr5' else 0
```
Add $10 bonus for DDR5 RAM.

### Combined Storage Value
```python
(primary_storage_gb / 128) * 25 + (secondary_storage_gb / 1024) * 20
```
Value primary storage at $25 per 128GB, secondary at $20 per 1TB.

### Efficiency-Based Pricing
```python
round((cpu.cpu_mark_multi / max(cpu.tdp_w, 1)) * 2.0, 2)
```
Value CPU based on performance-per-watt efficiency.

### Condition Multiplier
```python
(ram_gb * 2.5) * (1.0 if condition == 'new' else 0.85 if condition == 'refurb' else 0.7)
```
Apply condition-based multiplier to base RAM value.

### Null-Safe CPU Value
```python
(cpu.cpu_mark_multi or 0) / 1000 * 5.0
```
Handle missing CPU benchmark score gracefully.

## Support and Resources

- **Formula Parser**: `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/formula.py`
- **Formula Validator**: `/mnt/containers/deal-brain/packages/core/dealbrain_core/rules/formula_validator.py`
- **Generation Script**: `/mnt/containers/deal-brain/scripts/generate_formula_reference.py`
- **Reference Output**: `/mnt/containers/deal-brain/data/formula_reference.json`
- **Custom Fields Service**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/custom_fields.py`
