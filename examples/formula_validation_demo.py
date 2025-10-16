"""
Demo script showing enhanced formula parser and validator capabilities.

This demonstrates the improvements made in Phase 4, Task P4-FEAT-001:
- Enhanced error messages with position information
- AST visualization for debugging
- Field reference extraction
- Field availability validation
"""

from dealbrain_core.rules import (
    FormulaParser,
    FormulaEngine,
    FormulaValidator,
    FormulaSyntaxError,
    FormulaValidationError,
)


def demo_basic_parsing():
    """Demo basic formula parsing"""
    print("=" * 80)
    print("DEMO 1: Basic Formula Parsing")
    print("=" * 80)

    parser = FormulaParser()

    formulas = [
        "ram_gb * 2.5",
        "max(ram_gb, 16) + cpu_mark / 1000",
        "clamp(price * multiplier, min_price, max_price)",
        "ram_gb * 2.5 if condition == 'new' else ram_gb * 3.0",
    ]

    for formula in formulas:
        try:
            parser.parse(formula)
            print(f"✓ Valid: {formula}")
        except Exception as e:
            print(f"✗ Invalid: {formula}")
            print(f"  Error: {e}")

    print()


def demo_error_messages():
    """Demo enhanced error messages"""
    print("=" * 80)
    print("DEMO 2: Enhanced Error Messages")
    print("=" * 80)

    parser = FormulaParser()

    # Test various syntax errors
    invalid_formulas = [
        ("", "Empty formula"),
        ("ram_gb * ", "Incomplete operation"),
        ("max(ram_gb, 16", "Missing closing parenthesis"),
        ("eval('bad')", "Disallowed function"),
        ("ram_gb and cpu_mark", "Disallowed operator"),
    ]

    for formula, description in invalid_formulas:
        print(f"\nTesting: {description}")
        print(f"Formula: '{formula}'")
        try:
            parser.parse(formula)
            print("  Unexpectedly valid!")
        except (FormulaSyntaxError, FormulaValidationError) as e:
            print(f"  Error: {e.message}")
            if e.position is not None:
                print(f"  Position: {e.position}")
            if e.suggestion:
                print(f"  Suggestion: {e.suggestion}")

    print()


def demo_field_extraction():
    """Demo field reference extraction"""
    print("=" * 80)
    print("DEMO 3: Field Reference Extraction")
    print("=" * 80)

    validator = FormulaValidator()

    formulas = [
        "ram_gb * 2.5",
        "cpu.cores * 100 + ram_spec.ddr_generation",
        "max(ram_gb, min_ram) + sqrt(cpu_mark) / divisor",
        "price * (1 + tax_rate) if taxable else price",
    ]

    for formula in formulas:
        fields = validator.get_field_references(formula)
        print(f"\nFormula: {formula}")
        print(f"Fields: {', '.join(sorted(fields))}")

    print()


def demo_ast_visualization():
    """Demo AST visualization"""
    print("=" * 80)
    print("DEMO 4: AST Visualization for Debugging")
    print("=" * 80)

    validator = FormulaValidator()

    formulas = [
        "ram_gb * 2.5",
        "max(ram_gb, 16) + 100",
        "x if condition else y",
    ]

    for formula in formulas:
        print(f"\n{formula}")
        print("-" * 40)
        viz = validator.get_ast_visualization(formula)
        print(viz)

    print()


def demo_field_validation():
    """Demo field availability validation"""
    print("=" * 80)
    print("DEMO 5: Field Availability Validation")
    print("=" * 80)

    validator = FormulaValidator()

    # Available fields in context
    available_fields = {"ram_gb", "cpu_mark", "price", "condition", "storage_gb"}

    formulas = [
        ("ram_gb * 2.5", "Valid - all fields available"),
        ("ram_gb * cpu_mark", "Valid - all fields available"),
        ("ramgb * 2.5", "Invalid - typo in field name"),
        ("ram_gb * unknown_field", "Invalid - field doesn't exist"),
    ]

    for formula, description in formulas:
        print(f"\n{description}")
        print(f"Formula: {formula}")

        errors = validator.validate_field_availability(formula, available_fields)

        if not errors:
            print("  ✓ All fields available")
        else:
            for error in errors:
                print(f"  ✗ {error.message}")
                if error.suggestion:
                    print(f"    {error.suggestion}")

    print()


def demo_validation_warnings():
    """Demo validation warnings and best practices"""
    print("=" * 80)
    print("DEMO 6: Validation Warnings")
    print("=" * 80)

    validator = FormulaValidator()

    formulas = [
        ("ram_gb * 2.5", "Simple formula - no warnings"),
        ("ram_gb / divisor", "Division - potential zero division"),
        ("((((((ram_gb * 2) + 3) / 4) - 5) ** 6) + 7) - 8", "Deep nesting"),
        ("a / b / c / d", "Multiple divisions - precision concerns"),
    ]

    for formula, description in formulas:
        print(f"\n{description}")
        print(f"Formula: {formula}")

        errors = validator.validate(formula)

        if not errors:
            print("  ✓ No issues")
        else:
            for error in errors:
                icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(
                    error.severity, "•"
                )
                print(f"  {icon} [{error.severity.upper()}] {error.message}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")

    print()


def demo_evaluation():
    """Demo formula evaluation with better error messages"""
    print("=" * 80)
    print("DEMO 7: Formula Evaluation")
    print("=" * 80)

    engine = FormulaEngine()

    context = {
        "ram_gb": 16,
        "cpu_mark": 12000,
        "price": 500,
        "condition": "new",
    }

    print(f"Context: {context}\n")

    formulas = [
        ("ram_gb * 2.5", "Simple calculation"),
        ("max(ram_gb, 8) * 2.5", "With function"),
        ("ram_gb * 2.5 if condition == 'new' else ram_gb * 3.0", "Conditional"),
        ("ram_gb * missing_field", "Missing field error"),
        ("price / 0", "Division by zero error"),
    ]

    for formula, description in formulas:
        print(f"{description}: {formula}")
        try:
            result = engine.evaluate(formula, context)
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {type(e).__name__}: {e}")

        print()


def main():
    """Run all demos"""
    demos = [
        demo_basic_parsing,
        demo_error_messages,
        demo_field_extraction,
        demo_ast_visualization,
        demo_field_validation,
        demo_validation_warnings,
        demo_evaluation,
    ]

    for demo in demos:
        demo()
        input("Press Enter to continue...")
        print("\n")


if __name__ == "__main__":
    main()
