# Baseline JSON Format - Developer Guide

## Overview

This document specifies the JSON format for baseline valuation rules in Deal Brain. Baseline files define the system's default valuation adjustments for various PC components and attributes.

## Schema Version

Current Version: `1.0`

The schema version should be specified in every baseline file to ensure compatibility:

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-01-13T10:00:00Z",
  "entities": { ... }
}
```

## Root Structure

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601 timestamp",
  "generator": "optional-generator-identifier",
  "metadata": {
    "description": "Optional description",
    "author": "Optional author",
    "source": "Optional data source"
  },
  "entities": {
    "entity_key": {
      "field_name": {
        "type": "field_type",
        "value": "field_value",
        "description": "optional description",
        "metadata": {}
      }
    }
  }
}
```

## Entity Structure

Entities represent different categories of valuation adjustments. Each entity is a collection of fields that define specific adjustments.

### Standard Entity Keys

- `cpu`: Processor-specific adjustments
- `gpu`: Graphics card adjustments
- `ram`: Memory configuration adjustments
- `storage`: Storage device adjustments
- `condition`: Item condition adjustments
- `form_factor`: Form factor adjustments
- `peripherals`: Included peripherals adjustments
- `features`: Additional features adjustments

### Entity Format

```json
{
  "cpu": {
    "display_name": "CPUs",
    "description": "Processor value adjustments",
    "fields": {
      "field_key": { ... }
    }
  }
}
```

## Field Types

### 1. Scalar Fields

Direct dollar amount adjustments.

```json
{
  "intel_i7_12700": {
    "type": "scalar",
    "value": -50.00,
    "description": "Intel Core i7-12700 adjustment",
    "unit": "USD",
    "metadata": {
      "source": "market_analysis",
      "confidence": 0.95
    }
  }
}
```

**Properties:**
- `type`: Must be `"scalar"`
- `value`: Numeric value (positive or negative)
- `unit`: Currency unit (default: "USD")
- `description`: Human-readable description
- `metadata`: Optional additional data

### 2. Presence Fields

Boolean fields that apply adjustments when a feature is present.

```json
{
  "has_thunderbolt": {
    "type": "presence",
    "value": true,
    "adjustment": 25.00,
    "description": "Thunderbolt port availability",
    "metadata": {
      "min_ports": 1,
      "version": "3.0+"
    }
  }
}
```

**Properties:**
- `type`: Must be `"presence"`
- `value`: Boolean (true/false)
- `adjustment`: Dollar amount when present
- `description`: Feature description
- `metadata`: Optional specifications

### 3. Multiplier Fields

Percentage-based adjustments to base price.

```json
{
  "condition_fair": {
    "type": "multiplier",
    "value": 0.85,
    "description": "Fair condition multiplier",
    "metadata": {
      "condition_criteria": "minor cosmetic damage, fully functional"
    }
  }
}
```

**Properties:**
- `type`: Must be `"multiplier"`
- `value`: Decimal (0.0-2.0, where 1.0 = no change)
- `description`: Multiplier rationale
- `metadata`: Optional criteria

### 4. Formula Fields

Dynamic calculations based on listing properties.

```json
{
  "cpu_performance_bonus": {
    "type": "formula",
    "value": "=(cpu_mark - 10000) * 0.01",
    "description": "Performance-based CPU adjustment",
    "variables": ["cpu_mark"],
    "metadata": {
      "baseline_score": 10000,
      "dollar_per_point": 0.01
    }
  }
}
```

**Properties:**
- `type`: Must be `"formula"`
- `value`: Formula string (see Formula Syntax)
- `variables`: List of required variables
- `description`: Calculation explanation
- `metadata`: Optional parameters

## Formula Syntax

Formulas support basic arithmetic and listing properties:

### Operators
- Arithmetic: `+`, `-`, `*`, `/`, `^` (power)
- Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Logical: `&&` (and), `||` (or), `!` (not)
- Conditional: `condition ? true_value : false_value`

### Functions
- `min(a, b)`: Minimum value
- `max(a, b)`: Maximum value
- `abs(x)`: Absolute value
- `round(x)`: Round to nearest integer
- `floor(x)`: Round down
- `ceil(x)`: Round up
- `clamp(x, min, max)`: Constrain value

### Variables

Available listing properties:

