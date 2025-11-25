"""Safe formula parser and evaluator for custom calculations"""

import ast
import math
import operator
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class FormulaError(Exception):
    """Base exception for formula parsing and evaluation errors"""

    def __init__(
        self, message: str, position: Optional[int] = None, suggestion: Optional[str] = None
    ):
        """
        Initialize formula error with detailed information.

        Args:
            message: Error description
            position: Character position in formula where error occurred
            suggestion: Optional suggestion for fixing the error
        """
        self.message = message
        self.position = position
        self.suggestion = suggestion

        # Build detailed error message
        error_parts = [message]
        if position is not None:
            error_parts.append(f" at position {position}")
        if suggestion:
            error_parts.append(f"\nSuggestion: {suggestion}")

        super().__init__("".join(error_parts))


class FormulaSyntaxError(FormulaError):
    """Raised when formula has syntax errors"""

    pass


class FormulaValidationError(FormulaError):
    """Raised when formula contains unsafe or disallowed operations"""

    pass


class FormulaParser:
    """Parse formula strings to ensure they are safe for evaluation"""

    # Allowed operators
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Allowed comparisons
    ALLOWED_COMPARISONS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }

    # Allowed functions
    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "min": min,
        "max": max,
        "round": round,
        "int": int,
        "float": float,
        "sum": sum,
        # Math functions
        "sqrt": math.sqrt,
        "pow": pow,
        "floor": math.floor,
        "ceil": math.ceil,
        # Custom functions
        "clamp": lambda value, min_val, max_val: max(min_val, min(max_val, value)),
    }

    def parse(self, formula: str) -> ast.Expression:
        """
        Parse a formula string and validate it's safe.

        Args:
            formula: Formula string (e.g., "ram_gb * 2.5 + cpu_mark / 1000")

        Returns:
            Parsed AST expression

        Raises:
            FormulaSyntaxError: If formula has syntax errors
            FormulaValidationError: If formula contains unsafe operations
        """
        if not formula or not formula.strip():
            raise FormulaSyntaxError("Formula cannot be empty")

        try:
            tree = ast.parse(formula, mode="eval")
        except SyntaxError as e:
            # Extract position and provide helpful error message
            position = e.offset if hasattr(e, "offset") and e.offset else None

            # Try to provide helpful suggestions based on common errors
            suggestion = self._get_syntax_error_suggestion(formula, e)

            raise FormulaSyntaxError(
                f"Invalid formula syntax: {e.msg}", position=position, suggestion=suggestion
            ) from e

        # Validate the AST
        try:
            self._validate_node(tree.body, formula)
        except FormulaValidationError:
            raise
        except Exception as e:
            raise FormulaValidationError(f"Formula validation failed: {e}") from e

        return tree

    def _get_syntax_error_suggestion(self, formula: str, error: SyntaxError) -> Optional[str]:
        """
        Provide helpful suggestion based on syntax error.

        Args:
            formula: The formula string
            error: The syntax error

        Returns:
            Helpful suggestion or None
        """
        error_msg = str(error.msg).lower() if error.msg else ""

        # Common mistakes and suggestions
        if "unexpected eof" in error_msg or "invalid syntax" in error_msg:
            # Check for unmatched parentheses
            open_parens = formula.count("(")
            close_parens = formula.count(")")
            if open_parens > close_parens:
                return f"Missing {open_parens - close_parens} closing parenthesis"
            elif close_parens > open_parens:
                return f"Extra {close_parens - open_parens} closing parenthesis"

            # Check for incomplete operations
            if formula.rstrip().endswith(("*", "/", "+", "-", "%", "**")):
                return "Formula ends with an operator - add the right operand"

        if "invalid character" in error_msg:
            return "Check for special characters that are not allowed in formulas"

        return None

    def _validate_node(self, node: ast.AST, formula: str) -> None:
        """
        Recursively validate that an AST node is safe.

        Args:
            node: AST node to validate
            formula: Original formula string for error reporting

        Raises:
            FormulaValidationError: If node contains unsafe operations
        """
        if isinstance(node, ast.Constant):
            # Constants are safe
            return

        elif isinstance(node, ast.Name):
            # Variable names are safe (we'll validate against context)
            return

        elif isinstance(node, ast.Attribute):
            # Attribute access like cpu.cores is safe
            self._validate_node(node.value, formula)
            return

        elif isinstance(node, ast.BinOp):
            # Binary operations
            if type(node.op) not in self.ALLOWED_OPERATORS:
                op_name = type(node.op).__name__
                allowed_ops = ["+", "-", "*", "/", "//", "%", "**"]
                raise FormulaValidationError(
                    f"Operator '{op_name}' is not allowed",
                    position=getattr(node, "col_offset", None),
                    suggestion=f"Use one of the allowed operators: {', '.join(allowed_ops)}",
                )
            self._validate_node(node.left, formula)
            self._validate_node(node.right, formula)
            return

        elif isinstance(node, ast.UnaryOp):
            # Unary operations (negation, positive)
            if type(node.op) not in self.ALLOWED_OPERATORS:
                op_name = type(node.op).__name__
                raise FormulaValidationError(
                    f"Unary operator '{op_name}' is not allowed",
                    position=getattr(node, "col_offset", None),
                    suggestion="Use only '+' or '-' as unary operators",
                )
            self._validate_node(node.operand, formula)
            return

        elif isinstance(node, ast.Compare):
            # Comparison operations
            disallowed_ops = [op for op in node.ops if type(op) not in self.ALLOWED_COMPARISONS]
            if disallowed_ops:
                op_name = type(disallowed_ops[0]).__name__
                allowed_comps = ["==", "!=", "<", "<=", ">", ">="]
                raise FormulaValidationError(
                    f"Comparison operator '{op_name}' is not allowed",
                    position=getattr(node, "col_offset", None),
                    suggestion=f"Use one of: {', '.join(allowed_comps)}",
                )
            self._validate_node(node.left, formula)
            for comparator in node.comparators:
                self._validate_node(comparator, formula)
            return

        elif isinstance(node, ast.Call):
            # Function calls
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name not in self.ALLOWED_FUNCTIONS:
                    allowed_funcs = sorted(self.ALLOWED_FUNCTIONS.keys())
                    raise FormulaValidationError(
                        f"Function '{func_name}' is not allowed",
                        position=getattr(node, "col_offset", None),
                        suggestion=f"Use one of: {', '.join(allowed_funcs)}",
                    )
            else:
                raise FormulaValidationError(
                    "Only simple function calls are allowed",
                    position=getattr(node, "col_offset", None),
                    suggestion="Use function_name(args) format, not methods or complex calls",
                )

            # Validate arguments
            for arg in node.args:
                self._validate_node(arg, formula)
            return

        elif isinstance(node, ast.IfExp):
            # Ternary expressions (x if condition else y)
            self._validate_node(node.test, formula)
            self._validate_node(node.body, formula)
            self._validate_node(node.orelse, formula)
            return

        elif isinstance(node, ast.List):
            # List literals
            for elt in node.elts:
                self._validate_node(elt, formula)
            return

        elif isinstance(node, ast.Tuple):
            # Tuple literals
            for elt in node.elts:
                self._validate_node(elt, formula)
            return

        elif isinstance(node, ast.Subscript):
            # Array/dict subscripting
            self._validate_node(node.value, formula)
            self._validate_node(node.slice, formula)
            return

        else:
            raise FormulaValidationError(
                f"AST node type '{type(node).__name__}' is not allowed",
                position=getattr(node, "col_offset", None),
                suggestion="Formula contains unsupported constructs. Use only math operations, comparisons, and allowed functions.",
            )


