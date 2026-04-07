"""
ast_helpers.py — AST-based source analysis for proof validation.

Replaces regex heuristics with reliable Python AST parsing for:
  - Extracting imports from scripts.* modules
  - Finding actual call sites (excluding comments, strings, import lines)
  - Extracting dict literal keys

Used by validate_proof.py.
"""

import ast
import re


def extract_script_imports(source: str) -> dict[str, str]:
    """Extract imported names from `from scripts.* import ...` statements.

    Returns:
        dict mapping imported name -> module path.
        e.g. {"compare": "scripts.computations"}

    Falls back to regex on SyntaxError (LLM drafts may have parse errors).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Regex fallback: still reliable for import lines
        imports = {}
        for m in re.finditer(r'from\s+(scripts\.\w+)\s+import\s+(.+)', source):
            module = m.group(1)
            for name in m.group(2).split(","):
                imports[name.strip()] = module
        return imports

    imports = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("scripts."):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports[name] = node.module
    return imports


def find_call_sites(source: str) -> dict[str, int] | None:
    """Find all function call sites in source code.

    Only counts actual calls (Name or Attribute node as Call.func in the AST).
    Handles both bare calls `func()` and qualified calls `module.func()`.
    Does NOT count: imports, comments, string literals.

    Returns:
        dict mapping function name -> number of call sites.
        Only names that are actually called appear in the result.
        Returns None on SyntaxError — callers MUST distinguish None
        (parse failed, can't verify) from {} (parsed OK, nothing called).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    calls = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Bare call: func(...)
            if isinstance(node.func, ast.Name):
                name = node.func.id
                calls[name] = calls.get(name, 0) + 1
            # Qualified call: module.func(...)
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
                calls[name] = calls.get(name, 0) + 1
    return calls


def extract_dict_keys(source: str, variable_name: str) -> list[str]:
    """Extract top-level string keys from a dict literal assigned to variable_name.

    Finds `variable_name = { "key1": ..., "key2": ... }` and returns
    the list of string keys in order. Only returns top-level keys.

    Handles both simple assignment (`x = {...}`) and AugAssign/AnnAssign.
    Returns empty list if variable not found, not a dict, or parse fails.

    Limitations vs. the brace-depth parser this replaces:
    - Only matches `ast.Assign` (simple `name = {...}`). If a proof ever
      uses `empirical_facts: dict = {...}` (annotated assignment), this
      won't match. The fallback in _extract_empirical_facts_keys catches this.
    - Dict comprehensions and dict() constructor calls return [].
    - These shapes don't occur in any of the 47 published proofs (verified).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    if isinstance(node.value, ast.Dict):
                        return [
                            k.value for k in node.value.keys
                            if isinstance(k, ast.Constant) and isinstance(k.value, str)
                        ]
        # Also handle annotated assignment: name: type = {...}
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == variable_name:
                if node.value and isinstance(node.value, ast.Dict):
                    return [
                        k.value for k in node.value.keys
                        if isinstance(k, ast.Constant) and isinstance(k.value, str)
                    ]
    return []
