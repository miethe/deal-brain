# Formula Quick Reference

A concise cheat sheet for creating baseline rule formulas.

## Quick Start

```python
# Simple per-unit pricing
ram_gb * 2.5

# CPU benchmark-based
(cpu.cpu_mark_multi / 1000) * 8.0

# Conditional
50 if cpu.tdp_w > 120 else 0

# Combined with bounds
clamp((gpu.gpu_mark / 1000) * 5.0, 0, 500)
```

## Field Access

### Direct (Listing)
```python
price_usd
ram_gb
condition
```

### Related Entities
```python
cpu.cpu_mark_multi
cpu.cores
cpu.tdp_w
gpu.gpu_mark
ram_spec.ddr_generation
ram_spec.speed_mhz
primary_storage.medium
primary_storage.capacity_gb
```

### Custom Fields
```python
listing.custom_fields.warranty_months
cpu.custom_fields.efficiency_rating
```

## Operators

### Arithmetic
```python
+    # Addition
-    # Subtraction
*    # Multiplication
/    # Division (float)
//   # Floor division (integer)
%    # Modulo (remainder)
**   # Exponentiation
```

### Comparison
```python
==   # Equal
!=   # Not equal
<    # Less than
<=   # Less than or equal
>    # Greater than
>=   # Greater than or equal
```

### Logical
```python
and  # Both true
or   # At least one true
not  # Negate
```

## Functions

```python
abs(value)                      # Absolute value
min(a, b, ...)                  # Minimum value
max(a, b, ...)                  # Maximum value
round(value, ndigits=0)         # Round to n decimals
int(value)                      # Convert to integer
float(value)                    # Convert to float
sum([a, b, c])                  # Sum of values
sqrt(value)                     # Square root
pow(base, exponent)             # Power
floor(value)                    # Round down
ceil(value)                     # Round up
clamp(value, min_val, max_val)  # Constrain between min/max
```

## Syntax Patterns

### Ternary (if-else)
```python
value_if_true if condition else value_if_false

# Examples
50 if cpu.tdp_w > 120 else 0
ram_gb * 3.0 if ram_gb >= 16 else ram_gb * 2.5
```

### Nested Ternary
```python
val1 if cond1 else val2 if cond2 else val3

# Example
1.0 if condition == 'new' else 0.85 if condition == 'refurb' else 0.7
```

### Null Safety
```python
(cpu.cpu_mark_multi or 0) * 5.0       # Provide default
cpu.cpu_mark_multi * 5.0 if cpu else 0  # Check existence
```

### Bounds Checking
```python
clamp(value, 0, 500)           # Hard bounds
max(value, 0)                  # Minimum only
min(value, 500)                # Maximum only
```

## Common Patterns

### Per-Unit Pricing
```python
ram_gb * 2.5                   # $2.50/GB RAM
primary_storage_gb * 0.05      # $0.05/GB storage
cpu.cores * 10                 # $10/core
```

### Benchmark Valuation
```python
(cpu.cpu_mark_multi / 1000) * 8.0
(cpu.cpu_mark_single / 500) * 5.0
(gpu.gpu_mark / 1000) * 10.0
```

### Conditional Penalties/Bonuses
```python
50 if cpu.tdp_w > 120 else 0                      # TDP penalty
10 if ram_spec.ddr_generation == 'ddr5' else 0   # DDR5 bonus
-25 if primary_storage.medium == 'hdd' else 0    # HDD penalty
```

### Tiered Pricing
```python
# RAM tiers
ram_gb * 3.0 if ram_gb >= 32 else ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 2.0

# Storage tiers
(primary_storage_gb / 256) * 50 if primary_storage_gb >= 512 else (primary_storage_gb / 128) * 30
```

### Efficiency Metrics
```python
(cpu.cpu_mark_multi / max(cpu.tdp_w, 1)) * 2.0    # Perf per watt
round((cpu.cpu_mark_single / cpu.tdp_w) * 10, 2)  # Single-thread efficiency
```

### Condition Multipliers
```python
base_value = ram_gb * 2.5 + (cpu.cpu_mark_multi / 1000) * 8.0
base_value * (1.0 if condition == 'new' else 0.85 if condition == 'refurb' else 0.7)
```

### Combined Components
```python
# RAM + Storage
(ram_gb * 2.5) + (primary_storage_gb / 128) * 25

# CPU + GPU
(cpu.cpu_mark_multi / 1000) * 8.0 + (gpu.gpu_mark / 1000) * 10.0

# Full system
(ram_gb * 2.5) + (cpu.cpu_mark_multi / 1000) * 8.0 + (primary_storage_gb * 0.05)
```

## Available Entities

