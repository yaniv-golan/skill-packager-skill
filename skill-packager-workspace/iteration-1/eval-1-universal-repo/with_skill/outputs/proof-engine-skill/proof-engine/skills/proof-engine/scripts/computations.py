"""
computations.py — Verified constants and common computation functions.

Enforces Rule 7: Never hand-code constants or formulas. LLMs can misremember
well-known values (typing 365.25 instead of 365.2425, or getting the leap year
rule wrong). This module provides tested, citable implementations so proof
scripts import them instead of re-deriving from memory.

Every constant includes its definition and source so the proof is auditable.

Usage as module:
    from scripts.computations import compute_age, DAYS_PER_GREGORIAN_YEAR
    from scripts.computations import compare, safe_divide

Usage as CLI:
    python scripts/computations.py age 1948-05-14
    python scripts/computations.py age 1948-05-14 2026-03-25
    python scripts/computations.py compare 77 ">" 70
"""

import ast
import sys
import datetime
import operator


# ---------------------------------------------------------------------------
# Verified constants
# ---------------------------------------------------------------------------

DAYS_PER_GREGORIAN_YEAR = 365.2425
"""Mean length of a Gregorian calendar year in days.
Source: the Gregorian calendar's leap year rule (every 4 years, except every
100, except every 400) yields exactly 97 leap years per 400-year cycle:
  (400 * 365 + 97) / 400 = 146097 / 400 = 365.2425
"""

DAYS_PER_JULIAN_YEAR = 365.25
"""Mean length of a Julian calendar year (used in astronomy).
  (4 * 365 + 1) / 4 = 365.25
"""

SECONDS_PER_DAY = 86400
"""Exactly 24 * 60 * 60 = 86,400 seconds per day (ignoring leap seconds)."""


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------

OPERATORS = {
    ">":  operator.gt,
    ">=": operator.ge,
    "<":  operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}
"""Mapping from string operator symbols to Python operator functions.
Using this avoids eval() and ensures the operator string in CLAIM_FORMAL
is executed correctly."""


def compare(value, op_str: str, threshold, label=None) -> bool:
    """Compare a value against a threshold using a string operator."""
    if op_str not in OPERATORS:
        raise ValueError(
            f"Unknown operator '{op_str}'. Must be one of: {', '.join(OPERATORS.keys())}"
        )
    result = OPERATORS[op_str](value, threshold)
    tag = label or "compare"
    print(f"  {tag}: {value} {op_str} {threshold} = {result}")
    return result


def cross_check(value_a, value_b, tolerance=0.01, mode="absolute", label=None):
    """Compare two independently sourced values with tolerance."""
    diff = abs(value_a - value_b)
    tag = label or "cross_check"
    if mode == "relative":
        denom = max(abs(value_a), abs(value_b))
        if denom == 0:
            result = diff == 0
            pct = 0.0
        else:
            pct = diff / denom
            result = pct <= tolerance
        print(f"  {tag}: {value_a} vs {value_b}, diff={diff}, "
              f"relative={pct:.6f}, tolerance={tolerance} "
              f"-> {'AGREE' if result else 'DISAGREE'}")
    elif mode == "absolute":
        result = diff <= tolerance
        print(f"  {tag}: {value_a} vs {value_b}, diff={diff}, "
              f"tolerance={tolerance} -> {'AGREE' if result else 'DISAGREE'}")
    else:
        raise ValueError(
            f"Unknown mode '{mode}'. Must be 'absolute' or 'relative'."
        )
    return result


def compute_percentage_change(old_value, new_value, label=None, mode="increase"):
    """Compute percentage change from old to new value."""
    tag = label or "pct_change"
    if mode == "decline":
        if new_value == 0:
            raise ValueError("Cannot compute decline with zero new_value")
        result = (1 - old_value / new_value) * 100
        print(f"  {tag}: (1 - {old_value} / {new_value}) * 100 = {result:.4f}%")
        return result
    else:
        if old_value == 0:
            raise ValueError("Cannot compute percentage change from zero")
        change = (new_value - old_value) / old_value * 100
        print(f"  {tag}: ({new_value} - {old_value}) / {old_value} * 100 = {change:.4f}%")
        return change


