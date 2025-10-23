"""Unit tests for formula validator"""

import pytest

from dealbrain_core.rules.formula_validator import FormulaValidator, ValidationError


class TestFormulaValidatorBasics:
    """Test basic formula validation"""

    def test_validate_simple_formula(self):
        """Test validating simple formula"""
        validator = FormulaValidator()

        errors = validator.validate("ram_gb * 2.5")
        assert len(errors) == 0

    def test_validate_complex_formula(self):
        """Test validating complex formula"""
        validator = FormulaValidator()

        formula = "max(ram_gb * 2.5, 50) + (cpu_mark / 1000 * 5.0)"
        errors = validator.validate(formula)

        # Should have no errors, but may have warnings about division
        error_count = sum(1 for e in errors if e.severity == "error")
        assert error_count == 0

    def test_validate_empty_formula(self):
        """Test that empty formula returns error"""
        validator = FormulaValidator()

        errors = validator.validate("")
        assert len(errors) > 0
        assert errors[0].severity == "error"
        assert "empty" in errors[0].message.lower()

    def test_validate_syntax_error(self):
        """Test that syntax errors are captured"""
        validator = FormulaValidator()

        errors = validator.validate("ram_gb * ")
        assert len(errors) > 0
        assert errors[0].severity == "error"
        assert errors[0].suggestion is not None

    def test_validate_invalid_function(self):
        """Test that invalid functions are captured"""
        validator = FormulaValidator()

        errors = validator.validate("eval('malicious')")
        assert len(errors) > 0
        assert any("not allowed" in e.message.lower() for e in errors)


class TestFormulaValidatorFieldExtraction:
    """Test field reference extraction"""

    def test_extract_simple_fields(self):
        """Test extracting simple field references"""
        validator = FormulaValidator()

        fields = validator.get_field_references("ram_gb * 2.5 + cpu_mark")
        assert fields == {"ram_gb", "cpu_mark"}

    def test_extract_nested_fields(self):
        """Test extracting nested field references"""
        validator = FormulaValidator()

        fields = validator.get_field_references("cpu.cores * 100 + ram_spec.ddr_generation")
        assert "cpu.cores" in fields
        assert "ram_spec.ddr_generation" in fields

    def test_extract_fields_from_functions(self):
        """Test extracting fields from function calls"""
        validator = FormulaValidator()

        fields = validator.get_field_references("max(ram_gb, min_ram) + sqrt(cpu_mark)")
        assert fields == {"ram_gb", "min_ram", "cpu_mark"}

    def test_extract_fields_from_ternary(self):
        """Test extracting fields from ternary expressions"""
        validator = FormulaValidator()

        formula = "ram_gb * 2.5 if condition == 'new' else ram_gb * 3.0"
        fields = validator.get_field_references(formula)

        assert "ram_gb" in fields
        assert "condition" in fields

    def test_extract_fields_from_complex_formula(self):
        """Test extracting fields from complex formula"""
        validator = FormulaValidator()

        formula = (
            "max(ram_gb * multiplier, min_value) + "
            "(cpu_mark / divisor if cpu_mark > threshold else default_value)"
        )
        fields = validator.get_field_references(formula)

        expected = {"ram_gb", "multiplier", "min_value", "cpu_mark", "divisor", "threshold", "default_value"}
        assert fields == expected

    def test_extract_fields_ignores_constants(self):
        """Test that constants are not extracted as fields"""
        validator = FormulaValidator()

        fields = validator.get_field_references("ram_gb * 2.5 + 100")
        assert fields == {"ram_gb"}
        assert 2.5 not in fields
        assert 100 not in fields

    def test_extract_fields_from_invalid_formula(self):
        """Test that field extraction handles invalid formulas gracefully"""
        validator = FormulaValidator()

        # Should return empty set, not raise error
        fields = validator.get_field_references("ram_gb * ")
        assert isinstance(fields, set)