class FormulaEngine:
    """Engine for evaluating safe formulas against context"""

    def __init__(self):
        self.parser = FormulaParser()

    def evaluate(self, formula: str, context: dict[str, Any]) -> float:
        """
        Evaluate a formula string against a context.

        Args:
            formula: Formula string
            context: Dictionary with variable values

        Returns:
            Calculated result as float

        Raises:
            FormulaSyntaxError: If formula has syntax errors
            FormulaValidationError: If formula is invalid
            FormulaError: If evaluation fails
        """
        if not formula:
            return 0.0

        # Parse and validate formula
        tree = self.parser.parse(formula)

        # Prepare evaluation context
        eval_context = self._build_eval_context(context)

        # Evaluate
        try:
            result = eval(compile(tree, "<formula>", "eval"), {"__builtins__": {}}, eval_context)
            result_float = float(result)
            logger.debug(
                f"Formula evaluated successfully: {formula} = {result_float}",
                extra={
                    "formula": formula,
                    "result": result_float,
                    "context_keys": list(context.keys()),
                },
            )
            return result_float
        except NameError as e:
            # Variable not found in context
            var_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
            logger.error(
                f"Formula evaluation failed - undefined variable: {formula}",
                extra={"formula": formula, "error": str(e), "context_keys": list(context.keys())},
                exc_info=True,
            )
            raise FormulaError(
                f"Variable '{var_name}' is not defined",
                suggestion=f"Available variables: {', '.join(sorted(k for k in context.keys() if not callable(context[k])))}",
            ) from e
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logger.error(
                f"Formula evaluation failed: {formula}",
                extra={"formula": formula, "error": str(e), "context_keys": list(context.keys())},
                exc_info=True,
            )
            raise FormulaError(f"Formula evaluation failed: {e}") from e
        except Exception as e:
            logger.error(
                f"Formula evaluation failed with unexpected error: {formula}",
                extra={"formula": formula, "error": str(e), "context_keys": list(context.keys())},
                exc_info=True,
            )
            raise FormulaError(f"Formula evaluation failed: {e}") from e

    def _build_eval_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Build evaluation context with allowed functions and flattened variables.

        Args:
            context: Original context dictionary

        Returns:
            Flattened context suitable for eval
        """
        eval_context = {}

        # Add allowed functions
        eval_context.update(FormulaParser.ALLOWED_FUNCTIONS)

        # Flatten nested context (e.g., cpu.cores -> cpu_cores)
        def flatten_dict(d: dict[str, Any], prefix: str = "") -> None:
            for key, value in d.items():
                full_key = f"{prefix}{key}" if prefix else key

                if isinstance(value, dict):
                    # Recursively flatten nested dicts
                    flatten_dict(value, f"{full_key}_")
                    # Also keep the dict itself for attribute access
                    eval_context[key] = value
                else:
                    eval_context[full_key] = value

        flatten_dict(context)

        return eval_context

    def test_formula(self, formula: str, test_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Test a formula against multiple test cases.

        Args:
            formula: Formula string to test
            test_cases: List of context dictionaries

        Returns:
            List of results with context and calculated value
        """
        results = []

        for test_context in test_cases:
            try:
                value = self.evaluate(formula, test_context)
                results.append({"context": test_context, "result": value, "success": True})
            except Exception as e:
                results.append(
                    {"context": test_context, "result": None, "success": False, "error": str(e)}
                )

        return results


# Example formulas:
# "ram_gb * 2.5"  # Simple per-GB pricing
# "cpu_mark_multi / 1000 * 5.0"  # Benchmark-based
# "max(ram_gb * 2.5, 50)"  # Minimum value
# "ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0"  # Conditional pricing
# "(ram_gb * 2.5 + cpu_mark_multi / 1000 * 5.0) * 0.85 if condition == 'used' else (ram_gb * 2.5 + cpu_mark_multi / 1000 * 5.0)"