# ---------------------------------------------------------------------------
# Age / duration computations
# ---------------------------------------------------------------------------

def compute_age(birth_date: datetime.date, reference_date: datetime.date = None) -> int:
    """Compute age in completed calendar years."""
    if reference_date is None:
        reference_date = datetime.date.today()
    age = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    print(f"  compute_age: {birth_date} -> {reference_date} = {age} completed years")
    return age


def compute_elapsed_days(start_date: datetime.date, end_date: datetime.date = None) -> int:
    """Compute exact number of days between two dates."""
    if end_date is None:
        end_date = datetime.date.today()
    days = (end_date - start_date).days
    print(f"  elapsed_days: {start_date} -> {end_date} = {days} days")
    return days


def days_to_years(days: int, calendar: str = "gregorian") -> float:
    """Convert a day count to approximate years."""
    if calendar == "gregorian":
        divisor = DAYS_PER_GREGORIAN_YEAR
    elif calendar == "julian":
        divisor = DAYS_PER_JULIAN_YEAR
    else:
        raise ValueError(f"Unknown calendar '{calendar}'. Use 'gregorian' or 'julian'.")
    result = days / divisor
    print(f"  days_to_years: {days} days / {divisor} = {result:.4f} years ({calendar})")
    return result


# ---------------------------------------------------------------------------
# AST-based expression explainer
# ---------------------------------------------------------------------------

_OP_PRECEDENCE = {
    ast.Add: 2, ast.Sub: 2,
    ast.Mult: 3, ast.Div: 3, ast.FloorDiv: 3, ast.Mod: 3,
    ast.Pow: 4,
}

_NON_COMMUTATIVE_OPS = {ast.Sub, ast.Div, ast.FloorDiv, ast.Mod}