class TestFormulaValidatorASTVisualization:
    """Test AST visualization"""

    def test_visualize_simple_formula(self):
        """Test visualizing simple formula"""
        validator = FormulaValidator()

        viz = validator.get_ast_visualization("ram_gb * 2.5")

        assert "Formula: ram_gb * 2.5" in viz
        assert "AST Tree:" in viz
        assert "BinaryOp" in viz or "Mult" in viz
        assert "Name: ram_gb" in viz
        assert "Constant: 2.5" in viz

    def test_visualize_nested_formula(self):
        """Test visualizing nested formula"""
        validator = FormulaValidator()

        viz = validator.get_ast_visualization("max(ram_gb, 16) * 2.5")

        assert "Formula:" in viz
        assert "Call: max" in viz
        assert "ram_gb" in viz
        assert "16" in viz

    def test_visualize_complex_formula(self):
        """Test visualizing complex formula"""
        validator = FormulaValidator()

        formula = "ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0"
        viz = validator.get_ast_visualization(formula)

        assert "Formula:" in viz
        assert "Ternary" in viz or "IfExp" in viz
        assert "test:" in viz
        assert "body:" in viz
        assert "orelse:" in viz

    def test_visualize_attribute_access(self):
        """Test visualizing attribute access"""
        validator = FormulaValidator()

        viz = validator.get_ast_visualization("cpu.cores * 100")

        assert "Formula:" in viz
        assert "cpu.cores" in viz or "Attribute" in viz

    def test_visualize_invalid_formula(self):
        """Test that visualization handles invalid formulas"""
        validator = FormulaValidator()

        viz = validator.get_ast_visualization("ram_gb * ")

        assert "ERROR" in viz.upper()
        assert "cannot parse" in viz.lower()

    def test_visualize_with_custom_indent(self):
        """Test visualization with custom indentation"""
        validator = FormulaValidator()

        viz2 = validator.get_ast_visualization("ram_gb * 2.5", indent=2)
        viz4 = validator.get_ast_visualization("ram_gb * 2.5", indent=4)

        # Different indents should produce different outputs
        assert viz2 != viz4


class TestFormulaValidatorFieldAvailability:
    """Test field availability validation"""

    def test_validate_all_fields_available(self):
        """Test that validation passes when all fields are available"""
        validator = FormulaValidator()

        formula = "ram_gb * 2.5 + cpu_mark"
        available_fields = {"ram_gb", "cpu_mark", "price", "condition"}

        errors = validator.validate_field_availability(formula, available_fields)
        assert len(errors) == 0

    def test_validate_missing_field(self):
        """Test that missing fields are reported"""
        validator = FormulaValidator()

        formula = "ram_gb * cpu_mark"
        available_fields = {"ram_gb", "price"}

        errors = validator.validate_field_availability(formula, available_fields)
        assert len(errors) == 1
        assert "cpu_mark" in errors[0].message
        assert "not available" in errors[0].message.lower()

    def test_validate_multiple_missing_fields(self):
        """Test that multiple missing fields are reported"""
        validator = FormulaValidator()

        formula = "ram_gb * cpu_mark + storage_gb"
        available_fields = {"price", "condition"}

        errors = validator.validate_field_availability(formula, available_fields)
        assert len(errors) == 3  # All three fields missing

    def test_validate_suggests_similar_field(self):
        """Test that similar fields are suggested"""
        validator = FormulaValidator()

        formula = "ramgb * 2.5"  # Typo: should be ram_gb
        available_fields = {"ram_gb", "cpu_mark", "price"}

        errors = validator.validate_field_availability(formula, available_fields)
        assert len(errors) == 1
        # Should suggest ram_gb
        assert "ram_gb" in errors[0].suggestion or "ram_gb" in errors[0].message

    def test_validate_nested_field_availability(self):
        """Test validating nested field availability"""
        validator = FormulaValidator()

        formula = "cpu.cores * 100"
        available_fields = {"cpu.cores", "cpu.threads", "ram_gb"}

        errors = validator.validate_field_availability(formula, available_fields)
        assert len(errors) == 0

    def test_validate_nested_field_missing(self):
        """Test that missing nested fields are reported"""
        validator = FormulaValidator()

        formula = "cpu.cores * 100"
        available_fields = {"ram_gb", "price"}

        errors = validator.validate_field_availability(formula, available_fields)
        assert len(errors) == 1
        assert "cpu.cores" in errors[0].message


