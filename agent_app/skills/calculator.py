"""
Skill 2: Calculator
Safely evaluates math expressions using Python's math library.
Avoids eval() on arbitrary strings for security.
"""

import math
import ast
import operator
from langchain_core.tools import Tool

# Safe operators allowed in expressions
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "pow": math.pow,
    "factorial": math.factorial,
    "exp": math.exp,
}


def _safe_eval(node):
    """Recursively evaluate AST nodes safely."""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        operand = _safe_eval(node.operand)
        return SAFE_OPERATORS[op_type](operand)
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls allowed")
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Unknown function: {func_name}")
        args = [_safe_eval(a) for a in node.args]
        return SAFE_FUNCTIONS[func_name](*args)
    elif isinstance(node, ast.Name):
        if node.id in SAFE_FUNCTIONS:
            val = SAFE_FUNCTIONS[node.id]
            if callable(val):
                raise ValueError(f"'{node.id}' is a function, not a value")
            return val
        raise ValueError(f"Unknown name: {node.id}")
    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        expression = expression.strip()
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)

        # Format nicely
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(round(result, 10)).rstrip("0").rstrip(".")
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Invalid expression: {str(e)}"


def get_tool() -> Tool:
    return Tool(
        name="calculator",
        description=(
            "Evaluate mathematical expressions. Supports +, -, *, /, **, %, //, "
            "and functions: sqrt, abs, round, ceil, floor, log, log10, sin, cos, tan, "
            "factorial, exp, pow. Constants: pi, e. "
            "Input must be a valid math expression string, e.g. 'sqrt(144) + 2**8'."
        ),
        func=calculate,
    )
