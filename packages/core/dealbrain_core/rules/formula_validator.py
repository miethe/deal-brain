"""Formula validator with AST analysis and field reference extraction"""

import ast
from typing import Any, Optional

import structlog

from .formula import FormulaError, FormulaParser, FormulaSyntaxError, FormulaValidationError

logger = structlog.get_logger(__name__)


class ValidationError:
    """Represents a validation error with details"""

    def __init__(
        self,
        message: str,
        severity: str = "error",
        position: Optional[int] = None,
        suggestion: Optional[str] = None,
    ):
        """
        Initialize validation error.

        Args:
            message: Error message
            severity: Error severity (error, warning, info)
            position: Character position in formula
            suggestion: Suggested fix
        """
        self.message = message
        self.severity = severity
        self.position = position
        self.suggestion = suggestion

    def __repr__(self) -> str:
        parts = [f"{self.severity.upper()}: {self.message}"]
        if self.position is not None:
            parts.append(f" at position {self.position}")
        if self.suggestion:
            parts.append(f"\n  Suggestion: {self.suggestion}")
        return "".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            "message": self.message,
            "severity": self.severity,
        }
        if self.position is not None:
            result["position"] = self.position
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class FormulaValidator:
    """
    Advanced formula validator with AST analysis and field reference extraction.

    This validator provides:
    - Detailed validation with multiple error reporting
    - Field reference extraction (including nested fields)
    - AST visualization for debugging
    - Context validation (checking if fields exist)
    """

    def __init__(self):
        self.parser = FormulaParser()

    def validate(self, formula: str) -> list[ValidationError]:
        """
        Validate a formula and return list of validation errors.

        Args:
            formula: Formula string to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for empty formula
        if not formula or not formula.strip():
            errors.append(
                ValidationError(
                    "Formula cannot be empty",
                    severity="error",
                    suggestion="Provide a valid formula expression"
                )
            )
            return errors

        # Try to parse the formula
        try:
            tree = self.parser.parse(formula)
            logger.debug(f"Formula validated successfully: {formula}")
        except FormulaSyntaxError as e:
            errors.append(
                ValidationError(
                    e.message,
                    severity="error",
                    position=e.position,
                    suggestion=e.suggestion
                )
            )
            return errors
        except FormulaValidationError as e:
            errors.append(
                ValidationError(
                    e.message,
                    severity="error",
                    position=e.position,
                    suggestion=e.suggestion
                )
            )
            return errors
        except Exception as e:
            errors.append(
                ValidationError(
                    f"Unexpected validation error: {e}",
                    severity="error"
                )
            )
            return errors

        # Additional validations (warnings, best practices)
        warnings = self._check_best_practices(formula, tree)
        errors.extend(warnings)

        return errors

    def get_field_references(self, formula: str) -> set[str]:
        """
        Extract all field references from a formula.

        This includes:
        - Simple variables: ram_gb
        - Nested fields: cpu.cores, ram_spec.ddr_generation

        Args:
            formula: Formula string

        Returns:
            Set of field reference strings
        """
        try:
            tree = self.parser.parse(formula)
        except Exception as e:
            logger.warning(f"Cannot extract fields from invalid formula: {e}")
            return set()

        fields = set()
        self._extract_fields(tree.body, fields)
        return fields

    def get_ast_visualization(self, formula: str, indent: int = 2) -> str:
        """
        Generate a readable AST visualization for debugging.

        Args:
            formula: Formula string
            indent: Number of spaces per indentation level

        Returns:
            String representation of AST tree
        """
        try:
            tree = self.parser.parse(formula)
        except Exception as e:
            return f"ERROR: Cannot parse formula: {e}"

        lines = [f"Formula: {formula}", "AST Tree:"]
        self._visualize_node(tree.body, lines, 0, indent)
        return "\n".join(lines)

    def validate_field_availability(
        self,
        formula: str,
        available_fields: set[str]
    ) -> list[ValidationError]:
        """
        Validate that all referenced fields exist in the available context.

        Args:
            formula: Formula string
            available_fields: Set of field names available in context

        Returns:
            List of validation errors for missing fields
        """
        errors = []

        # Get all referenced fields
        referenced_fields = self.get_field_references(formula)

        # Check each reference
        for field in referenced_fields:
            if field not in available_fields:
                # Try to suggest similar fields
                suggestion = self._suggest_similar_field(field, available_fields)
                errors.append(
                    ValidationError(
                        f"Field '{field}' is not available in context",
                        severity="error",
                        suggestion=suggestion or f"Available fields: {', '.join(sorted(available_fields))}"
                    )
                )

        return errors

    def _extract_fields(self, node: ast.AST, fields: set[str]) -> None:
        """
        Recursively extract field references from AST.

        Args:
            node: AST node to analyze
            fields: Set to accumulate field names
        """
        if isinstance(node, ast.Name):
            # Simple variable reference
            fields.add(node.id)

        elif isinstance(node, ast.Attribute):
            # Nested field reference (e.g., cpu.cores)
            field_path = self._get_attribute_path(node)
            if field_path:
                fields.add(field_path)

        elif isinstance(node, ast.BinOp):
            self._extract_fields(node.left, fields)
            self._extract_fields(node.right, fields)

        elif isinstance(node, ast.UnaryOp):
            self._extract_fields(node.operand, fields)

        elif isinstance(node, ast.Compare):
            self._extract_fields(node.left, fields)
            for comparator in node.comparators:
                self._extract_fields(comparator, fields)

        elif isinstance(node, ast.Call):
            for arg in node.args:
                self._extract_fields(arg, fields)

        elif isinstance(node, ast.IfExp):
            self._extract_fields(node.test, fields)
            self._extract_fields(node.body, fields)
            self._extract_fields(node.orelse, fields)

        elif isinstance(node, (ast.List, ast.Tuple)):
            for elt in node.elts:
                self._extract_fields(elt, fields)

        elif isinstance(node, ast.Subscript):
            self._extract_fields(node.value, fields)
            self._extract_fields(node.slice, fields)

    def _get_attribute_path(self, node: ast.Attribute) -> Optional[str]:
        """
        Get full path for attribute access (e.g., cpu.cores -> 'cpu.cores').

        Args:
            node: Attribute AST node

        Returns:
            Full path string or None
        """
        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))

        return None

    def _visualize_node(
        self,
        node: ast.AST,
        lines: list[str],
        level: int,
        indent: int
    ) -> None:
        """
        Recursively visualize AST node structure.

        Args:
            node: AST node to visualize
            lines: List to accumulate output lines
            level: Current indentation level
            indent: Spaces per level
        """
        prefix = " " * (level * indent)
        node_type = type(node).__name__

        if isinstance(node, ast.Constant):
            lines.append(f"{prefix}Constant: {node.value!r}")

        elif isinstance(node, ast.Name):
            lines.append(f"{prefix}Name: {node.id}")

        elif isinstance(node, ast.Attribute):
            path = self._get_attribute_path(node)
            lines.append(f"{prefix}Attribute: {path}")

        elif isinstance(node, ast.BinOp):
            op_name = type(node.op).__name__
            lines.append(f"{prefix}BinaryOp: {op_name}")
            self._visualize_node(node.left, lines, level + 1, indent)
            self._visualize_node(node.right, lines, level + 1, indent)

        elif isinstance(node, ast.UnaryOp):
            op_name = type(node.op).__name__
            lines.append(f"{prefix}UnaryOp: {op_name}")
            self._visualize_node(node.operand, lines, level + 1, indent)

        elif isinstance(node, ast.Compare):
            ops = ", ".join(type(op).__name__ for op in node.ops)
            lines.append(f"{prefix}Compare: {ops}")
            self._visualize_node(node.left, lines, level + 1, indent)
            for comparator in node.comparators:
                self._visualize_node(comparator, lines, level + 1, indent)

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                lines.append(f"{prefix}Call: {node.func.id}")
            else:
                lines.append(f"{prefix}Call: (complex)")
            for arg in node.args:
                self._visualize_node(arg, lines, level + 1, indent)

        elif isinstance(node, ast.IfExp):
            lines.append(f"{prefix}Ternary:")
            lines.append(f"{prefix}  test:")
            self._visualize_node(node.test, lines, level + 2, indent)
            lines.append(f"{prefix}  body:")
            self._visualize_node(node.body, lines, level + 2, indent)
            lines.append(f"{prefix}  orelse:")
            self._visualize_node(node.orelse, lines, level + 2, indent)

        elif isinstance(node, ast.List):
            lines.append(f"{prefix}List: [{len(node.elts)} elements]")
            for elt in node.elts:
                self._visualize_node(elt, lines, level + 1, indent)

        elif isinstance(node, ast.Tuple):
            lines.append(f"{prefix}Tuple: ({len(node.elts)} elements)")
            for elt in node.elts:
                self._visualize_node(elt, lines, level + 1, indent)

        elif isinstance(node, ast.Subscript):
            lines.append(f"{prefix}Subscript:")
            self._visualize_node(node.value, lines, level + 1, indent)
            self._visualize_node(node.slice, lines, level + 1, indent)

        else:
            lines.append(f"{prefix}{node_type}")

    def _check_best_practices(
        self,
        formula: str,
        tree: ast.Expression
    ) -> list[ValidationError]:
        """
        Check formula for best practices and potential issues.

        Args:
            formula: Formula string
            tree: Parsed AST

        Returns:
            List of warnings
        """
        warnings = []

        # Check for division by zero risk
        if self._has_division_without_check(tree.body):
            warnings.append(
                ValidationError(
                    "Formula contains division - ensure divisor is never zero",
                    severity="warning",
                    suggestion="Consider using clamp() or conditional checks to prevent division by zero"
                )
            )

        # Check for very deep nesting
        max_depth = self._get_max_depth(tree.body)
        if max_depth > 5:
            warnings.append(
                ValidationError(
                    f"Formula has deep nesting (depth {max_depth})",
                    severity="warning",
                    suggestion="Consider simplifying the formula for better readability"
                )
            )

        # Check for potential precision issues with float operations
        if self._has_multiple_divisions(tree.body):
            warnings.append(
                ValidationError(
                    "Multiple divisions may accumulate floating-point precision errors",
                    severity="info",
                    suggestion="Consider reordering operations to minimize precision loss"
                )
            )

        return warnings

    def _has_division_without_check(self, node: ast.AST) -> bool:
        """Check if formula has division operations"""
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv)):
            return True
        elif isinstance(node, ast.BinOp):
            return self._has_division_without_check(node.left) or self._has_division_without_check(node.right)
        elif isinstance(node, ast.UnaryOp):
            return self._has_division_without_check(node.operand)
        elif isinstance(node, ast.Compare):
            return any(self._has_division_without_check(c) for c in [node.left] + node.comparators)
        elif isinstance(node, ast.Call):
            return any(self._has_division_without_check(arg) for arg in node.args)
        elif isinstance(node, ast.IfExp):
            return (self._has_division_without_check(node.test) or
                    self._has_division_without_check(node.body) or
                    self._has_division_without_check(node.orelse))
        return False

    def _get_max_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Get maximum nesting depth of AST"""
        max_child_depth = current_depth

        if isinstance(node, ast.BinOp):
            max_child_depth = max(
                self._get_max_depth(node.left, current_depth + 1),
                self._get_max_depth(node.right, current_depth + 1)
            )
        elif isinstance(node, ast.UnaryOp):
            max_child_depth = self._get_max_depth(node.operand, current_depth + 1)
        elif isinstance(node, ast.Compare):
            depths = [self._get_max_depth(node.left, current_depth + 1)]
            depths.extend(self._get_max_depth(c, current_depth + 1) for c in node.comparators)
            max_child_depth = max(depths)
        elif isinstance(node, ast.Call):
            if node.args:
                max_child_depth = max(self._get_max_depth(arg, current_depth + 1) for arg in node.args)
        elif isinstance(node, ast.IfExp):
            max_child_depth = max(
                self._get_max_depth(node.test, current_depth + 1),
                self._get_max_depth(node.body, current_depth + 1),
                self._get_max_depth(node.orelse, current_depth + 1)
            )

        return max_child_depth

    def _has_multiple_divisions(self, node: ast.AST, count: int = 0) -> bool:
        """Check if formula has multiple division operations"""
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, (ast.Div, ast.FloorDiv)):
                count += 1
            count = max(
                self._has_multiple_divisions(node.left, count),
                self._has_multiple_divisions(node.right, count)
            )
        elif isinstance(node, ast.UnaryOp):
            return self._has_multiple_divisions(node.operand, count)
        elif isinstance(node, ast.IfExp):
            return max(
                self._has_multiple_divisions(node.test, count),
                self._has_multiple_divisions(node.body, count),
                self._has_multiple_divisions(node.orelse, count)
            )

        return count >= 2

    def _suggest_similar_field(self, field: str, available_fields: set[str]) -> Optional[str]:
        """
        Suggest similar field name based on edit distance.

        Args:
            field: Field name to match
            available_fields: Available field names

        Returns:
            Suggestion string or None
        """
        # Simple similarity check based on prefix matching and length
        candidates = []

        for available in available_fields:
            # Check if starts with same characters
            common_prefix = 0
            for i in range(min(len(field), len(available))):
                if field[i].lower() == available[i].lower():
                    common_prefix += 1
                else:
                    break

            # Score based on common prefix and length difference
            if common_prefix >= 2:
                length_diff = abs(len(field) - len(available))
                score = common_prefix - (length_diff * 0.5)
                candidates.append((score, available))

        if candidates:
            candidates.sort(reverse=True)
            best_match = candidates[0][1]
            return f"Did you mean '{best_match}'?"

        return None
