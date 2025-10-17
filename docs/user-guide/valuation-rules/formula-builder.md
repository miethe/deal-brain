# Formula Builder User Guide

## Overview

The Formula Builder is a powerful tool in Deal Brain that allows you to create dynamic pricing formulas for valuation rules. Instead of using fixed values, you can define complex pricing logic using fields from your listings, mathematical functions, and conditional expressions.

### Why Use Formulas?

- **Flexibility**: Create sophisticated pricing rules
- **Dynamic Adjustments**: Automatically adjust prices based on multiple factors
- **Precision**: Fine-tune valuations with complex calculations
- **Scalability**: Apply consistent pricing logic across many listings

## Getting Started

### Accessing the Formula Builder

1. Navigate to the Valuation Rules section
2. Create or edit a valuation rule
3. Click on the "Formula" input field
4. Choose between Visual Mode and Text Mode

### Modes

#### Visual Mode
- Drag and drop fields and functions
- Point-and-click interface
- Great for beginners
- Helps prevent syntax errors

#### Text Mode
- Direct text input
- Full flexibility
- Recommended for advanced users
- Supports complex expressions

## Syntax Guide

### Variables (Fields)

Variables represent listing attributes. Use them directly in your formulas:

- `price_usd`: Listing price in USD
- `ram_gb`: RAM capacity
- `cpu.cpu_mark_single`: Single-thread CPU performance
- `storage_gb`: Storage capacity
- `condition`: Listing condition (new, used, refurbished)

Example:
```
ram_gb * 2.5  # Multiply RAM capacity by 2.5
```

### Operators

Standard mathematical and comparison operators:

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Addition | `ram_gb + 4` |
| `-` | Subtraction | `price_usd - 50` |
| `*` | Multiplication | `cpu.cpu_mark_single * 0.1` |
| `/` | Division | `ram_gb / 8` |
| `//` | Integer Division | `storage_gb // 256` |
| `%` | Modulo (Remainder) | `ram_gb % 8` |
| `**` | Exponentiation | `ram_gb ** 2` |

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal to | `condition == "used"` |
| `!=` | Not equal to | `ram_gb != 16` |
| `<` | Less than | `price_usd < 500` |
| `<=` | Less than or equal | `ram_gb <= 32` |
| `>` | Greater than | `cpu.cpu_mark_single > 5000` |
| `>=` | Greater than or equal | `storage_gb >= 512` |

### Conditional Expressions

Use ternary expressions for conditional logic:

```
value_if_true if condition else value_if_false
```

Example:
```
ram_gb * 3.0 if ram_gb >= 32 else ram_gb * 2.5
```

## Function Reference

### Mathematical Functions

| Function | Description | Example |
|----------|-------------|---------|
| `abs(x)` | Absolute value | `abs(-5)` returns `5` |
| `min(a, b)` | Minimum of two values | `min(ram_gb, 32)` |
| `max(a, b)` | Maximum of two values | `max(price_usd, 100)` |
| `round(x)` | Round to nearest integer | `round(price_usd / 10)` |
| `int(x)` | Convert to integer | `int(ram_gb)` |
| `float(x)` | Convert to float | `float(cpu.cpu_mark_single)` |
| `sum(list)` | Sum of list elements | `sum([ram_gb, storage_gb])` |
| `sqrt(x)` | Square root | `sqrt(cpu.cpu_mark_single)` |
| `pow(x, y)` | Power (x raised to y) | `pow(ram_gb, 2)` |
| `floor(x)` | Round down | `floor(price_usd / 10)` |
| `ceil(x)` | Round up | `ceil(price_usd / 10)` |
| `clamp(x, min, max)` | Constrain value | `clamp(ram_gb * 2.5, 0, 100)` |

## Example Formulas

### 1. Simple Per-Unit Pricing
```
ram_gb * 2.5  # Multiply RAM capacity by 2.5
```

### 2. CPU Performance Adjustment
```
cpu.cpu_mark_single * 0.05  # Scale price by single-thread performance
```

### 3. Conditional Pricing by RAM
```
ram_gb * 3.0 if ram_gb >= 32 else ram_gb * 2.5
```

### 4. Constrained Performance Scaling
```
clamp(cpu.cpu_mark_single / 100 * 5.2, 0, 80)
```

### 5. Combined Metrics
```
(ram_gb * 2.5 + cpu.cpu_mark_multi / 1000 * 5.0)
```

### 6. Condition-Based Discount
```
price_usd * 0.85 if condition == "used" else price_usd
```

## Best Practices

1. **Keep It Simple**: Start with basic formulas, then add complexity
2. **Test Thoroughly**: Use sample data to validate your formulas
3. **Handle Edge Cases**:
   - Check for potential division by zero
   - Use `clamp()` to set reasonable bounds
4. **Be Consistent**: Use clear, descriptive variable references
5. **Performance**: Avoid overly complex calculations

## Troubleshooting

### Common Errors

| Error | Possible Cause | Solution |
|-------|----------------|----------|
| Undefined field | Typo in field name | Double-check field references |
| Division by zero | No check for zero | Add conditional check |
| Type mismatch | Mixing number types | Use `int()` or `float()` |
| Syntax error | Incorrect operators | Check syntax, use parentheses |

### Tips

- Use parentheses to clarify calculation order
- Break complex formulas into multiple steps
- Use the live preview to validate calculations

## Advanced Usage

### Nested Conditionals
```
ram_gb * (3.5 if condition == "new" else 2.5) if ram_gb >= 32 else ram_gb * 2.0
```

### Performance Considerations
- Keep formulas relatively simple
- Avoid repeated complex calculations
- Use `clamp()` to limit extreme values

## Version Information

- **Current Version**: 1.0
- **Last Updated**: 2025-10-16
- **Applicable Product**: Deal Brain Valuation System

## Getting Help

If you encounter issues or need more assistance:
- Check the live preview validation messages
- Consult the in-app function reference
- Contact Deal Brain support