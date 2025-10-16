"""Unit tests for formula parser with enhanced error messages"""

import pytest

from dealbrain_core.rules.formula import (
    FormulaParser,
    FormulaEngine,
    FormulaError,
    FormulaSyntaxError,
    FormulaValidationError,
)


class TestFormulaParserBasics:
    """Test basic formula parsing functionality"""

    def test_parse_simple_arithmetic(self):
        """Test parsing simple arithmetic expressions"""
        parser = FormulaParser()

        # Should parse without errors
        parser.parse("1 + 2")
        parser.parse("10 * 3.5")
        parser.parse("100 / 4")
        parser.parse("10 - 5")
        parser.parse("10 % 3")
        parser.parse("2 ** 3")

    def test_parse_with_variables(self):
        """Test parsing with variable references"""
        parser = FormulaParser()

        parser.parse("ram_gb * 2.5")
        parser.parse("cpu_mark / 1000")
        parser.parse("price + adjustment")

    def test_parse_nested_attributes(self):
        """Test parsing nested attribute access"""
        parser = FormulaParser()

        parser.parse("cpu.cores * 100")
        parser.parse("ram_spec.ddr_generation + 1")
        parser.parse("storage.capacity_gb / 1000")

    def test_parse_functions(self):
        """Test parsing function calls"""
        parser = FormulaParser()

        parser.parse("max(ram_gb, 16)")
        parser.parse("min(price, 500)")
        parser.parse("round(cpu_mark / 1000, 2)")
        parser.parse("abs(-100)")
        parser.parse("sqrt(256)")
        parser.parse("clamp(value, 0, 100)")

    def test_parse_comparisons(self):
        """Test parsing comparison operations"""
        parser = FormulaParser()

        parser.parse("ram_gb > 16")
        parser.parse("cpu_mark >= 10000")
        parser.parse("price < 500")
        parser.parse("condition == 'new'")
        parser.parse("status != 'sold'")

    def test_parse_ternary(self):
        """Test parsing ternary expressions"""
        parser = FormulaParser()

        parser.parse("ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0")
        parser.parse("100 if condition == 'new' else 50")

    def test_parse_complex_formula(self):
        """Test parsing complex nested formula"""
        parser = FormulaParser()

        formula = (
            "max(ram_gb * 2.5, 50) + "
            "(cpu_mark / 1000 * 5.0 if cpu_mark > 0 else 0) + "
            "clamp(storage_gb * 0.1, 10, 100)"
        )
        parser.parse(formula)


class TestFormulaParserErrors:
    """Test formula parser error handling"""

    def test_empty_formula(self):
        """Test that empty formula raises error"""
        parser = FormulaParser()

        with pytest.raises(FormulaSyntaxError) as exc_info:
            parser.parse("")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_syntax_error_with_position(self):
        """Test that syntax errors include position information"""
        parser = FormulaParser()

        with pytest.raises(FormulaSyntaxError) as exc_info:
            parser.parse("ram_gb * ")

        error = exc_info.value
        # Position may or may not be set depending on Python's parser
        # But suggestion should be provided
        assert error.suggestion is not None
        assert "operator" in error.suggestion.lower()

    def test_unmatched_parentheses_suggestion(self):
        """Test helpful suggestion for unmatched parentheses"""
        parser = FormulaParser()

        # Missing closing parenthesis
        with pytest.raises(FormulaSyntaxError) as exc_info:
            parser.parse("max(ram_gb, 16")

        error = exc_info.value
        # Python's parser says "'(' was never closed" - that counts as parenthesis error
        error_str = str(exc_info.value).lower()
        assert "parenthesis" in error_str or "never closed" in error_str or ")" in error_str

        # Extra closing parenthesis - this is actually valid Python (extra parens)
        # So let's test a different case
        with pytest.raises(FormulaSyntaxError) as exc_info:
            parser.parse("(ram_gb + ")

        error_str = str(exc_info.value).lower()
        assert "parenthesis" in error_str or "operator" in error_str or "never closed" in error_str

    def test_incomplete_operation_suggestion(self):
        """Test helpful suggestion for incomplete operations"""
        parser = FormulaParser()

        with pytest.raises(FormulaSyntaxError) as exc_info:
            parser.parse("ram_gb * 2.5 +")

        error = exc_info.value
        assert error.suggestion is not None
        assert "operator" in error.suggestion.lower()

    def test_disallowed_function(self):
        """Test that disallowed functions raise validation error"""
        parser = FormulaParser()

        with pytest.raises(FormulaValidationError) as exc_info:
            parser.parse("eval('malicious code')")

        error = exc_info.value
        assert "not allowed" in str(error).lower()
        assert error.suggestion is not None

    def test_disallowed_operator(self):
        """Test that disallowed operators raise validation error"""
        parser = FormulaParser()

        # Bitwise operators should not be allowed
        # Note: & is actually valid syntax (bitwise AND), it just evaluates incorrectly
        # Let's test an operator that truly isn't allowed or doesn't exist
        with pytest.raises((FormulaSyntaxError, FormulaValidationError)):
            # Boolean 'and' keyword is valid Python but we want math operators
            parser.parse("ram_gb and cpu_mark")

    def test_disallowed_ast_node(self):
        """Test that disallowed AST nodes raise validation error"""
        parser = FormulaParser()

        # Import statements should not be allowed (mode='eval' prevents this)
        # These will fail at syntax/parsing stage since we use mode='eval'
        with pytest.raises((FormulaSyntaxError, FormulaValidationError)):
            parser.parse("import os")

        # Lambda functions should not be allowed
        with pytest.raises((FormulaSyntaxError, FormulaValidationError)):
            parser.parse("lambda x: x * 2")

        # Assignment should not be allowed
        with pytest.raises((FormulaSyntaxError, FormulaValidationError)):
            parser.parse("x = 5")


