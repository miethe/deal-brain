"""Safe formula parser and evaluator for custom calculations"""

import ast
import logging
import math
import operator
from typing import Any

logger = logging.getLogger(__name__)


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
            ValueError: If formula contains unsafe operations
        """
        try:
            tree = ast.parse(formula, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid formula syntax: {e}")

        # Validate the AST
        self._validate_node(tree.body)

        return tree

    def _validate_node(self, node: ast.AST) -> None:
        """
        Recursively validate that an AST node is safe.

        Raises:
            ValueError: If node contains unsafe operations
        """
        if isinstance(node, ast.Constant):
            # Constants are safe
            return

        elif isinstance(node, ast.Name):
            # Variable names are safe (we'll validate against context)
            return

        elif isinstance(node, ast.Attribute):
            # Attribute access like cpu.cores is safe
            self._validate_node(node.value)
            return

        elif isinstance(node, ast.BinOp):
            # Binary operations
            if type(node.op) not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator {type(node.op).__name__} not allowed")
            self._validate_node(node.left)
            self._validate_node(node.right)
            return

        elif isinstance(node, ast.UnaryOp):
            # Unary operations (negation, positive)
            if type(node.op) not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator {type(node.op).__name__} not allowed")
            self._validate_node(node.operand)
            return

        elif isinstance(node, ast.Compare):
            # Comparison operations
            if not all(type(op) in self.ALLOWED_COMPARISONS for op in node.ops):
                raise ValueError("Unsafe comparison operator")
            self._validate_node(node.left)
            for comparator in node.comparators:
                self._validate_node(comparator)
            return

        elif isinstance(node, ast.Call):
            # Function calls
            if isinstance(node.func, ast.Name):
                if node.func.id not in self.ALLOWED_FUNCTIONS:
                    raise ValueError(f"Function {node.func.id} not allowed")
            else:
                raise ValueError("Only simple function calls allowed")

            # Validate arguments
            for arg in node.args:
                self._validate_node(arg)
            return

        elif isinstance(node, ast.IfExp):
            # Ternary expressions (x if condition else y)
            self._validate_node(node.test)
            self._validate_node(node.body)
            self._validate_node(node.orelse)
            return

        elif isinstance(node, ast.List):
            # List literals
            for elt in node.elts:
                self._validate_node(elt)
            return

        elif isinstance(node, ast.Tuple):
            # Tuple literals
            for elt in node.elts:
                self._validate_node(elt)
            return

        elif isinstance(node, ast.Subscript):
            # Array/dict subscripting
            self._validate_node(node.value)
            self._validate_node(node.slice)
            return

        elif isinstance(node, ast.Index):
            # Index value (deprecated in Python 3.9+, but included for compatibility)
            self._validate_node(node.value)
            return

        else:
            raise ValueError(f"AST node type {type(node).__name__} not allowed")


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
            ValueError: If formula is invalid or evaluation fails
        """
        if not formula:
            return 0.0

        # Parse and validate formula
        try:
            tree = self.parser.parse(formula)
        except ValueError as e:
            raise ValueError(f"Formula validation failed: {e}")

        # Prepare evaluation context
        eval_context = self._build_eval_context(context)

        # Evaluate
        try:
            result = eval(compile(tree, '<formula>', 'eval'), {"__builtins__": {}}, eval_context)
            result_float = float(result)
            logger.debug(
                f"Formula evaluated successfully: {formula} = {result_float}",
                extra={"formula": formula, "result": result_float, "context_keys": list(context.keys())}
            )
            return result_float
        except Exception as e:
            logger.error(
                f"Formula evaluation failed: {formula}",
                extra={"formula": formula, "error": str(e), "context_keys": list(context.keys())},
                exc_info=True
            )
            raise ValueError(f"Formula evaluation failed: {e}")

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
                results.append({
                    "context": test_context,
                    "result": value,
                    "success": True
                })
            except Exception as e:
                results.append({
                    "context": test_context,
                    "result": None,
                    "success": False,
                    "error": str(e)
                })

        return results


# Example formulas:
# "ram_gb * 2.5"  # Simple per-GB pricing
# "cpu_mark_multi / 1000 * 5.0"  # Benchmark-based
# "max(ram_gb * 2.5, 50)"  # Minimum value
# "ram_gb * 2.5 if ram_gb >= 16 else ram_gb * 3.0"  # Conditional pricing
# "(ram_gb * 2.5 + cpu_mark_multi / 1000 * 5.0) * 0.85 if condition == 'used' else (ram_gb * 2.5 + cpu_mark_multi / 1000 * 5.0)"