```
cpu_mark         - CPU benchmark score
single_thread    - Single-thread performance
gpu_mark        - GPU benchmark score
ram_gb          - RAM capacity in GB
storage_gb      - Primary storage in GB
price_usd       - Original listing price
form_factor     - Size category (0-4)
condition       - Condition rating (1-5)
```

### Formula Examples

```json
{
  "examples": {
    "linear_scaling": "=(cpu_mark - 5000) * 0.02",
    "capped_bonus": "=min((gpu_mark / 1000) * 10, 200)",
    "conditional": "=ram_gb >= 16 ? 50 : 0",
    "complex": "=((cpu_mark + gpu_mark) / 2 - 8000) * 0.015"
  }
}
```

## Complete Example

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-01-13T10:00:00Z",
  "generator": "baseline_generator_v2",
  "metadata": {
    "description": "Q1 2025 Baseline Valuations",
    "author": "Market Analysis Team",
    "source": "aggregated_market_data"
  },
  "entities": {
    "cpu": {
      "display_name": "Processors",
      "description": "CPU value adjustments",
      "fields": {
        "intel_i5_11400": {
          "type": "scalar",
          "value": -75.00,
          "description": "Intel Core i5-11400"
        },
        "intel_i7_12700": {
          "type": "scalar",
          "value": -50.00,
          "description": "Intel Core i7-12700"
        },
        "amd_ryzen_5600": {
          "type": "scalar",
          "value": -65.00,
          "description": "AMD Ryzen 5 5600X"
        },
        "performance_scaling": {
          "type": "formula",
          "value": "=(cpu_mark - 10000) * 0.01",
          "variables": ["cpu_mark"],
          "description": "Performance-based adjustment"
        }
      }
    },
    "gpu": {
      "display_name": "Graphics Cards",
      "description": "GPU value adjustments",
      "fields": {
        "has_dedicated_gpu": {
          "type": "presence",
          "value": false,
          "adjustment": -100.00,
          "description": "No dedicated GPU penalty"
        },
        "nvidia_rtx_3060": {
          "type": "scalar",
          "value": 150.00,
          "description": "NVIDIA RTX 3060"
        },
        "nvidia_rtx_3070": {
          "type": "scalar",
          "value": 250.00,
          "description": "NVIDIA RTX 3070"
        }
      }
    },
    "condition": {
      "display_name": "Condition",
      "description": "Condition-based multipliers",
      "fields": {
        "excellent": {
          "type": "multiplier",
          "value": 1.10,
          "description": "Excellent/Like New"
        },
        "good": {
          "type": "multiplier",
          "value": 1.00,
          "description": "Good condition"
        },
        "fair": {
          "type": "multiplier",
          "value": 0.85,
          "description": "Fair condition"
        },
        "poor": {
          "type": "multiplier",
          "value": 0.70,
          "description": "Poor condition"
        }
      }
    },
    "storage": {
      "display_name": "Storage",
      "description": "Storage configuration adjustments",
      "fields": {
        "nvme_512gb": {
          "type": "scalar",
          "value": 25.00,
          "description": "512GB NVMe SSD"
        },
        "nvme_1tb": {
          "type": "scalar",
          "value": 50.00,
          "description": "1TB NVMe SSD"
        },
        "nvme_2tb": {
          "type": "scalar",
          "value": 100.00,
          "description": "2TB NVMe SSD"
        },
        "has_secondary": {
          "type": "presence",
          "value": true,
          "adjustment": 30.00,
          "description": "Secondary drive present"
        }
      }
    },
    "ram": {
      "display_name": "Memory",
      "description": "RAM configuration adjustments",
      "fields": {
        "capacity_8gb": {
          "type": "scalar",
          "value": -50.00,
          "description": "8GB RAM"
        },
        "capacity_16gb": {
          "type": "scalar",
          "value": 0.00,
          "description": "16GB RAM (baseline)"
        },
        "capacity_32gb": {
          "type": "scalar",
          "value": 75.00,
          "description": "32GB RAM"
        },
        "capacity_64gb": {
          "type": "scalar",
          "value": 200.00,
          "description": "64GB RAM"
        },
        "ddr5_premium": {
          "type": "multiplier",
          "value": 1.15,
          "description": "DDR5 memory premium"
        }
      }
    }
  }
}
```

## Validation Rules

### Required Fields

1. Root object must contain:
   - `schema_version`
   - `entities`

2. Each entity must contain:
   - At least one field

3. Each field must contain:
   - `type`
   - `value`

### Type-Specific Validation

#### Scalar Fields
- `value` must be numeric
- `unit` if present must be valid currency code

#### Presence Fields
- `value` must be boolean
- `adjustment` must be numeric

#### Multiplier Fields
- `value` must be between 0.0 and 2.0
- Common ranges: 0.7-1.3

#### Formula Fields
- `value` must be valid formula syntax
- `variables` must list all referenced variables
- Formula must evaluate without errors

### Naming Conventions

- **Entity Keys**: lowercase, underscore-separated (`form_factor`)
- **Field Keys**: lowercase, underscore-separated (`intel_i7_12700`)
- **Display Names**: Title case with spaces (`Graphics Cards`)

## Versioning Scheme

Baselines use semantic versioning:

```
major.minor.patch
```

- **Major**: Breaking changes to schema
- **Minor**: New entities or field types
- **Patch**: Value updates, bug fixes

Version is derived from:
1. Explicit `version` field in metadata
2. `generated_at` timestamp (fallback)
3. File content hash (last resort)

## Generation Tools

### Python Generator Example

```python
import json
from datetime import datetime

