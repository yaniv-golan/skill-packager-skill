"""
latex_text.py — Convert LaTeX math strings to readable plain text.

Used by verify_citations.py to extract human-readable text from MathML
alttext attributes. Handles the most common symbols found in scientific
papers (Greek letters, operators, relations). Not a full LaTeX parser —
just the subset needed for citation matching.
"""

import re

_LATEX_SYMBOLS = [
    # Greek letters (uppercase)
    (r"\Omega", "\u03A9"),
    (r"\Delta", "\u0394"),
    (r"\Lambda", "\u039B"),
    (r"\Sigma", "\u03A3"),
    (r"\Gamma", "\u0393"),
    (r"\Theta", "\u0398"),
    (r"\Phi", "\u03A6"),
    (r"\Psi", "\u03A8"),
    (r"\Pi", "\u03A0"),
    # Greek letters (lowercase)
    (r"\omega", "\u03C9"),
    (r"\alpha", "\u03B1"),
    (r"\beta", "\u03B2"),
    (r"\gamma", "\u03B3"),
    (r"\delta", "\u03B4"),
    (r"\epsilon", "\u03B5"),
    (r"\lambda", "\u03BB"),
    (r"\sigma", "\u03C3"),
    (r"\mu", "\u03BC"),
    (r"\pi", "\u03C0"),
    (r"\rho", "\u03C1"),
    (r"\tau", "\u03C4"),
    (r"\phi", "\u03C6"),
    (r"\chi", "\u03C7"),
    (r"\psi", "\u03C8"),
    (r"\eta", "\u03B7"),
    (r"\theta", "\u03B8"),
    (r"\kappa", "\u03BA"),
    (r"\nu", "\u03BD"),
    (r"\xi", "\u03BE"),
    # Operators and relations
    (r"\pm", "\u00B1"),
    (r"\mp", "\u2213"),
    (r"\times", "\u00D7"),
    (r"\cdot", "\u00B7"),
    (r"\infty", "\u221E"),
    (r"\approx", "\u2248"),
    (r"\leq", "\u2264"),
    (r"\geq", "\u2265"),
    (r"\neq", "\u2260"),
    (r"\sim", "~"),
    (r"\propto", "\u221D"),
    (r"\ll", "\u226A"),
    (r"\gg", "\u226B"),
    (r"\rightarrow", "\u2192"),
    (r"\leftarrow", "\u2190"),
    (r"\equiv", "\u2261"),
]


def latex_to_text(latex: str) -> str:
    """Convert a LaTeX math string to readable plain text."""
    text = latex
    for cmd, replacement in _LATEX_SYMBOLS:
        text = text.replace(cmd, replacement)
    text = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\text\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\mathit\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\mathbf\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\textrm\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\operatorname\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"\1/\2", text)
    text = re.sub(r"\\sqrt\{([^}]*)\}", r"sqrt(\1)", text)
    text = re.sub(r"_\{([^}]*)\}", r"\1", text)
    text = re.sub(r"_([a-zA-Z0-9])", r"\1", text)
    text = re.sub(r"\^\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\^([a-zA-Z0-9])", r"\1", text)
    # Strip unknown commands BEFORE braces (so \mathcal{O} → {O} → O, not \mathcalO → "")
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = text.replace("{", "").replace("}", "")
    text = " ".join(text.split())
    return text