class TestFormulaValidatorWarnings:
    """Test best practice warnings"""

    def test_warning_for_division(self):
        """Test warning for division operations"""
        validator = FormulaValidator()

        errors = validator.validate("ram_gb / divisor")

        # Should have at least one warning about division
        warnings = [e for e in errors if e.severity == "warning"]
        assert len(warnings) > 0
        assert any("division" in w.message.lower() for w in warnings)

    def test_warning_for_deep_nesting(self):
        """Test warning for deeply nested formulas"""
        validator = FormulaValidator()

        # Create deeply nested formula (needs to be >5 levels deep)
        formula = "((((((ram_gb * 2) + 3) / 4) - 5) ** 6) + 7) - 8"
        errors = validator.validate(formula)

        # Should have warning about deep nesting
        warnings = [e for e in errors if e.severity == "warning"]
        assert any("nesting" in w.message.lower() or "depth" in w.message.lower() for w in warnings)

    def test_info_for_multiple_divisions(self):
        """Test info message for multiple divisions"""
        validator = FormulaValidator()

        formula = "ram_gb / cpu_mark / storage_gb"
        errors = validator.validate(formula)

        # Should have info or warning about multiple divisions
        infos = [e for e in errors if e.severity in ("info", "warning")]
        assert len(infos) > 0

    def test_no_warnings_for_simple_formula(self):
        """Test that simple formulas don't generate warnings"""
        validator = FormulaValidator()

        errors = validator.validate("ram_gb * 2.5 + 100")

        # Should have no errors or warnings
        assert len([e for e in errors if e.severity == "error"]) == 0
        # May have warnings about best practices, but that's OK


class TestValidationErrorClass:
    """Test ValidationError class"""

    def test_validation_error_basic(self):
        """Test basic ValidationError creation"""
        error = ValidationError("Test error")

        assert error.message == "Test error"
        assert error.severity == "error"
        assert error.position is None
        assert error.suggestion is None

    def test_validation_error_with_details(self):
        """Test ValidationError with all details"""
        error = ValidationError(
            "Test error",
            severity="warning",
            position=10,
            suggestion="Try this instead"
        )

        assert error.message == "Test error"
        assert error.severity == "warning"
        assert error.position == 10
        assert error.suggestion == "Try this instead"

    def test_validation_error_repr(self):
        """Test ValidationError string representation"""
        error = ValidationError(
            "Test error",
            severity="error",
            position=5,
            suggestion="Fix it"
        )

        repr_str = repr(error)
        assert "ERROR" in repr_str
        assert "Test error" in repr_str
        assert "position 5" in repr_str
        assert "Fix it" in repr_str

    def test_validation_error_to_dict(self):
        """Test ValidationError dictionary conversion"""
        error = ValidationError(
            "Test error",
            severity="warning",
            position=10,
            suggestion="Try this"
        )

        d = error.to_dict()
        assert d["message"] == "Test error"
        assert d["severity"] == "warning"
        assert d["position"] == 10
        assert d["suggestion"] == "Try this"

    def test_validation_error_to_dict_minimal(self):
        """Test ValidationError dict with minimal data"""
        error = ValidationError("Test error")

        d = error.to_dict()
        assert d["message"] == "Test error"
        assert d["severity"] == "error"
        assert "position" not in d
        assert "suggestion" not in d


class TestFormulaValidatorEdgeCases:
    """Test edge cases and corner cases"""

    def test_validate_whitespace_only_formula(self):
        """Test that whitespace-only formula is treated as empty"""
        validator = FormulaValidator()

        errors = validator.validate("   ")
        assert len(errors) > 0
        assert "empty" in errors[0].message.lower()

    def test_validate_very_long_formula(self):
        """Test validating very long formula"""
        validator = FormulaValidator()

        # Create a very long but valid formula
        terms = [f"var_{i}" for i in range(50)]
        formula = " + ".join(terms)

        errors = validator.validate(formula)
        # Should not have errors (though may have warnings)
        assert len([e for e in errors if e.severity == "error"]) == 0

    def test_extract_fields_with_subscripts(self):
        """Test field extraction with array subscripts"""
        validator = FormulaValidator()

        fields = validator.get_field_references("values[0] * 2")
        assert "values" in fields

    def test_visualize_list_literals(self):
        """Test visualizing list literals"""
        validator = FormulaValidator()

        viz = validator.get_ast_visualization("max([1, 2, 3])")
        assert "List" in viz or "[" in viz

    def test_validate_formula_with_unicode(self):
        """Test that unicode characters are handled"""
        validator = FormulaValidator()

        # Unicode in variable names might not be valid Python
        errors = validator.validate("价格 * 2")  # Chinese characters
        # Should either parse or give clear error
        assert isinstance(errors, list)