def _resolve_node(node, scope: dict):
    """Resolve an AST node to its runtime value using the provided scope."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in scope:
            return scope[node.id]
        import builtins
        if hasattr(builtins, node.id):
            return getattr(builtins, node.id)
        raise NameError(f"'{node.id}' not found in scope")
    if isinstance(node, ast.Attribute):
        obj = _resolve_node(node.value, scope)
        return getattr(obj, node.attr)
    if isinstance(node, ast.BinOp):
        left = _resolve_node(node.left, scope)
        right = _resolve_node(node.right, scope)
        ops = {
            ast.Add: operator.add, ast.Sub: operator.sub,
            ast.Mult: operator.mul, ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
            ast.Pow: operator.pow,
        }
        op_func = ops.get(type(node.op))
        if op_func is None:
            raise TypeError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _resolve_node(node.operand, scope)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise TypeError(f"Unsupported unary op: {type(node.op).__name__}")
    if isinstance(node, ast.Call):
        func = _resolve_node(node.func, scope)
        args = [_resolve_node(a, scope) for a in node.args]
        kwargs = {kw.arg: _resolve_node(kw.value, scope) for kw in node.keywords}
        return func(*args, **kwargs)
    if isinstance(node, ast.Subscript):
        obj = _resolve_node(node.value, scope)
        key = _resolve_node(node.slice, scope)
        return obj[key]
    if isinstance(node, ast.Compare):
        left = _resolve_node(node.left, scope)
        cmp_ops = {
            ast.Gt: operator.gt, ast.GtE: operator.ge,
            ast.Lt: operator.lt, ast.LtE: operator.le,
            ast.Eq: operator.eq, ast.NotEq: operator.ne,
        }
        results = []
        current = left
        for op_node, comparator_node in zip(node.ops, node.comparators):
            right = _resolve_node(comparator_node, scope)
            op_func = cmp_ops.get(type(op_node))
            if op_func is None:
                raise TypeError(f"Unsupported comparison: {type(op_node).__name__}")
            results.append(op_func(current, right))
            current = right
        return all(results)
    raise TypeError(f"Unsupported AST node type: {type(node).__name__}")


def _format_node(node, scope: dict) -> str:
    """Format an AST node as a string showing resolved values."""
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        val = scope.get(node.id, "?")
        return str(val)
    if isinstance(node, ast.Attribute):
        val = _resolve_node(node, scope)
        return str(val)
    if isinstance(node, ast.BinOp):
        op_symbols = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*",
            ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**",
        }
        parent_prec = _OP_PRECEDENCE.get(type(node.op), 0)
        sym = op_symbols.get(type(node.op), "?")
        left = _format_node(node.left, scope)
        if isinstance(node.left, ast.BinOp):
            child_prec = _OP_PRECEDENCE.get(type(node.left.op), 0)
            if child_prec < parent_prec:
                left = f"({left})"
        right = _format_node(node.right, scope)
        if isinstance(node.right, ast.BinOp):
            child_prec = _OP_PRECEDENCE.get(type(node.right.op), 0)
            if child_prec < parent_prec:
                right = f"({right})"
            elif child_prec == parent_prec and type(node.op) in _NON_COMMUTATIVE_OPS:
                right = f"({right})"
        return f"{left} {sym} {right}"
    if isinstance(node, ast.UnaryOp):
        operand = _format_node(node.operand, scope)
        if isinstance(node.op, ast.USub):
            return f"-{operand}"
        return operand
    if isinstance(node, ast.Compare):
        cmp_symbols = {
            ast.Gt: ">", ast.GtE: ">=", ast.Lt: "<",
            ast.LtE: "<=", ast.Eq: "==", ast.NotEq: "!=",
        }
        left = _format_node(node.left, scope)
        parts = [left]
        for op_node, comp in zip(node.ops, node.comparators):
            sym = cmp_symbols.get(type(op_node), "?")
            parts.append(sym)
            parts.append(_format_node(comp, scope))
        return " ".join(parts)
    if isinstance(node, ast.Call):
        func_name = ast.unparse(node.func) if hasattr(ast, 'unparse') else "func"
        args = [_format_node(a, scope) for a in node.args]
        return f"{func_name}({', '.join(args)})"
    try:
        return str(_resolve_node(node, scope))
    except Exception:
        return ast.unparse(node) if hasattr(ast, 'unparse') else "<?>"


def explain_calc(expr_str: str, scope: dict, label: str = None) -> object:
    """Evaluate a Python expression and print a self-documenting explanation."""
    tree = ast.parse(expr_str, mode='eval')
    expr_node = tree.body
    result = _resolve_node(expr_node, scope)
    substituted = _format_node(expr_node, scope)
    if isinstance(result, float):
        result_str = f"{result:.4f}" if abs(result) < 1e6 else f"{result:.2e}"
    else:
        result_str = str(result)
    tag = label or expr_str
    if substituted != expr_str and substituted != result_str:
        print(f"  {tag}: {expr_str} = {substituted} = {result_str}")
    elif substituted != result_str:
        print(f"  {tag}: {substituted} = {result_str}")
    else:
        print(f"  {tag}: {expr_str} = {result_str}")
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python computations.py age 1948-05-14 [2026-03-25]")
        print("  python computations.py compare 77 '>' 70")
        print("  python computations.py constants")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "age":
        birth = datetime.date.fromisoformat(sys.argv[2])
        ref = datetime.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else datetime.date.today()
        age = compute_age(birth, ref)
        print(f"Result: {age} completed years")

    elif mode == "compare":
        if len(sys.argv) != 5:
            print("Usage: python computations.py compare <value> <op> <threshold>")
            sys.exit(1)
        value = float(sys.argv[2])
        op_str = sys.argv[3]
        threshold = float(sys.argv[4])
        result = compare(value, op_str, threshold)
        print(f"Result: {result}")

    elif mode == "constants":
        print(f"DAYS_PER_GREGORIAN_YEAR = {DAYS_PER_GREGORIAN_YEAR}")
        print(f"DAYS_PER_JULIAN_YEAR    = {DAYS_PER_JULIAN_YEAR}")
        print(f"SECONDS_PER_DAY         = {SECONDS_PER_DAY}")

    else:
        print(f"Unknown mode '{mode}'. Use: age, compare, constants")
        sys.exit(1)