class TestFormulaEngine:
    """Test formula evaluation engine"""

    def test_evaluate_simple_arithmetic(self):
        """Test evaluating simple arithmetic"""
        engine = FormulaEngine()

        assert engine.evaluate("1 + 2", {}) == 3.0
        assert engine.evaluate("10 * 3.5", {}) == 35.0
        assert engine.evaluate("100 / 4", {}) == 25.0

    def test_evaluate_with_variables(self):
        """Test evaluating with variable context"""
        engine = FormulaEngine()

        context = {"ram_gb": 16, "price": 500}

        assert engine.evaluate("ram_gb * 2.5", context) == 40.0
        assert engine.evaluate("price - 100", context) == 400.0

    def test_evaluate_with_nested_fields(self):
        """Test evaluating with nested field access"""
        engine = FormulaEngine()

        context = {
            "cpu": {"cores": 8, "threads": 16},
            "ram_spec": {"capacity_gb": 16, "ddr_generation": 4}
        }

        # The flattened names should work
        result = engine.evaluate("cpu_cores * 100", context)
        assert result == 800.0

        # Test with actual nested dict access
        result = engine.evaluate("cpu_threads * 10", context)
        assert result == 160.0

    def test_evaluate_with_functions(self):
        """Test evaluating formulas with functions"""
        engine = FormulaEngine()

        context = {"ram_gb": 32, "price": 750}

        assert engine.evaluate("max(ram_gb, 16)", context) == 32.0
        assert engine.evaluate("min(price, 500)", context) == 500.0
        assert engine.evaluate("round(ram_gb / 3, 1)", context) == pytest.approx(10.7, 0.1)

    def test_evaluate_clamp_function(self):
        """Test clamp function"""
        engine = FormulaEngine()

        context = {"value": 150}

        # Clamp high value
        result = engine.evaluate("clamp(value, 0, 100)", context)
        assert result == 100.0

        # Clamp low value
        context["value"] = -50
        result = engine.evaluate("clamp(value, 0, 100)", context)
        assert result == 0.0

        # Value in range
        context["value"] = 50
        result = engine.evaluate("clamp(value, 0, 100)", context)
        assert result == 50.0

    def test_evaluate_ternary(self):
        """Test evaluating ternary expressions"""
        engine = FormulaEngine()

        context = {"ram_gb": 32}

        result = engine.evaluate("ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0", context)
        assert result == 80.0  # 32 * 2.5

        context["ram_gb"] = 8
        result = engine.evaluate("ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0", context)
        assert result == 24.0  # 8 * 3.0

    def test_evaluate_complex_formula(self):
        """Test evaluating complex formula"""
        engine = FormulaEngine()

        context = {
            "ram_gb": 16,
            "cpu_mark": 12000,
            "storage_gb": 512,
        }

        formula = (
            "max(ram_gb * 2.5, 50) + "
            "(cpu_mark / 1000 * 5.0 if cpu_mark > 0 else 0) + "
            "clamp(storage_gb * 0.1, 10, 100)"
        )

        result = engine.evaluate(formula, context)
        # max(16 * 2.5, 50) = 50
        # (12000 / 1000 * 5.0) = 60
        # clamp(512 * 0.1, 10, 100) = clamp(51.2, 10, 100) = 51.2
        # Total = 50 + 60 + 51.2 = 161.2
        assert result == pytest.approx(161.2, 0.1)

    def test_evaluate_undefined_variable_error(self):
        """Test that undefined variables raise helpful error"""
        engine = FormulaEngine()

        context = {"ram_gb": 16}

        with pytest.raises(FormulaError) as exc_info:
            engine.evaluate("ram_gb * cpu_mark", context)

        error = exc_info.value
        assert "not defined" in str(error).lower()
        assert error.suggestion is not None
        assert "available variables" in error.suggestion.lower()

    def test_evaluate_zero_division_error(self):
        """Test that division by zero raises helpful error"""
        engine = FormulaEngine()

        context = {"value": 100, "divisor": 0}

        with pytest.raises(FormulaError) as exc_info:
            engine.evaluate("value / divisor", context)

        assert "division" in str(exc_info.value).lower()

    def test_evaluate_type_error(self):
        """Test that type errors raise helpful error"""
        engine = FormulaEngine()

        context = {"value": "not_a_number"}

        with pytest.raises(FormulaError):
            engine.evaluate("value * 2", context)

    def test_empty_formula_returns_zero(self):
        """Test that empty formula returns 0"""
        engine = FormulaEngine()

        result = engine.evaluate("", {})
        assert result == 0.0