| Entity | Access Pattern | Nullable | Key Fields |
|--------|---------------|----------|------------|
| listing | `listing.field` or `field` | No | price_usd, condition, ram_gb, status |
| cpu | `cpu.field` | Yes | cpu_mark_multi, cpu_mark_single, cores, threads, tdp_w |
| gpu | `gpu.field` | Yes | gpu_mark, metal_score, name |
| ram_spec | `ram_spec.field` | Yes | ddr_generation, speed_mhz, total_capacity_gb |
| primary_storage | `primary_storage.field` | Yes | medium, capacity_gb, interface |
| secondary_storage | `secondary_storage.field` | Yes | medium, capacity_gb, interface |
| ports_profile | `ports_profile.field` | Yes | name, description |

## Enum Values

### Condition
```python
'new', 'refurb', 'used'
```

### RamGeneration
```python
'ddr3', 'ddr4', 'ddr5', 'lpddr4', 'lpddr4x', 'lpddr5', 'lpddr5x', 'hbm2', 'hbm3', 'unknown'
```

### StorageMedium
```python
'nvme', 'sata_ssd', 'hdd', 'hybrid', 'emmc', 'ufs', 'unknown'
```

### ListingStatus
```python
'active', 'archived', 'pending'
```

## Best Practices

### Always Handle Nulls
```python
# BAD
cpu.cpu_mark_multi * 5.0

# GOOD
(cpu.cpu_mark_multi or 0) * 5.0
cpu.cpu_mark_multi * 5.0 if cpu else 0
```

### Prevent Division by Zero
```python
# BAD
cpu.cpu_mark_multi / cpu.tdp_w

# GOOD
cpu.cpu_mark_multi / max(cpu.tdp_w, 1)
```

### Use Clamp for Bounds
```python
# BAD
value = gpu.gpu_mark * 0.5
if value > 500:
    value = 500  # Can't do this in formulas!

# GOOD
clamp(gpu.gpu_mark * 0.5, 0, 500)
```

### Round Currency
```python
round(ram_gb * 2.53, 2)     # $2.53/GB, rounded to cents
```

### Readability
```python
# BAD
ram_gb*2.5+(cpu.cpu_mark_multi or 0)/1000*8+50 if cpu.tdp_w>120 else 0

# GOOD
base_ram = ram_gb * 2.5
cpu_value = (cpu.cpu_mark_multi or 0) / 1000 * 8.0
tdp_penalty = 50 if cpu.tdp_w > 120 else 0
# Note: Can't use variables in formulas, this is conceptual
# Actual: (ram_gb * 2.5) + ((cpu.cpu_mark_multi or 0) / 1000 * 8.0) + (50 if cpu.tdp_w > 120 else 0)
```

## Common Mistakes

### Mistake: Accessing nullable field directly
```python
cpu.cores * 10  # Fails if listing has no CPU
```
**Fix:**
```python
(cpu.cores or 0) * 10
cpu.cores * 10 if cpu else 0
```

### Mistake: Division by zero
```python
cpu.cpu_mark_multi / cpu.tdp_w  # Fails if tdp_w is 0
```
**Fix:**
```python
cpu.cpu_mark_multi / max(cpu.tdp_w, 1)
```

### Mistake: Unbounded values
```python
(gpu.gpu_mark / 100) * 50  # Could be $5000+
```
**Fix:**
```python
clamp((gpu.gpu_mark / 100) * 50, 0, 500)
```

### Mistake: Wrong enum comparison
```python
ram_spec.ddr_generation == 'DDR5'  # Wrong case
```
**Fix:**
```python
ram_spec.ddr_generation == 'ddr5'  # Lowercase
```

### Mistake: Using unsupported operations
```python
price_usd += 50  # Assignment not allowed
for i in range(10): ...  # Loops not allowed
import math  # Imports not allowed
```
**Fix:** Use single expression with operators and functions

## Testing Formulas

### Edge Cases to Test
- Null entity (no CPU, GPU, etc.)
- Zero values (0 RAM, 0 storage, etc.)
- Extreme values (9999 GB RAM, etc.)
- All enum values (new, refurb, used)
- Missing custom fields

### Manual Testing
```python
# Test with real listing
poetry run dealbrain-cli explain <listing_id>

# Check valuation breakdown
# Verify formula result matches expected value
```

## Getting Help

- **Full Documentation**: `docs/FORMULA_REFERENCE.md`
- **Schema Reference**: `data/formula_reference.json`
- **Parser Code**: `packages/core/dealbrain_core/rules/formula.py`
- **Examples**: See `examples` section in formula_reference.json

## Formula Validation

Formulas are validated for:
- ✓ Syntax errors
- ✓ Unsupported operations
- ✓ Undefined fields
- ✓ Type mismatches
- ✓ Security issues

Use the validation endpoint to test:
```bash
POST /api/v1/formulas/validate
{
  "formula": "ram_gb * 2.5",
  "context": "listing"
}
```