def generate_baseline():
    baseline = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "entities": {
            "cpu": {
                "display_name": "Processors",
                "fields": {}
            }
        }
    }

    # Add CPU adjustments
    cpu_adjustments = load_cpu_market_data()
    for cpu_model, adjustment in cpu_adjustments.items():
        baseline["entities"]["cpu"]["fields"][cpu_model] = {
            "type": "scalar",
            "value": adjustment,
            "description": cpu_model.replace("_", " ").title()
        }

    return baseline

# Save baseline
with open("baseline_2025q1.json", "w") as f:
    json.dump(generate_baseline(), f, indent=2)
```

### Validation Script

```python
import json
import jsonschema

def validate_baseline(filepath):
    with open(filepath) as f:
        baseline = json.load(f)

    # Check required fields
    assert "schema_version" in baseline
    assert "entities" in baseline

    # Validate each entity
    for entity_key, entity in baseline["entities"].items():
        for field_key, field in entity.get("fields", {}).items():
            validate_field(field_key, field)

    print(f"✓ Baseline valid: {filepath}")

def validate_field(key, field):
    assert "type" in field
    assert "value" in field

    if field["type"] == "scalar":
        assert isinstance(field["value"], (int, float))
    elif field["type"] == "multiplier":
        assert 0.0 <= field["value"] <= 2.0
    elif field["type"] == "presence":
        assert isinstance(field["value"], bool)
        assert "adjustment" in field
    elif field["type"] == "formula":
        assert isinstance(field["value"], str)
        # Additional formula validation
```

## Best Practices

### 1. Value Calibration

- Base adjustments on market data
- Use consistent methodology
- Document data sources in metadata
- Update quarterly or as needed

### 2. Formula Design

- Keep formulas simple and readable
- Use meaningful variable names
- Include bounds checking
- Test with edge cases

### 3. Organization

- Group related fields in entities
- Use consistent naming patterns
- Add descriptions to all fields
- Include metadata for traceability

### 4. Testing

- Validate JSON syntax
- Test formulas with sample data
- Verify multiplier ranges
- Check for missing dependencies

## Migration Guide

### From Legacy Format

If migrating from older formats:

```python
def migrate_legacy(legacy_data):
    baseline = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "entities": {}
    }

    # Map legacy fields to new format
    for old_category, rules in legacy_data.items():
        entity = map_category_to_entity(old_category)
        baseline["entities"][entity] = {
            "fields": convert_rules(rules)
        }

    return baseline
```

## Troubleshooting

### Common Issues

1. **Invalid JSON Syntax**
   - Use JSON validator
   - Check for trailing commas
   - Ensure proper quotes

2. **Formula Errors**
   - Verify variable names
   - Check operator syntax
   - Test with sample values

3. **Type Mismatches**
   - Ensure correct field type
   - Validate value ranges
   - Check required properties

4. **Version Conflicts**
   - Specify schema_version
   - Use compatible features
   - Update generators

---

*Last Updated: January 2025*
*Schema Version: 1.0*