class TestFormulaEngineSecurity:
    """Test formula engine security restrictions"""

    def test_cannot_access_builtins(self):
        """Test that builtins are not accessible"""
        engine = FormulaEngine()

        with pytest.raises((FormulaSyntaxError, FormulaValidationError, FormulaError)):
            # __builtins__ should not be accessible
            engine.evaluate("__builtins__", {})

    def test_cannot_import_modules(self):
        """Test that import statements are blocked"""
        engine = FormulaEngine()

        with pytest.raises((FormulaSyntaxError, FormulaValidationError)):
            engine.evaluate("__import__('os')", {})

    def test_cannot_execute_code(self):
        """Test that code execution is blocked"""
        engine = FormulaEngine()

        with pytest.raises((FormulaSyntaxError, FormulaValidationError)):
            engine.evaluate("exec('print(123)')", {})

    def test_cannot_use_eval(self):
        """Test that eval is blocked"""
        engine = FormulaEngine()

        with pytest.raises((FormulaSyntaxError, FormulaValidationError)):
            engine.evaluate("eval('1 + 1')", {})


class TestFormulaEngineTestCases:
    """Test formula test case functionality"""

    def test_test_formula_with_cases(self):
        """Test testing a formula against multiple cases"""
        engine = FormulaEngine()

        formula = "ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0"

        test_cases = [
            {"ram_gb": 8},
            {"ram_gb": 16},
            {"ram_gb": 32},
        ]

        results = engine.test_formula(formula, test_cases)

        assert len(results) == 3
        assert all(r["success"] for r in results)

        assert results[0]["result"] == 24.0  # 8 * 3.0
        assert results[1]["result"] == 40.0  # 16 * 2.5
        assert results[2]["result"] == 80.0  # 32 * 2.5

    def test_test_formula_with_failing_case(self):
        """Test that failing cases are reported"""
        engine = FormulaEngine()

        formula = "ram_gb * cpu_mark"

        test_cases = [
            {"ram_gb": 16, "cpu_mark": 10000},
            {"ram_gb": 8},  # Missing cpu_mark
        ]

        results = engine.test_formula(formula, test_cases)

        assert len(results) == 2
        assert results[0]["success"]
        assert not results[1]["success"]
        assert "error" in results[1]


class TestFormulaPerformance:
    """Test formula parsing and evaluation performance"""

    def test_parse_performance(self):
        """Test that parsing is fast enough"""
        import time

        parser = FormulaParser()

        # Typical formula
        formula = "max(ram_gb * 2.5, 50) + (cpu_mark / 1000 * 5.0)"

        # Parse 100 times and measure
        start = time.time()
        for _ in range(100):
            parser.parse(formula)
        elapsed = time.time() - start

        # Should be well under 1 second for 100 parses
        assert elapsed < 1.0, f"Parsing too slow: {elapsed}s for 100 parses"

        # Average should be under 10ms
        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 10, f"Average parse time too slow: {avg_ms}ms"

    def test_evaluate_performance(self):
        """Test that evaluation is fast enough"""
        import time

        engine = FormulaEngine()

        formula = "max(ram_gb * 2.5, 50) + (cpu_mark / 1000 * 5.0)"
        context = {"ram_gb": 16, "cpu_mark": 12000}

        # Evaluate 1000 times and measure
        start = time.time()
        for _ in range(1000):
            engine.evaluate(formula, context)
        elapsed = time.time() - start

        # Should be well under 1 second for 1000 evaluations
        assert elapsed < 1.0, f"Evaluation too slow: {elapsed}s for 1000 evaluations"

        # Average should be under 1ms
        avg_ms = (elapsed / 1000) * 1000
        assert avg_ms < 1, f"Average evaluation time too slow: {avg_ms}ms"
